import { Outlet } from "react-router-dom";
import { Brand } from "./Brand.jsx";
import { BottomNav } from "./BottomNav.jsx";
import { Sidebar } from "./Sidebar.jsx";
import { Topbar } from "./Topbar.jsx";

export function AppShell({ mode }) {
  return (
    <div className="app-shell">
      <Sidebar mode={mode} />
      <div className="app-main">
        <div className="mobile-brandbar">
          <Brand />
        </div>
        <Topbar mode={mode} />
        <main className="content-area">
          <Outlet />
        </main>
      </div>
      <BottomNav mode={mode} />
    </div>
  );
}
