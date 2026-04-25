import { useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "../config";

const DOCUMENTS_URL = `${API_BASE_URL}/documents`;
const DOCUMENT_UPLOAD_URL = `${DOCUMENTS_URL}/upload`;

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

function hasSupportedExtension(file) {
  const name = file?.name?.toLowerCase() || "";
  return name.endsWith(".txt") || name.endsWith(".md") || name.endsWith(".pdf");
}

export default function KnowledgePage() {
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");

  async function fetchDocuments() {
    setLoading(true);

    try {
      const response = await fetch(DOCUMENTS_URL);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setDocuments(Array.isArray(data) ? data : []);
      setError("");
    } catch (err) {
      setDocuments([]);
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let isCancelled = false;

    async function loadDocuments() {
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

    loadDocuments();
    return () => {
      isCancelled = true;
    };
  }, []);

  async function handleUpload(event) {
    event.preventDefault();
    setUploadError("");
    setUploadMessage("");

    if (!selectedFile) {
      setUploadError("请选择一个 .txt、.md 或 .pdf 文件。");
      return;
    }

    if (!hasSupportedExtension(selectedFile)) {
      setUploadError("仅支持上传 .txt、.md 或 .pdf 文件。");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    setUploading(true);

    try {
      const response = await fetch(DOCUMENT_UPLOAD_URL, {
        method: "POST",
        body: formData,
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setUploadMessage(`已上传：${data.filename || selectedFile.name}`);
      await fetchDocuments();
    } catch (err) {
      setUploadError(formatError(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <section>
      <h2>Knowledge Base</h2>
      <p>
        这里用于展示浮空器知识库中的文档元数据。当前页面已接入后端
        /documents 接口，并从 SQLite 读取文档列表。
      </p>

      <section className="card">
        <div className="section-heading">
          <h3>Upload</h3>
          <span className="badge">.txt / .md / .pdf</span>
        </div>

        <form className="upload-form" onSubmit={handleUpload}>
          <label htmlFor="document-upload">原始文档</label>
          <input
            ref={fileInputRef}
            id="document-upload"
            type="file"
            accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf"
            onChange={(event) => {
              setSelectedFile(event.target.files?.[0] || null);
              setUploadError("");
              setUploadMessage("");
            }}
            disabled={uploading}
          />
          <button type="submit" disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>

        {uploadError ? <p className="error">上传失败：{uploadError}</p> : null}
        {uploadMessage ? <p className="success">{uploadMessage}</p> : null}
      </section>

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
                {document.parse_status ? (
                  <span>解析状态：{document.parse_status}</span>
                ) : null}
                {document.filename ? <span>文件名：{document.filename}</span> : null}
                {document.source_type ? <span>来源：{document.source_type}</span> : null}
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

      <p className="muted">当前阶段仅注册原始文件并持久化元数据，暂未接入解析或切分。</p>
    </section>
  );
}
