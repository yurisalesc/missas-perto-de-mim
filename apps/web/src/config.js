function defaultApiBase() {
  const host = window.location?.hostname;
  if (host && host !== "localhost" && host !== "127.0.0.1") {
    return "/api";
  }
  return "http://127.0.0.1:8000";
}

export const API_BASE =
  window.__API_BASE__ || import.meta.env.VITE_API_BASE || defaultApiBase();

export const PIX_COPIA_COLA =
  import.meta.env.VITE_PIX_COPIA_COLA || window.__PIX_COPIA_COLA__ || "";
