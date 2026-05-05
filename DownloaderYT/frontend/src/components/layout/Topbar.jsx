import { Bell, LogOut, Menu } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Avatar } from "../ui/Avatar.jsx";
import { logout } from "../../features/auth/auth.api.js";
import { useMeQuery } from "../../features/auth/useAuth.js";
import { useUiStore } from "../../store/uiStore.js";

export function Topbar({ mode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const sseStatus = useUiStore((state) => state.sseStatus);
  const user = useMeQuery().data?.user;
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSettled: async () => {
      queryClient.clear();
      navigate("/login", { replace: true });
    },
  });

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button className="icon-button desktop-menu" type="button" onClick={toggleSidebar} aria-label="Abrir menu">
          <Menu size={22} />
        </button>
        <h1>{mode === "admin" ? "Panel de administracion" : "Inicio"}</h1>
      </div>
      <div className="topbar-right">
        <span className={`connection ${sseStatus === "reconnecting" ? "is-warning" : ""}`}>
          <i /> {sseStatus === "reconnecting" ? "Reconectando" : "Conectado"}
        </span>
        <button className="icon-button bell" type="button" aria-label="Notificaciones">
          <Bell size={21} />
          <span>2</span>
        </button>
        <Avatar name={user?.username || "Usuario"} tone="orange" />
        <span className="topbar-user">{mode === "admin" ? "Admin" : `¡Hola, ${user?.username || "Maria"}!`}</span>
        <button className="icon-button" type="button" onClick={() => logoutMutation.mutate()} aria-label="Cerrar sesion">
          <LogOut size={19} />
        </button>
      </div>
    </header>
  );
}
