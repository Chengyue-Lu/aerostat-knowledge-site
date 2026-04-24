import { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";

const DOCUMENTS_URL = `${API_BASE_URL}/documents`;

function formatError(error) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
}

function formatDate(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function fetchDocuments() {
      try {
        const response = await fetch(DOCUMENTS_URL);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (!isCancelled) {
          setDocuments(Array.isArray(data) ? data : []);
          setError("");
        }
      } catch (err) {
        if (!isCancelled) {
          setDocuments([]);
          setError(formatError(err));
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    fetchDocuments();
    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <section>
      <h2>Knowledge Base</h2>
      <p>
        这里用于展示浮空器知识库中的文档元数据。当前页面已接入后端
        /documents 接口，并从 SQLite 读取文档列表。
      </p>

      <section className="card">
        <div className="section-heading">
          <h3>Documents</h3>
          <span className="badge">SQLite</span>
        </div>

        {loading ? <p>Loading documents...</p> : null}
        {error ? (
          <p className="error">文档列表请求失败：{error}</p>
        ) : null}

        {!loading && !error ? (
          <ul className="document-list">
            {documents.map((document) => (
              <li key={document.id} className="document-item">
                <strong>{document.title}</strong>
                <span>分类：{document.category}</span>
                <span>状态：{document.status}</span>
                {document.filename ? <span>文件名：{document.filename}</span> : null}
                <span>分块数：{document.chunk_count ?? 0}</span>
                {document.created_at ? (
                  <span>创建时间：{formatDate(document.created_at)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}

        {!loading && !error && documents.length === 0 ? (
          <p>暂无文档元数据。</p>
        ) : null}
      </section>

      <p className="muted">当前阶段仅持久化文档元数据，暂未接入文件上传或解析。</p>
    </section>
  );
}
