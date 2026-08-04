import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useApp } from "./context";
import { PlayerProvider } from "./player";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { Toasts } from "./components/Toasts";
import HomePage from "./pages/HomePage";
import MoviesPage from "./pages/MoviesPage";
import ShowsPage from "./pages/ShowsPage";
import SearchPage from "./pages/SearchPage";
import SettingsPage from "./pages/SettingsPage";
import ItemDetailPage from "./pages/ItemDetailPage";
import ShowDetailPage from "./pages/ShowDetailPage";

export default function App() {
  const { refreshAll } = useApp();

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  // Disable native browser context menu app-wide
  useEffect(() => {
    const prevent = (e: MouseEvent) => {
      if (e.button === 2) e.preventDefault();
    };
    window.addEventListener("contextmenu", prevent);
    return () => window.removeEventListener("contextmenu", prevent);
  }, []);

  return (
    <PlayerProvider>
      <div className="app">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<><TopBar title="Home" /><div className="content"><HomePage /></div></>} />
            <Route path="/movies" element={<><TopBar title="Movies" /><div className="content"><MoviesPage /></div></>} />
            <Route path="/shows" element={<><TopBar title="TV Shows" /><div className="content"><ShowsPage /></div></>} />
            <Route path="/search" element={<><TopBar title="Search" /><div className="content"><SearchPage /></div></>} />
            <Route path="/settings" element={<><div className="content"><SettingsPage /></div></>} />
            <Route path="/item/:mediaId" element={<ItemDetailPage />} />
            <Route path="/show/:title" element={<ShowDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Toasts />
      </div>
    </PlayerProvider>
  );
}
