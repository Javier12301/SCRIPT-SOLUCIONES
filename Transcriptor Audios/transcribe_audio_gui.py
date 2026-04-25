from __future__ import annotations

import os
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from transcribe_audio import (
    BatchMode,
    OutputConfig,
    RuntimeConfig,
    friendly_error_message,
    transcribe_audios_batch,
)


MODEL_OPTIONS = {
    "tiny - muy rapido": "tiny",
    "base - rapido": "base",
    "small - recomendado": "small",
    "medium - mejor calidad": "medium",
    "large-v3 - pesado": "large-v3",
    "turbo - rapido moderno": "turbo",
}


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tip_window: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event: tk.Event | None = None) -> None:
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + 18
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            wraplength=320,
            padx=8,
            pady=6,
        )
        label.pack()

    def hide(self, _event: tk.Event | None = None) -> None:
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class TranscriptionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Transcriptor de audios")
        self.root.geometry("980x760")
        self.root.minsize(920, 700)

        self.audio_paths: list[Path] = []
        self.output_dir = tk.StringVar(value=str(Path.cwd() / "transcripciones"))
        self.output_format = tk.StringVar(value="txt")
        self.parts_enabled = tk.BooleanVar(value=True)
        self.split_mode = tk.StringVar(value="auto")
        self.split_minutes = tk.StringVar(value="10")
        self.export_srt = tk.BooleanVar(value=False)
        self.export_vtt = tk.BooleanVar(value=False)

        self.show_advanced = tk.BooleanVar(value=False)
        self.model_name = tk.StringVar(value="small - recomendado")
        self.device_strategy = tk.StringVar(value="auto")
        self.compute_type = tk.StringVar(value="auto")
        self.inference_engine = tk.StringVar(value="auto")
        self.beam_size = tk.StringVar(value="2")
        self.batch_size = tk.StringVar(value="4")
        self.vad_enabled = tk.BooleanVar(value=True)
        self.vad_min_silence = tk.StringVar(value="500")
        self.batch_mode = tk.StringVar(value="sequential")
        self.parallel_workers = tk.StringVar(value="2")
        self.status_text = tk.StringVar(value="Elegi un audio para empezar.")

        self._build_ui()

    def add_help_label(self, parent: tk.Widget, row: int, column: int, text: str, padx: tuple[int, int] = (4, 0)) -> None:
        help_label = ttk.Label(parent, text="?", cursor="question_arrow")
        help_label.grid(row=row, column=column, sticky="w", padx=padx)
        Tooltip(help_label, text)

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(shell, highlightthickness=0)
        page_scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self.canvas.yview)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        page_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=page_scrollbar.set)

        main = ttk.Frame(self.canvas, padding=14)
        self.canvas_window = self.canvas.create_window((0, 0), window=main, anchor="nw")
        main.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.resize_canvas_window)
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(6, weight=1)

        ttk.Label(
            main,
            text="Transcriptor de audios para estudio",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            main,
            text="Agrega multiples audios, define formato y guarda todo en una carpeta destino.",
            wraplength=920,
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        top = ttk.Frame(main)
        top.grid(row=2, column=0, sticky="nsew")
        top.columnconfigure(0, weight=1)

        file_frame = ttk.LabelFrame(top, text="1. Audios", padding=10)
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

        button_row = ttk.Frame(file_frame)
        button_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        button_row.columnconfigure(3, weight=1)
        ttk.Button(button_row, text="Agregar audios", command=self.add_audio_files).grid(row=0, column=0, sticky="w")
        ttk.Button(button_row, text="Quitar seleccionado", command=self.remove_selected_audio).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        ttk.Button(button_row, text="Limpiar lista", command=self.clear_audio_files).grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.audio_count_label = ttk.Label(button_row, text="0 audios seleccionados")
        self.audio_count_label.grid(row=0, column=4, sticky="e")

        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.audio_listbox = tk.Listbox(list_frame, selectmode="extended", height=8)
        self.audio_listbox.grid(row=0, column=0, sticky="nsew")
        audio_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.audio_listbox.yview)
        audio_scrollbar.grid(row=0, column=1, sticky="ns")
        self.audio_listbox.configure(yscrollcommand=audio_scrollbar.set)

        out_frame = ttk.LabelFrame(top, text="2. Guardar en", padding=10)
        out_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        out_frame.columnconfigure(0, weight=1)
        ttk.Entry(out_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(out_frame, text="Elegir carpeta", command=self.choose_output_dir).grid(row=0, column=1)

        options_frame = ttk.LabelFrame(top, text="3. Opciones", padding=10)
        options_frame.grid(row=2, column=0, sticky="ew")
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Guardar como").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            options_frame,
            textvariable=self.output_format,
            values=("txt", "md"),
            state="readonly",
            width=10,
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(options_frame, text="Salida completa").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Label(options_frame, text="Siempre activada (archivo completo por audio)").grid(
            row=1, column=1, sticky="w", pady=(12, 0)
        )

        ttk.Checkbutton(
            options_frame,
            text="Generar transcripcion por partes",
            variable=self.parts_enabled,
            command=self.toggle_split_controls,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self.split_label = ttk.Label(options_frame, text="Como dividir el texto")
        self.split_label.grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.split_box = ttk.Frame(options_frame)
        self.split_box.grid(row=3, column=1, sticky="w", pady=(12, 0))

        self.split_buttons: list[ttk.Radiobutton] = []
        self.split_buttons.append(ttk.Radiobutton(
            self.split_box,
            text="No dividir",
            value="none",
            variable=self.split_mode,
            command=self.toggle_split_controls,
        ))
        self.split_buttons[-1].grid(row=0, column=0, sticky="w")
        self.split_buttons.append(ttk.Radiobutton(
            self.split_box,
            text="Dividir automaticamente",
            value="auto",
            variable=self.split_mode,
            command=self.toggle_split_controls,
        ))
        self.split_buttons[-1].grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.split_buttons.append(ttk.Radiobutton(
            self.split_box,
            text="Dividir cada X minutos",
            value="minutes",
            variable=self.split_mode,
            command=self.toggle_split_controls,
        ))
        self.split_buttons[-1].grid(row=2, column=0, sticky="w", pady=(6, 0))

        self.minutes_row = ttk.Frame(options_frame)
        self.minutes_row.grid(row=4, column=1, sticky="w", pady=(10, 0))
        self.minutes_label = ttk.Label(self.minutes_row, text="Minutos por parte")
        self.minutes_label.grid(row=0, column=0, sticky="w")
        self.minutes_entry = ttk.Entry(self.minutes_row, textvariable=self.split_minutes, width=10)
        self.minutes_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))

        subtitle_frame = ttk.Frame(options_frame)
        subtitle_frame.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Label(subtitle_frame, text="Subtitulos opcionales:").grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(subtitle_frame, text="SRT", variable=self.export_srt).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Checkbutton(subtitle_frame, text="VTT", variable=self.export_vtt).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Checkbutton(
            options_frame,
            text="Mostrar opciones avanzadas",
            variable=self.show_advanced,
            command=self.toggle_advanced_section,
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self.advanced_frame = ttk.LabelFrame(options_frame, text="Opciones avanzadas (opcional)", padding=10)
        self.advanced_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.advanced_frame.columnconfigure(1, weight=1)

        ttk.Label(self.advanced_frame, text="Modelo").grid(row=0, column=0, sticky="w")
        self.add_help_label(
            self.advanced_frame,
            0,
            4,
            "Define el tamano del modelo de IA. Modelos grandes suelen ser mas precisos, pero tardan mas y usan mas memoria.",
        )
        ttk.Combobox(
            self.advanced_frame,
            textvariable=self.model_name,
            values=tuple(MODEL_OPTIONS.keys()),
            width=24,
            state="readonly",
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(self.advanced_frame, text="Hardware").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            1,
            4,
            "Auto intenta usar GPU CUDA si esta disponible y si falla vuelve a CPU. CPU es mas compatible; CUDA puede ser mas rapido.",
        )
        ttk.Combobox(
            self.advanced_frame,
            textvariable=self.device_strategy,
            values=("auto", "cpu", "cuda"),
            width=14,
            state="readonly",
        ).grid(row=1, column=1, sticky="w", pady=(8, 0))

        ttk.Label(self.advanced_frame, text="Compute").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            2,
            4,
            "Controla como calcula el modelo internamente. Auto elige una opcion segura: int8 en CPU y float16 en GPU.",
        )
        ttk.Combobox(
            self.advanced_frame,
            textvariable=self.compute_type,
            values=("auto", "int8", "float16", "int8_float16", "float32"),
            width=14,
            state="readonly",
        ).grid(row=2, column=1, sticky="w", pady=(8, 0))

        ttk.Label(self.advanced_frame, text="Motor").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            3,
            4,
            "Auto usa el motor batched para acelerar audios largos. Standard consume menos memoria, pero puede ser mas lento.",
        )
        ttk.Combobox(
            self.advanced_frame,
            textvariable=self.inference_engine,
            values=("auto", "standard", "batched"),
            width=14,
            state="readonly",
        ).grid(row=3, column=1, sticky="w", pady=(8, 0))

        ttk.Label(self.advanced_frame, text="Beam size").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.add_help_label(
            self.advanced_frame,
            0,
            5,
            "Valores mas altos prueban mas alternativas por frase. Puede mejorar algo la calidad, pero vuelve la transcripcion mas lenta.",
        )
        ttk.Entry(self.advanced_frame, textvariable=self.beam_size, width=8).grid(row=0, column=3, sticky="w")
        ttk.Label(self.advanced_frame, text="Batch size").grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            1,
            5,
            "Cantidad de fragmentos procesados juntos. Subirlo puede acelerar en equipos potentes, pero consume mas RAM o VRAM.",
        )
        ttk.Entry(self.advanced_frame, textvariable=self.batch_size, width=8).grid(row=1, column=3, sticky="w", pady=(8, 0))
        ttk.Checkbutton(self.advanced_frame, text="VAD activo", variable=self.vad_enabled).grid(
            row=2, column=2, sticky="w", padx=(16, 0), pady=(8, 0)
        )
        self.add_help_label(
            self.advanced_frame,
            2,
            5,
            "Detecta silencios y evita transcribir partes sin voz. En clases largas suele ahorrar tiempo.",
        )
        ttk.Label(self.advanced_frame, text="Silencio VAD (ms)").grid(row=3, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            3,
            5,
            "Milisegundos de pausa necesarios para considerar que hay silencio. 500 es un buen punto de partida.",
        )
        ttk.Entry(self.advanced_frame, textvariable=self.vad_min_silence, width=8).grid(row=3, column=3, sticky="w", pady=(8, 0))

        ttk.Label(self.advanced_frame, text="Modo de lote").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            4,
            4,
            "Secuencial procesa un audio por vez y es mas estable. Paralelo puede acelerar lotes, pero consume mas memoria.",
        )
        ttk.Combobox(
            self.advanced_frame,
            textvariable=self.batch_mode,
            values=("sequential", "parallel"),
            width=14,
            state="readonly",
        ).grid(row=4, column=1, sticky="w", pady=(8, 0))
        ttk.Label(self.advanced_frame, text="Workers paralelo").grid(row=4, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        self.add_help_label(
            self.advanced_frame,
            4,
            5,
            "Cantidad de audios al mismo tiempo en modo paralelo. Mas workers consumen mas CPU, RAM y VRAM.",
        )
        ttk.Entry(self.advanced_frame, textvariable=self.parallel_workers, width=8).grid(row=4, column=3, sticky="w", pady=(8, 0))

        ttk.Label(
            self.advanced_frame,
            text=(
                "Recomendado para no tecnicos: Hardware auto, Compute auto, Motor auto, Beam 2, Batch 4 y modo secuencial."
            ),
            wraplength=860,
            justify="left",
        ).grid(row=5, column=0, columnspan=4, sticky="w", pady=(10, 0))

        ttk.Label(
            top,
            text=(
                "Para clases largas, el modo recomendado es: partes activadas + division automatica + hardware auto."
            ),
            wraplength=920,
            justify="left",
        ).grid(row=3, column=0, sticky="w", pady=(10, 0))

        actions = ttk.Frame(main)
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 10))
        actions.columnconfigure(0, weight=1)
        self.start_button = ttk.Button(actions, text="Transcribir lote", command=self.start_transcription)
        self.start_button.grid(row=0, column=0, sticky="w")
        ttk.Button(actions, text="Abrir carpeta de salida", command=self.open_output_dir).grid(row=0, column=1, sticky="e")

        progress = ttk.LabelFrame(main, text="Progreso", padding=10)
        progress.grid(row=6, column=0, sticky="nsew")
        progress.columnconfigure(0, weight=1)
        progress.rowconfigure(2, weight=1)

        ttk.Label(progress, textvariable=self.status_text, wraplength=920).grid(row=0, column=0, sticky="w")
        ttk.Label(
            progress,
            text="Aca vas a ver el avance por audio y el resumen final del lote.",
            wraplength=920,
        ).grid(row=1, column=0, sticky="w", pady=(4, 8))

        log_frame = ttk.Frame(progress)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = tk.Text(log_frame, height=16, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scrollbar.set)

        self.toggle_split_controls()
        self.toggle_advanced_section()

    def update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def resize_canvas_window(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def on_mousewheel(self, event: tk.Event) -> None:
        if self.canvas.bbox("all") is None:
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def add_audio_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Elegir audios",
            filetypes=[
                ("Audios", "*.mp3 *.wav *.m4a *.mp4 *.aac *.ogg *.flac"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not paths:
            return

        existing = {str(path) for path in self.audio_paths}
        for item in paths:
            if item not in existing:
                self.audio_paths.append(Path(item))
                self.audio_listbox.insert("end", item)
                existing.add(item)
        self.update_audio_count()

    def remove_selected_audio(self) -> None:
        selected = list(self.audio_listbox.curselection())
        if not selected:
            return
        for index in reversed(selected):
            self.audio_listbox.delete(index)
            del self.audio_paths[index]
        self.update_audio_count()

    def clear_audio_files(self) -> None:
        self.audio_paths.clear()
        self.audio_listbox.delete(0, "end")
        self.update_audio_count()

    def update_audio_count(self) -> None:
        self.audio_count_label.configure(text=f"{len(self.audio_paths)} audios seleccionados")

    def choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Elegir carpeta de salida")
        if path:
            self.output_dir.set(path)

    def open_output_dir(self) -> None:
        output_dir = Path(self.output_dir.get().strip())
        if output_dir.exists():
            os.startfile(output_dir.resolve())
            return
        messagebox.showinfo("Carpeta no encontrada", "La carpeta todavia no existe. Se va a crear al transcribir.")

    def toggle_split_controls(self) -> None:
        split_state = "normal" if self.parts_enabled.get() else "disabled"
        minute_state = "normal" if self.parts_enabled.get() and self.split_mode.get() == "minutes" else "disabled"

        self.split_label.configure(state=split_state)
        for button in self.split_buttons:
            button.configure(state=split_state)
        self.minutes_label.configure(state=minute_state)
        self.minutes_entry.configure(state=minute_state)

    def toggle_advanced_section(self) -> None:
        if self.show_advanced.get():
            self.advanced_frame.grid()
        else:
            self.advanced_frame.grid_remove()

    def validate_inputs(self) -> tuple[list[Path], Path] | None:
        output_dir = Path(self.output_dir.get().strip())

        if not self.audio_paths:
            messagebox.showerror("Faltan audios", "Agrega al menos un archivo de audio.")
            return None

        missing = [path for path in self.audio_paths if not path.exists()]
        if missing:
            messagebox.showerror("Audio no encontrado", f"Hay archivos inexistentes en la lista.\nEjemplo: {missing[0]}")
            return None

        if not self.output_dir.get().strip():
            messagebox.showerror("Falta la carpeta", "Elegi una carpeta de salida.")
            return None

        if self.parts_enabled.get() and self.split_mode.get() == "minutes":
            try:
                split_minutes = float(self.split_minutes.get())
            except ValueError:
                messagebox.showerror("Minutos invalidos", "Ingresa un numero valido de minutos por parte.")
                return None
            if split_minutes <= 0:
                messagebox.showerror("Minutos invalidos", "Los minutos por parte deben ser mayores que cero.")
                return None

        return [path.resolve() for path in self.audio_paths], output_dir.resolve()

    def build_configs(self) -> tuple[RuntimeConfig, OutputConfig, BatchMode, int] | None:
        try:
            beam_size = int(self.beam_size.get())
            batch_size = int(self.batch_size.get())
            vad_silence = int(self.vad_min_silence.get())
            parallel_workers = int(self.parallel_workers.get())
        except ValueError:
            messagebox.showerror("Valores invalidos", "Beam, Batch, VAD silencio y workers deben ser enteros.")
            return None

        if beam_size <= 0 or batch_size <= 0:
            messagebox.showerror("Valores invalidos", "Beam size y batch size deben ser mayores que cero.")
            return None
        if vad_silence <= 0:
            messagebox.showerror("Valor invalido", "El silencio minimo de VAD debe ser mayor que cero.")
            return None
        if parallel_workers <= 0:
            messagebox.showerror("Valor invalido", "Los workers deben ser mayores que cero.")
            return None

        subtitle_formats: set[str] = set()
        if self.export_srt.get():
            subtitle_formats.add("srt")
        if self.export_vtt.get():
            subtitle_formats.add("vtt")

        model_name = MODEL_OPTIONS.get(self.model_name.get(), self.model_name.get())
        adjusted_model, adjusted_batch, adjusted_mode, adjusted_workers = self.apply_resource_guardrails(
            model_name=model_name,
            batch_size=batch_size,
            mode=self.batch_mode.get(),
            parallel_workers=parallel_workers,
            beam_size=beam_size,
            device_strategy=self.device_strategy.get(),
        )
        if adjusted_model is None:
            return None

        runtime_cfg = RuntimeConfig(
            model_name=adjusted_model,
            language="es",
            device_strategy=self.device_strategy.get(),
            compute_type=self.compute_type.get(),
            beam_size=beam_size,
            vad_filter=self.vad_enabled.get(),
            vad_parameters={"min_silence_duration_ms": vad_silence},
            inference_engine=self.inference_engine.get(),
            batch_size=adjusted_batch,
        )

        output_cfg = OutputConfig(
            output_format=self.output_format.get(),
            split_mode=self.split_mode.get(),
            max_minutes=float(self.split_minutes.get()) if self.split_mode.get() == "minutes" else 2.5,
            parts_enabled=self.parts_enabled.get(),
            subtitle_formats=subtitle_formats,
        )
        mode: BatchMode = adjusted_mode  # type: ignore[assignment]
        return runtime_cfg, output_cfg, mode, adjusted_workers

    def apply_resource_guardrails(
        self,
        model_name: str,
        batch_size: int,
        mode: str,
        parallel_workers: int,
        beam_size: int,
        device_strategy: str,
    ) -> tuple[str | None, int, str, int]:
        warnings: list[str] = []
        changes: list[str] = []
        adjusted_batch = batch_size
        adjusted_mode = mode
        adjusted_workers = parallel_workers

        if model_name == "large-v3" and adjusted_batch > 4:
            adjusted_batch = 4
            changes.append("Batch size se bajo a 4 porque large-v3 consume mucha memoria.")
        if model_name == "large-v3" and adjusted_mode == "parallel":
            adjusted_mode = "sequential"
            changes.append("Modo de lote se cambio a secuencial porque large-v3 en paralelo puede saturar memoria.")
        if adjusted_workers > 3:
            adjusted_workers = 3
            changes.append("Workers paralelo se limito a 3 para proteger la estabilidad.")

        if model_name in {"medium", "large-v3"} and device_strategy == "cpu":
            warnings.append("Modelo pesado en CPU puede tardar bastante.")
        if batch_size > 8:
            warnings.append("Batch size alto puede consumir mucha RAM o VRAM.")
        if beam_size > 5:
            warnings.append("Beam size alto puede volver la transcripcion mucho mas lenta.")
        if mode == "parallel" and parallel_workers > 2:
            warnings.append("Paralelo con mas de 2 workers puede cargar mucho el equipo.")

        if changes:
            for change in changes:
                self.append_log(f"Ajuste automatico: {change}")
            self.batch_size.set(str(adjusted_batch))
            self.batch_mode.set(adjusted_mode)
            self.parallel_workers.set(str(adjusted_workers))

        if warnings:
            message = "Configuracion exigente detectada:\n\n" + "\n".join(f"- {item}" for item in warnings)
            message += "\n\nQueres continuar igual?"
            if not messagebox.askyesno("Configuracion exigente", message):
                return None, adjusted_batch, adjusted_mode, adjusted_workers
            for warning in warnings:
                self.append_log(f"Advertencia: {warning}")

        return model_name, adjusted_batch, adjusted_mode, adjusted_workers

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.start_button.configure(state="disabled")
            self.status_text.set("Transcribiendo... esto puede tardar varios minutos.")
        else:
            self.start_button.configure(state="normal")

    def start_transcription(self) -> None:
        validated = self.validate_inputs()
        if not validated:
            return
        config_data = self.build_configs()
        if not config_data:
            return

        audio_paths, output_dir = validated
        runtime_cfg, output_cfg, mode, parallel_workers = config_data
        self.set_busy(True)
        self.append_log("Preparando lote de transcripcion...")
        self.append_log(f"Audios seleccionados: {len(audio_paths)}")
        self.append_log(f"Guardar como: {self.output_format.get()}")
        self.append_log(f"Carpeta de salida: {output_dir}")
        self.append_log(f"Modo de lote: {mode}")
        self.append_log(f"Hardware: {runtime_cfg.device_strategy} / Compute: {runtime_cfg.compute_type}")
        self.append_log(f"Motor: {runtime_cfg.inference_engine} / Batch interno: {runtime_cfg.batch_size}")
        if self.parts_enabled.get():
            if self.split_mode.get() == "none":
                self.append_log("Partes activadas, pero sin division.")
            elif self.split_mode.get() == "auto":
                self.append_log("Partes activadas con division automatica.")
            else:
                self.append_log(f"Partes activadas: dividir cada {self.split_minutes.get()} minutos.")
        else:
            self.append_log("Solo salida completa (sin partes).")

        thread = threading.Thread(
            target=self.run_transcription,
            args=(audio_paths, output_dir, runtime_cfg, output_cfg, mode, parallel_workers),
            daemon=True,
        )
        thread.start()

    def run_transcription(
        self,
        audio_paths: list[Path],
        output_dir: Path,
        runtime_cfg: RuntimeConfig,
        output_cfg: OutputConfig,
        mode: BatchMode,
        parallel_workers: int,
    ) -> None:
        try:
            self.root.after(0, lambda: self.status_text.set("Cargando modelo y preparando lote..."))
            summary = transcribe_audios_batch(
                audio_paths=audio_paths,
                destination_root=output_dir,
                runtime_config=runtime_cfg,
                output_config=output_cfg,
                mode=mode,
                max_parallel_workers=parallel_workers,
                progress_callback=lambda message: self.root.after(0, lambda: self.on_progress(message)),
            )
        except Exception as exc:  # pragma: no cover - GUI only
            details = friendly_error_message(exc)
            if not details:
                details = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self.root.after(0, lambda: self.on_error(details))
            return

        self.root.after(0, lambda: self.on_success(summary))

    def on_progress(self, message: str) -> None:
        self.status_text.set(message)
        self.append_log(message)

    def on_success(self, summary) -> None:
        self.set_busy(False)
        self.status_text.set("Lote finalizado.")
        self.append_log("Lote finalizado.")
        self.append_log(f"Total audios: {summary.total_count}")
        self.append_log(f"Exitos: {summary.success_count}")
        self.append_log(f"Fallos: {summary.failed_count}")

        for result in summary.results:
            if result.success:
                self.append_log(
                    f"OK {result.audio_path.name}: {len(result.files_written)} archivos, "
                    f"device={result.used_device}, tiempo={result.elapsed_seconds:.2f}s"
                )
            else:
                self.append_log(f"ERROR {result.audio_path.name}: {result.error_message}")

        messagebox.showinfo(
            "Listo",
            f"Proceso finalizado.\nExitos: {summary.success_count}\nFallos: {summary.failed_count}",
        )

    def on_error(self, details: str) -> None:
        self.set_busy(False)
        self.status_text.set("Ocurrio un error durante el lote.")
        self.append_log(f"Error: {details}")
        messagebox.showerror("No se pudo transcribir", details)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    TranscriptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
