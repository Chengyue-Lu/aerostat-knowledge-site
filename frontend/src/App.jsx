import { Link, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import KnowledgePage from "./pages/KnowledgePage";
import ChatPage from "./pages/ChatPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="header">
        <h1>Aerostat Knowledge Site</h1>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/knowledge">Knowledge</Link>
          <Link to="/chat">Chat</Link>
        </nav>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}
