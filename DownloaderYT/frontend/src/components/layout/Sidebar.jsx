import { Clock, Download, Globe, Home, ListFilter, Settings, Shield, SlidersHorizontal, Star, Users } from "lucide-react";
import { NavLink } from "react-router-dom";
import { Brand } from "./Brand.jsx";

const userItems = [
  { to: "/app/inicio", label: "Inicio", icon: Home },
  { to: "/app/descargas", label: "Descargas", icon: Download },
  { to: "/app/recientes", label: "Recientes", icon: Clock },
  { to: "/app/descargas", label: "Listas de reproduccion", icon: ListFilter },
  { to: "/app/recientes", label: "Favoritos", icon: Star },
  { to: "/app/ajustes", label: "Ajustes", icon: Settings },
];

const adminItems = [
  { to: "/admin/resumen", label: "Resumen", icon: Home },
  { to: "/admin/usuarios", label: "Usuarios", icon: Users },
  { to: "/admin/resumen", label: "Descargas", icon: Download },
  { to: "/admin/limites", label: "Limites", icon: SlidersHorizontal },
  { to: "/admin/ajustes", label: "Idioma", icon: Globe },
  { to: "/admin/ajustes", label: "Ajustes", icon: Settings },
  { to: "/admin/ajustes", label: "Seguridad", icon: Shield },
];

export function Sidebar({ mode }) {
  const items = mode === "admin" ? adminItems : userItems;

  return (
    <aside className="sidebar">
      <Brand />
      <nav className="sidebar-nav" aria-label="Navegacion principal">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={`${item.to}-${item.label}`} to={item.to} className="sidebar-link">
              <Icon size={19} aria-hidden="true" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="quick-tip">
        <span>Consejo rapido</span>
        <p>{mode === "admin" ? "Administra usuarios, limites y politicas para mantener el servicio seguro." : "Pega el enlace de YouTube y elige formato y calidad. Tu descarga comenzara al instante."}</p>
      </div>
      <p className="sidebar-foot">© 2025 DownloaderYT<br />Hecho para tu familia</p>
    </aside>
  );
}
