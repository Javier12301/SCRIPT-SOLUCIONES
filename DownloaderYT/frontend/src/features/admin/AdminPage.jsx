import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle, CheckCircle2, Download, HardDrive, Plus, Save, Search, Shield, SlidersHorizontal, Users } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { Avatar } from "../../components/ui/Avatar.jsx";
import { Badge } from "../../components/ui/Badge.jsx";
import { Button } from "../../components/ui/Button.jsx";
import { Card } from "../../components/ui/Card.jsx";
import { ProgressBar } from "../../components/ui/ProgressBar.jsx";
import { getApiErrorMessage } from "../../services/api.js";
import { registerUser } from "../auth/auth.api.js";
import { createUserSchema } from "../auth/auth.schemas.js";
import { adminActivity, adminUsers } from "./admin.mock.js";

export function AdminPage({ section }) {
  const [showCreate, setShowCreate] = useState(false);
  return (
    <div className="admin-page">
      <MetricGrid />
      {(section === "summary" || section === "users") && <UsersPanel onCreate={() => setShowCreate(true)} />}
      {(section === "summary" || section === "limits") && <PoliciesPanel />}
      {section === "summary" && <ActivityPanel />}
      {section === "settings" && <AdminSettings />}
      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function MetricGrid() {
  const metrics = [
    { label: "Usuarios totales", value: "28", sub: "+4 este mes", icon: Users, kind: "orange" },
    { label: "Descargas hoy", value: "152", sub: "+18% vs ayer", icon: Download, kind: "orange" },
    { label: "Descargas completadas", value: "4,982", sub: "Total acumulado", icon: CheckCircle2, kind: "success" },
    { label: "Descargas fallidas", value: "37", sub: "0.74% del total", icon: AlertTriangle, kind: "danger" },
    { label: "Almacenamiento usado", value: "256.8 GB", sub: "51% de 500 GB", icon: HardDrive, kind: "purple" },
  ];
  return (
    <div className="metric-grid">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card className="metric-card" key={metric.label}>
            <span className={`metric-icon metric-${metric.kind}`}><Icon size={32} /></span>
            <div><span>{metric.label}</span><strong>{metric.value}</strong><p>{metric.sub}</p>{metric.label.includes("Almacenamiento") && <ProgressBar value={51} kind="warning" />}</div>
          </Card>
        );
      })}
    </div>
  );
}

function UsersPanel({ onCreate }) {
  return (
    <Card className="admin-panel users-panel">
      <div className="panel-heading">
        <div><h2><Users size={24} /> Usuarios</h2><p>Gestiona las cuentas de tu familia y sus permisos.</p></div>
        <div className="admin-actions"><label className="search-box"><Search size={19} /><input placeholder="Buscar usuario..." /></label><Button onClick={onCreate}><Plus size={20} /> Crear usuario</Button></div>
      </div>
      <div className="admin-user-list">
        {adminUsers.map((user) => <UserRow key={user.id} user={user} />)}
      </div>
      <div className="panel-footer">Mostrando 1 a {adminUsers.length} de 28 usuarios <span>1 2 3 4 5</span></div>
    </Card>
  );
}

function UserRow({ user }) {
  const active = user.status === "Activo";
  return (
    <article className="admin-user-row">
      <Avatar name={user.name} tone={user.tone} />
      <div><strong>{user.name}</strong><span>{user.email}</span></div>
      <Badge kind={active ? "success" : "danger"}>{user.status}</Badge>
      <span><small>Limite diario</small>{user.daily} descargas</span>
      <span><small>URLs por lote</small>{user.batch}</span>
      <span><small>Idioma</small>{user.language}</span>
      <div className="row-actions"><Button variant="outline" size="sm">Editar</Button><Button variant="outline" size="sm">{active ? "Suspender" : "Activar"}</Button></div>
    </article>
  );
}

function PoliciesPanel() {
  return (
    <Card className="admin-panel policies-panel">
      <div className="panel-heading"><div><h2><Shield size={24} /> Politicas del sistema</h2><p>Configura las politicas globales que aplican a todos los usuarios.</p></div></div>
      <div className="policy-grid">
        <label>Limite de descargas por dia<select defaultValue="20"><option>20</option><option>10</option></select></label>
        <label>Limite de URLs por lote<select defaultValue="10"><option>10</option><option>5</option></select></label>
        <label>Idioma predeterminado<select defaultValue="es"><option value="es">Espanol (ES)</option><option value="en">English (US)</option></select></label>
        <label>Formatos permitidos<input value="MP4 Video, MP3 Audio" readOnly /></label>
        <div className="toggle-line"><span>Mostrar Google Drive</span><button type="button" className="switch is-on" aria-label="Google Drive habilitado" /></div>
        <div className="toggle-line"><span>Mostrar WhatsApp</span><button type="button" className="switch is-on" aria-label="WhatsApp habilitado" /></div>
      </div>
      <div className="save-row"><Button><Save size={19} /> Guardar cambios</Button></div>
    </Card>
  );
}

function ActivityPanel() {
  return (
    <Card className="admin-panel activity-panel">
      <div className="section-title"><h2>Actividad reciente</h2><a href="/admin/resumen">Ver todas</a></div>
      {adminActivity.map((event) => (
        <article className="activity-row" key={`${event.user}-${event.action}`}>
          <Avatar name={event.user} />
          <span>{event.user}</span>
          <Badge kind={event.kind}>{event.action}</Badge>
          <span>{event.detail}</span>
          <span>{event.date}</span>
        </article>
      ))}
    </Card>
  );
}

function AdminSettings() {
  return (
    <Card className="placeholder-card">
      <h2><SlidersHorizontal size={24} /> Ajustes de administracion</h2>
      <p>La actualizacion del extractor ya tiene endpoint backend. Las demas preferencias esperan endpoints de politicas y auditoria.</p>
    </Card>
  );
}

function CreateUserModal({ onClose }) {
  const [serverMessage, setServerMessage] = useState("");
  const form = useForm({ resolver: zodResolver(createUserSchema), defaultValues: { username: "", password: "", confirmPassword: "" } });
  const mutation = useMutation({ mutationFn: ({ username, password }) => registerUser({ username, password }) });
  const submit = async (values) => {
    setServerMessage("");
    try {
      await mutation.mutateAsync(values);
      setServerMessage("Usuario creado correctamente.");
      form.reset();
    } catch (error) {
      setServerMessage(getApiErrorMessage(error, "No se pudo crear el usuario"));
    }
  };
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-card" role="dialog" aria-modal="true" aria-label="Crear usuario">
        <h2>Crear usuario</h2>
        <form onSubmit={form.handleSubmit(submit)}>
          <label>Usuario<input {...form.register("username")} /></label>
          {form.formState.errors.username && <small>{form.formState.errors.username.message}</small>}
          <label>Contrasena<input type="password" {...form.register("password")} /></label>
          {form.formState.errors.password && <small>{form.formState.errors.password.message}</small>}
          <label>Confirmar contrasena<input type="password" {...form.register("confirmPassword")} /></label>
          {form.formState.errors.confirmPassword && <small>{form.formState.errors.confirmPassword.message}</small>}
          {serverMessage && <div className="form-error">{serverMessage}</div>}
          <div className="modal-actions"><Button type="button" variant="ghost" onClick={onClose}>Cerrar</Button><Button disabled={mutation.isPending}>{mutation.isPending ? "Creando..." : "Crear"}</Button></div>
        </form>
      </section>
    </div>
  );
}
