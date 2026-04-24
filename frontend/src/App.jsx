import { Link, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import KnowledgePage from "./pages/KnowledgePage";
import ChatPage from "./pages/ChatPage";

const NAV_ITEMS = [
  { to: "/", label: "Home" },
  { to: "/knowledge", label: "Knowledge" },
  { to: "/chat", label: "Chat" },
];

const ROUTES = [
  { path: "/", element: <HomePage /> },
  { path: "/knowledge", element: <KnowledgePage /> },
  { path: "/chat", element: <ChatPage /> },
];

export default function App() {
  return (
    <div className="app-shell">
      <header className="header">
        <h1>Aerostat Knowledge Site</h1>
        <nav>
          {NAV_ITEMS.map((item) => (
            <Link key={item.to} to={item.to}>
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="content">
        <Routes>
          {ROUTES.map((routeItem) => (
            <Route
              key={routeItem.path}
              path={routeItem.path}
              element={routeItem.element}
            />
          ))}
        </Routes>
      </main>
    </div>
  );
}
