import { zodResolver } from "@hookform/resolvers/zod";
import { Calendar, Clipboard, Download, FileAudio, FileVideo, Globe, HelpCircle, Link, List, MoreVertical, PlaySquare, RefreshCw, ShieldCheck, Zap } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Badge } from "../../components/ui/Badge.jsx";
import { Button } from "../../components/ui/Button.jsx";
import { Card } from "../../components/ui/Card.jsx";
import { ProgressBar } from "../../components/ui/ProgressBar.jsx";
import { getApiErrorMessage } from "../../services/api.js";
import { formatBytes, formatDateTime, formatEta, formatSpeed } from "../../utils/formatters.js";
import { flattenJobItems, splitUrls } from "../../utils/jobs.js";
import { getStatusKind, getStatusLabel } from "../../utils/status.js";
import { getDownloadUrl } from "./jobs.api.js";
import { useCancelJobMutation, useCreateJobMutation, useJobsQuery, useRetryItemMutation } from "./jobs.queries.js";
import { downloadSchema } from "./jobs.schemas.js";
import { useJobsEvents } from "./useJobsEvents.js";

const SAMPLE_URLS = "https://www.youtube.com/watch?v=abc123\nhttps://www.youtube.com/watch?v=def456\nhttps://www.youtube.com/watch?v=ghi789";

export function HomePage({ view }) {
  useJobsEvents(true);
  const jobsQuery = useJobsQuery();
  const items = useMemo(() => flattenJobItems(jobsQuery.data?.jobs || []), [jobsQuery.data]);
  const activeItems = items.filter((item) => !["completed", "failed", "canceled"].includes(item.status));
  const recentItems = items.filter((item) => ["completed", "failed", "canceled"].includes(item.status)).slice(0, 8);

  if (view === "settings") {
    return (
      <Card className="placeholder-card">
        <h2>Ajustes</h2>
        <p>La gestion de preferencias por usuario queda preparada para `GET/PUT /api/settings/me`.</p>
      </Card>
    );
  }

  return (
    <div className="home-grid">
      <div className="home-main">
        {view !== "recent" && <ReconnectNotice />}
        {view === "home" && <DownloadForm />}
        {view !== "recent" && <MultiUrlPreview />}
        {view !== "recent" && <DownloadsCard title="Descargas activas" items={activeItems} loading={jobsQuery.isLoading} emptyText="No hay descargas activas." />}
        {view !== "downloads" && <DownloadsCard title="Recientes" items={recentItems} loading={jobsQuery.isLoading} recent emptyText="Aun no hay descargas recientes." />}
      </div>
      {view === "home" && <QuickSummary activeCount={activeItems.length} completedCount={recentItems.filter((item) => item.status === "completed").length} />}
    </div>
  );
}

function ReconnectNotice() {
  return (
    <div className="notice">
      <RefreshCw size={22} aria-hidden="true" />
      <div><strong>La conexion se esta reconectando...</strong> Algunas descargas pueden tardar mas de lo habitual.</div>
      <span aria-hidden="true">×</span>
    </div>
  );
}

function DownloadForm() {
  const [serverError, setServerError] = useState("");
  const createMutation = useCreateJobMutation();
  const form = useForm({
    resolver: zodResolver(downloadSchema),
    defaultValues: {
      mode: "single",
      url: "",
      urlsText: SAMPLE_URLS,
      outputProfile: "video_mp4",
      quality: "best",
      cookiesPath: "",
      extraOptions: "",
    },
  });
  const mode = form.watch("mode");
  const outputProfile = form.watch("outputProfile");

  const submit = async (values) => {
    setServerError("");
    const sources = values.mode === "single" ? [values.url.trim()] : splitUrls(values.urlsText);
    const payload = {
      sources,
      config: {
        output_profile: values.outputProfile,
        cookies_path: values.cookiesPath || undefined,
        quality: values.quality,
        ytdlp_options: {},
        notes: values.extraOptions || undefined,
      },
    };
    try {
      await createMutation.mutateAsync(payload);
      form.reset({ ...values, url: "" });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "No se pudo crear la descarga"));
    }
  };

  return (
    <Card className="download-card">
      <div className="card-heading split">
        <div>
          <h2><Zap size={25} aria-hidden="true" /> Descarga rapida</h2>
          <p>Pega un enlace y descarga tu video o audio en segundos.</p>
        </div>
        <div className="segmented">
          <button type="button" className={mode === "single" ? "active" : ""} onClick={() => form.setValue("mode", "single")}><Link size={18} /> Una URL</button>
          <button type="button" className={mode === "multi" ? "active" : ""} onClick={() => form.setValue("mode", "multi")}><List size={18} /> Varias URLs</button>
        </div>
      </div>
      <form className="download-form" onSubmit={form.handleSubmit(submit)}>
        {mode === "single" ? (
          <label className="youtube-input">
            <PlaySquare size={30} aria-hidden="true" />
            <input placeholder="Pega aqui un enlace de YouTube o playlist" {...form.register("url")} />
            <Clipboard size={23} aria-hidden="true" />
          </label>
        ) : (
          <textarea className="multi-textarea" rows="4" {...form.register("urlsText")} />
        )}
        {form.formState.errors.url && <small className="field-error">{form.formState.errors.url.message}</small>}
        {form.formState.errors.urlsText && <small className="field-error">{form.formState.errors.urlsText.message}</small>}
        <div className="form-row">
          <div>
            <span className="field-label">Formato</span>
            <div className="format-grid">
              <button type="button" className={outputProfile === "video_mp4" ? "format-option active" : "format-option"} onClick={() => form.setValue("outputProfile", "video_mp4")}><FileVideo size={20} /> MP4 Video</button>
              <button type="button" className={outputProfile === "audio_mp3" ? "format-option active" : "format-option"} onClick={() => form.setValue("outputProfile", "audio_mp3")}><FileAudio size={20} /> MP3 Audio</button>
            </div>
          </div>
          <label>
            <span className="field-label">Calidad</span>
            <select {...form.register("quality")}>
              <option value="best">HD Mejor calidad</option>
              <option value="balanced">Balanceado</option>
              <option value="small">Archivo pequeno</option>
            </select>
          </label>
          <Button type="submit" disabled={createMutation.isPending} className="download-submit"><Download size={24} /> {createMutation.isPending ? "Creando..." : "Descargar"}</Button>
        </div>
        <details className="advanced" open>
          <summary>Opciones avanzadas</summary>
          <div className="advanced-grid">
            <label>Usar mis cookies <input placeholder="Ruta en servidor, ej. D:/cookies/youtube.txt" {...form.register("cookiesPath")} /></label>
            <label>Otras opciones <input placeholder="Ej.: nombre personalizado, inicio: 00:30, fin: 05:20" {...form.register("extraOptions")} /></label>
          </div>
        </details>
        {serverError && <div className="form-error">{serverError}</div>}
      </form>
    </Card>
  );
}

function MultiUrlPreview() {
  return (
    <Card className="multi-preview">
      <List size={31} aria-hidden="true" />
      <div><strong>Varias URLs</strong><p>Pega varias URLs una por linea. Ideal para listas de reproduccion.</p></div>
      <pre>{SAMPLE_URLS}</pre>
    </Card>
  );
}

function DownloadsCard({ title, items, loading, recent = false, emptyText }) {
  return (
    <Card className="downloads-card">
      <div className="section-title"><h2>{recent ? <><RefreshCw size={22} /> {title}</> : title}</h2><a href={recent ? "/app/recientes" : "/app/descargas"}>Ver todas</a></div>
      {loading && <p className="muted">Cargando descargas...</p>}
      {!loading && !items.length && <p className="muted">{emptyText}</p>}
      <div className="download-list">
        {items.map((item) => <DownloadRow key={item.id} item={item} recent={recent} />)}
      </div>
    </Card>
  );
}

function DownloadRow({ item, recent }) {
  const cancelMutation = useCancelJobMutation();
  const retryMutation = useRetryItemMutation();
  const statusKind = getStatusKind(item.status);
  const progress = Math.round(item.progress_pct || 0);
  const isRetryable = ["failed", "canceled", "pending_device_online"].includes(item.status);
  const isCancelable = ["queued", "downloading", "processing", "transferring"].includes(item.status);
  const isCompleted = item.status === "completed";

  return (
    <article className="download-row">
      <div className="thumb" />
      <div className="download-title"><strong>{item.displayTitle}</strong><span>YouTube · {item.job?.config?.output_profile === "audio_mp3" ? "MP3" : "1080p"}</span></div>
      {!recent && <Badge kind={statusKind}>{getStatusLabel(item.status)}</Badge>}
      {!recent && <div className="progress-cell"><ProgressBar value={progress} kind={statusKind} /><span>{progress}%</span></div>}
      <span className="desktop-only">{formatSpeed(item.speed)}</span>
      <span className="desktop-only">{recent ? formatBytes(item.total_bytes) : formatEta(item.eta)}</span>
      {recent && <span className="desktop-only">{formatDateTime(item.updated_at)}</span>}
      <div className="row-actions">
        {isCancelable && <Button variant="outline" size="sm" onClick={() => cancelMutation.mutate(item.job_id)}>Cancelar</Button>}
        {isRetryable && <Button variant="outline" size="sm" onClick={() => retryMutation.mutate(item.id)}>Reintentar</Button>}
        {isCompleted && <Button as="a" size="sm" onClick={() => { window.location.href = getDownloadUrl(item.id); }}>Descargar</Button>}
        <button className="icon-button" type="button" aria-label="Mas acciones"><MoreVertical size={20} /></button>
      </div>
    </article>
  );
}

function QuickSummary({ activeCount, completedCount }) {
  return (
    <aside className="quick-summary">
      <Card className="summary-card"><Calendar size={35} /><div><span>Cupo diario restante</span><strong>{Math.max(0, 10 - completedCount)} / 10</strong><p>descargas</p></div></Card>
      <Card className="summary-card"><Globe size={35} /><div><span>Idioma</span><strong>Espanol (ES)</strong></div></Card>
      <Card className="summary-card"><HelpCircle size={35} /><div><span>¿Necesitas ayuda?</span><strong>Centro de ayuda</strong></div></Card>
      <Card className="summary-card"><ShieldCheck size={35} /><div><span>Seguridad</span><strong>Navegacion segura</strong><p>{activeCount} activas</p></div></Card>
    </aside>
  );
}
