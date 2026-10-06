import { NavLink } from "react-router-dom";
import { useApp } from "../context";
import { FilmIcon, GearIcon, HomeIcon, MusicIcon, PhotoIcon, TvIcon } from "../icons";

export function Sidebar() {
  const { health } = useApp();
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-badge">
          <svg viewBox="0 0 24 24">
            <path d="M8 5l11 7-11 7V5z" fill="currentColor" />
          </svg>
        </div>
        Quark
      </div>

      <div className="nav-group-label">Library</div>
      <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
        <HomeIcon /> Home
      </NavLink>
      <NavLink to="/movies" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
        <FilmIcon /> Movies
      </NavLink>
      <NavLink to="/shows" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
        <TvIcon /> TV Shows
      </NavLink>
      <NavLink to="/music" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
        <MusicIcon /> Music
      </NavLink>
      <NavLink to="/photos" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
        <PhotoIcon /> Photos
      </NavLink>

      <div className="nav-group-label">System</div>
      <NavLink to="/settings" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
        <GearIcon /> Settings
      </NavLink>

      <div className="sidebar-spacer" />
      <div className="sidebar-footer">
        <div className="row">
          <span>Status</span>
          <span>
            <span className="dot" /> {health?.status ?? "—"}
          </span>
        </div>
        <div className="row">
          <span>Version</span>
          <span>{health?.version ?? "—"}</span>
        </div>
        <div className="row">
          <span>Items</span>
          <span>{health?.items ?? 0}</span>
        </div>
      </div>
    </aside>
  );
}
