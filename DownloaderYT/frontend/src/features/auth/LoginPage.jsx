import { zodResolver } from "@hookform/resolvers/zod";
import { EyeOff, Lock, ShieldCheck, User } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Brand } from "../../components/layout/Brand.jsx";
import { Button } from "../../components/ui/Button.jsx";
import { getApiErrorMessage } from "../../services/api.js";
import { login } from "./auth.api.js";
import { loginSchema } from "./auth.schemas.js";

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState("");
  const form = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });
  const mutation = useMutation({
    mutationFn: login,
    onSuccess: async (data) => {
      queryClient.setQueryData(["auth", "me"], { user: data.user });
      navigate(data.user?.role === "admin" ? "/admin/resumen" : "/app/inicio", { replace: true });
    },
    onError: (error) => setServerError(getApiErrorMessage(error, "Credenciales inválidas")),
  });

  const onSubmit = (values) => {
    setServerError("");
    mutation.mutate(values);
  };

  return (
    <main className="login-page">
      <section className="login-hero">
        <div className="login-brand-copy">
          <Brand />
          <p>Descarga tus videos y audios de YouTube de forma rapida, simple y segura.</p>
        </div>
        <div className="login-waves" aria-hidden="true" />
      </section>
      <section className="login-card" aria-label="Iniciar sesion">
        <div className="login-mobile-logo">
          <Brand />
        </div>
        <h1>Iniciar sesion</h1>
        <p>Accede a tu cuenta para continuar</p>
        <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
          <label>
            Usuario
            <span className="input-shell">
              <User size={18} aria-hidden="true" />
              <input type="text" placeholder="Ingresa tu usuario" {...form.register("username")} />
            </span>
            {form.formState.errors.username && <small>{form.formState.errors.username.message}</small>}
          </label>
          <label>
            Contrasena
            <span className="input-shell">
              <Lock size={18} aria-hidden="true" />
              <input type="password" placeholder="••••••••••••" {...form.register("password")} />
              <EyeOff size={18} aria-hidden="true" />
            </span>
            {form.formState.errors.password && <small>{form.formState.errors.password.message}</small>}
          </label>
          <div className="login-row">
            <label className="checkbox-line"><input type="checkbox" /> Recordarme</label>
            <a href="/login" onClick={(event) => event.preventDefault()}>¿Olvidaste tu contrasena?</a>
          </div>
          {serverError && <div className="form-error">{serverError}</div>}
          <Button type="submit" disabled={mutation.isPending} className="login-submit">
            {mutation.isPending ? "Iniciando..." : "Iniciar sesion"}
          </Button>
        </form>
        <p className="login-note"><ShieldCheck size={17} aria-hidden="true" /> Acceso seguro</p>
      </section>
    </main>
  );
}
