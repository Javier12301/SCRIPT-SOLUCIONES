import { Navigate, Outlet, createBrowserRouter } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell.jsx";
import { AdminPage } from "../features/admin/AdminPage.jsx";
import { LoginPage } from "../features/auth/LoginPage.jsx";
import { useMeQuery } from "../features/auth/useAuth.js";
import { HomePage } from "../features/jobs/HomePage.jsx";

function FullPageLoader() {
  return (
    <main className="route-loader">
      <div className="loader-dot" />
      <p>Cargando DownloaderYT...</p>
    </main>
  );
}

function RequireAuth({ role }) {
  const meQuery = useMeQuery();

  if (meQuery.isLoading) return <FullPageLoader />;
  if (meQuery.isError || !meQuery.data?.user) return <Navigate to="/login" replace />;
  if (role && meQuery.data.user.role !== role) return <Navigate to="/app/inicio" replace />;

  return <Outlet />;
}

function PublicOnly() {
  const meQuery = useMeQuery();
  const user = meQuery.data?.user;

  if (meQuery.isLoading) return <FullPageLoader />;
  if (user) return <Navigate to={user.role === "admin" ? "/admin/resumen" : "/app/inicio"} replace />;

  return <Outlet />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/app/inicio" replace />,
  },
  {
    element: <PublicOnly />,
    children: [{ path: "/login", element: <LoginPage /> }],
  },
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/app",
        element: <AppShell mode="user" />,
        children: [
          { index: true, element: <Navigate to="inicio" replace /> },
          { path: "inicio", element: <HomePage view="home" /> },
          { path: "descargas", element: <HomePage view="downloads" /> },
          { path: "recientes", element: <HomePage view="recent" /> },
          { path: "ajustes", element: <HomePage view="settings" /> },
        ],
      },
    ],
  },
  {
    element: <RequireAuth role="admin" />,
    children: [
      {
        path: "/admin",
        element: <AppShell mode="admin" />,
        children: [
          { index: true, element: <Navigate to="resumen" replace /> },
          { path: "resumen", element: <AdminPage section="summary" /> },
          { path: "usuarios", element: <AdminPage section="users" /> },
          { path: "limites", element: <AdminPage section="limits" /> },
          { path: "ajustes", element: <AdminPage section="settings" /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/app/inicio" replace /> },
]);
