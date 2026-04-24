import { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";

const HEALTH_URL = `${API_BASE_URL}/health`;

function formatError(error) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
}

export default function HealthCheck() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("unknown");
  const [error, setError] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function fetchHealth() {
      try {
        const response = await fetch(HEALTH_URL);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (!isCancelled) {
          setStatus(data?.status || "unknown");
          setError("");
        }
      } catch (err) {
        if (!isCancelled) {
          setStatus("down");
          setError(formatError(err));
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    fetchHealth();
    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <section className="card">
      <h2>Backend Health</h2>
      {loading ? <p>Checking...</p> : <p>Status: {status}</p>}
      {error ? <p className="error">Error: {error}</p> : null}
    </section>
  );
}
