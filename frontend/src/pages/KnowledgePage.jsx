import { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";

const DOCUMENTS_URL = `${API_BASE_URL}/documents`;

function formatError(error) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
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
        这里用于展示浮空器知识库中的文档条目。当前页面已接入后端
        /documents 占位接口，用于验证第一版原型的数据展示链路。
      </p>

      <section className="card">
        <div className="section-heading">
          <h3>Placeholder Documents</h3>
          <span className="badge">占位数据</span>
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
              </li>
            ))}
          </ul>
        ) : null}

        {!loading && !error && documents.length === 0 ? (
          <p>暂无占位文档。</p>
        ) : null}
      </section>

      <p className="muted">暂未接入真实文档数据。</p>
    </section>
  );
}
