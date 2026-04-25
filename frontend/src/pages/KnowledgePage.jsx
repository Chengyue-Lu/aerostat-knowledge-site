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

function canParseDocument(document) {
  const fileExt = document.file_ext?.toLowerCase();
  const filename = document.filename?.toLowerCase() || "";
  const isPdf = fileExt === ".pdf" || filename.endsWith(".pdf");
  return (
    isPdf &&
    (document.parse_status === "NOT_PARSED" || document.parse_status === "FAILED")
  );
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
  const [parsingDocumentId, setParsingDocumentId] = useState(null);
  const [parseMessage, setParseMessage] = useState("");
  const [parseError, setParseError] = useState("");

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

  async function handleParse(documentId) {
    setParseError("");
    setParseMessage("");
    setParsingDocumentId(documentId);

    try {
      const response = await fetch(`${DOCUMENTS_URL}/${documentId}/parse`, {
        method: "POST",
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      setParseMessage(`已提交解析任务：${data.title || documentId}`);
      await fetchDocuments();
    } catch (err) {
      setParseError(formatError(err));
    } finally {
      setParsingDocumentId(null);
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
        {parseError ? <p className="error">解析启动失败：{parseError}</p> : null}
        {parseMessage ? <p className="success">{parseMessage}</p> : null}
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
                {canParseDocument(document) ? (
                  <div className="document-actions">
                    <button
                      type="button"
                      onClick={() => handleParse(document.id)}
                      disabled={parsingDocumentId === document.id}
                    >
                      {parsingDocumentId === document.id ? "Starting..." : "Parse"}
                    </button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}

        {!loading && !error && documents.length === 0 ? (
          <p>暂无文档元数据。</p>
        ) : null}
      </section>

      <p className="muted">PDF 解析会在后台运行，列表刷新后可查看解析状态。</p>
    </section>
  );
}
