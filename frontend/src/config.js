const DEFAULT_API_BASE_URL = "http://localhost:8000";

const apiBaseUrlFromEnv = import.meta.env.VITE_API_BASE_URL;

export const API_BASE_URL = apiBaseUrlFromEnv?.trim() || DEFAULT_API_BASE_URL;
