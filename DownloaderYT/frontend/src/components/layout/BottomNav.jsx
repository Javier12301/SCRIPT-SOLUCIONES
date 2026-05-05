import { Clock, Download, Home, Settings, SlidersHorizontal, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

const userItems = [
  { to: "/app/inicio", label: "Inicio", icon: Home },
  { to: "/app/descargas", label: "Activas", icon: Download },
  { to: "/app/recientes", label: "Recientes", icon: Clock },
  { to: "/app/ajustes", label: "Ajustes", icon: Settings },
];

const adminItems = [
  { to: "/admin/resumen", label: "Resumen", icon: Home },
  { to: "/admin/usuarios", label: "Usuarios", icon: Users },
  { to: "/admin/limites", label: "Limites", icon: SlidersHorizontal },
  { to: "/admin/ajustes", label: "Ajustes", icon: Settings },
];

export function BottomNav({ mode }) {
  const items = mode === "admin" ? adminItems : userItems;
  return (
    <nav className="bottom-nav" aria-label="Navegacion mobile">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink key={item.to} to={item.to} className="bottom-nav-link">
            <Icon size={24} aria-hidden="true" />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
