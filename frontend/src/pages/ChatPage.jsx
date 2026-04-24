import { useState } from "react";
import { API_BASE_URL } from "../config";

const CHAT_URL = `${API_BASE_URL}/chat`;

function formatError(error) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
}

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      const response = await fetch(CHAT_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setReply(data?.reply || "后端已返回，但没有 reply 字段。");
    } catch (err) {
      setReply("");
      setError(formatError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <h2>Knowledge Q&A</h2>
      <p>
        这里用于验证浮空器知识问答的最小链路。当前会调用后端 /chat
        占位接口，并展示返回的 reply。
      </p>

      <form className="chat-form" onSubmit={handleSubmit}>
        <label htmlFor="question">Question</label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="例如：系留气球有哪些典型应用场景？"
          rows={4}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Sending..." : "Send"}
        </button>
      </form>

      <section className="card">
        <h3>Reply</h3>
        {error ? <p className="error">问答请求失败：{error}</p> : null}
        {reply ? <p>{reply}</p> : null}
        {!reply && !error ? <p className="muted">回复将在这里显示。</p> : null}
      </section>
    </section>
  );
}
