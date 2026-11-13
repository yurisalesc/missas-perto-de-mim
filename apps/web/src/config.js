export const API_BASE =
  window.__API_BASE__ || import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export const PIX_COPIA_COLA =
  import.meta.env.VITE_PIX_COPIA_COLA || window.__PIX_COPIA_COLA__ || "";
