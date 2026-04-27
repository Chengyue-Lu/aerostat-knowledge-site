import { useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "../config";

const DOCUMENTS_URL = `${API_BASE_URL}/documents`;
const DOCUMENT_UPLOAD_URL = `${DOCUMENTS_URL}/upload`;
const REFRESH_INTERVAL_MS = 5000;
const LARGE_DOCUMENT_PAGE_THRESHOLD = 20;
const RUNNING_PARSE_STATUSES = new Set(["QUEUED", "PARSING"]);

function formatError(error) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
}

function parseApiDate(value) {
  if (!value) {
    return null;
  }

  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(value);
  const normalizedValue = hasTimezone ? value : `${value}Z`;
  const parsedTime = new Date(normalizedValue).getTime();
  return Number.isNaN(parsedTime) ? null : parsedTime;
}

function formatDate(value) {
  const parsedTime = parseApiDate(value);
  if (parsedTime === null) {
    return "";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(parsedTime));
}

function formatFileSize(value) {
  if (value === null || value === undefined) {
    return "";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function formatElapsed(startedAt, now) {
  if (!startedAt) {
    return "";
  }

  const startTime = parseApiDate(startedAt);
  if (startTime === null) {
    return "";
  }

  const elapsedSeconds = Math.max(0, Math.floor((now - startTime) / 1000));
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
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

function canBuildChunks(document) {
  return document.parse_status === "PARSED";
}

function isRunningParse(document) {
  return RUNNING_PARSE_STATUSES.has(document.parse_status);
}

function isLargeDocument(document) {
  return document.page_count && document.page_count > LARGE_DOCUMENT_PAGE_THRESHOLD;
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
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);
  const [buildingChunksDocumentId, setBuildingChunksDocumentId] = useState(null);
  const [parseMessage, setParseMessage] = useState("");
  const [parseError, setParseError] = useState("");
  const [chunkMessage, setChunkMessage] = useState("");
  const [chunkError, setChunkError] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [tick, setTick] = useState(Date.now());

  const activeQueueDocuments = documents.filter(isRunningParse);

  async function fetchDocuments({ showLoading = true } = {}) {
    if (showLoading) {
      setLoading(true);
    }

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

  useEffect(() => {
    const refreshTimer = window.setInterval(() => {
      fetchDocuments({ showLoading: false });
    }, REFRESH_INTERVAL_MS);
    const tickTimer = window.setInterval(() => {
      setTick(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(refreshTimer);
      window.clearInterval(tickTimer);
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
      await fetchDocuments({ showLoading: false });
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
      await fetchDocuments({ showLoading: false });
    } catch (err) {
      setParseError(formatError(err));
    } finally {
      setParsingDocumentId(null);
    }
  }

  async function handleDelete(document) {
    const confirmed = window.confirm(`删除文档：${document.title}？`);
    if (!confirmed) {
      return;
    }

    setDeleteError("");
    setDeletingDocumentId(document.id);

    try {
      const response = await fetch(`${DOCUMENTS_URL}/${document.id}`, {
        method: "DELETE",
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      await fetchDocuments({ showLoading: false });
    } catch (err) {
      setDeleteError(formatError(err));
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function handleBuildChunks(documentId) {
    setChunkError("");
    setChunkMessage("");
    setBuildingChunksDocumentId(documentId);

    try {
      const response = await fetch(`${DOCUMENTS_URL}/${documentId}/chunks/build`, {
        method: "POST",
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      setChunkMessage(`已构建 chunks：${data.chunk_count ?? 0}`);
      await fetchDocuments({ showLoading: false });
    } catch (err) {
      setChunkError(formatError(err));
    } finally {
      setBuildingChunksDocumentId(null);
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
        {chunkError ? <p className="error">构建 chunks 失败：{chunkError}</p> : null}
        {chunkMessage ? <p className="success">{chunkMessage}</p> : null}
        {deleteError ? <p className="error">删除失败：{deleteError}</p> : null}
      </section>

      <section className="card">
        <div className="section-heading">
          <h3>Parse Queue</h3>
          <span className="badge">{activeQueueDocuments.length} active</span>
        </div>

        {activeQueueDocuments.length > 0 ? (
          <ul className="queue-list">
            {activeQueueDocuments.map((document) => (
              <li key={document.id} className="queue-item">
                <strong>{document.title}</strong>
                <span>{document.parse_status}</span>
                <span>耗时：{formatElapsed(document.updated_at, tick)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">当前没有排队或正在解析的文档。</p>
        )}
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
                <div className="document-main">
                  <div>
                    <strong>{document.title}</strong>
                    {document.filename ? <span>{document.filename}</span> : null}
                  </div>
                  <span className="document-id">ID {document.id}</span>
                </div>

                <div className="document-meta">
                  <span>分类：{document.category}</span>
                  <span>状态：{document.status}</span>
                  <span>解析：{document.parse_status || "UNKNOWN"}</span>
                  <span>分块：{document.chunk_count ?? 0}</span>
                  {document.file_ext ? <span>类型：{document.file_ext}</span> : null}
                  {document.file_size ? (
                    <span>大小：{formatFileSize(document.file_size)}</span>
                  ) : null}
                  {document.page_count ? <span>页数：{document.page_count}</span> : null}
                  {document.created_at ? (
                    <span>创建：{formatDate(document.created_at)}</span>
                  ) : null}
                  {isRunningParse(document) ? (
                    <span>耗时：{formatElapsed(document.updated_at, tick)}</span>
                  ) : null}
                </div>

                {isLargeDocument(document) ? (
                  <p className="document-warning">
                    页数超过 {LARGE_DOCUMENT_PAGE_THRESHOLD} 页，MinerU 解析可能需要较长时间。
                  </p>
                ) : null}

                {document.parse_error ? (
                  <p className="document-error">
                    {document.parse_error_code ? `${document.parse_error_code}: ` : null}
                    {document.parse_error}
                  </p>
                ) : null}

                <div className="document-actions">
                  {canParseDocument(document) ? (
                    <button
                      type="button"
                      onClick={() => handleParse(document.id)}
                      disabled={parsingDocumentId === document.id}
                    >
                      {parsingDocumentId === document.id ? "Starting..." : "Parse"}
                    </button>
                  ) : null}
                  {canBuildChunks(document) ? (
                    <button
                      type="button"
                      onClick={() => handleBuildChunks(document.id)}
                      disabled={buildingChunksDocumentId === document.id}
                    >
                      {buildingChunksDocumentId === document.id
                        ? "Building..."
                        : "Build Chunks"}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="danger-button"
                    onClick={() => handleDelete(document)}
                    disabled={deletingDocumentId === document.id || isRunningParse(document)}
                  >
                    {deletingDocumentId === document.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
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
