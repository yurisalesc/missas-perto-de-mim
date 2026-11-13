import { escapeHtml } from "./sanitize.js";

const FALLBACK = "Não informado";

function digitsOnly(value) {
  return String(value || "").replace(/\D/g, "");
}

export function phoneTelHref(rawPhone) {
  const digits = digitsOnly(rawPhone);
  if (!digits) return null;
  if (digits.startsWith("55") && digits.length >= 12) return `tel:+${digits}`;
  if (digits.length >= 10 && digits.length <= 11) return `tel:+55${digits}`;
  return `tel:+${digits}`;
}

export function socialHref(rawSocial) {
  const value = String(rawSocial || "").trim();
  if (!value) return null;

  const withoutProtocol = value.replace(/^https?:\/\//i, "");
  const instagramMatch = withoutProtocol.match(
    /^(?:www\.)?instagram\.com\/([A-Za-z0-9._]+)\/?/i
  );
  if (instagramMatch) {
    return `https://instagram.com/${instagramMatch[1]}`;
  }

  if (value.startsWith("@")) {
    const handle = value.slice(1).replace(/[^\w.]/g, "");
    return handle ? `https://instagram.com/${handle}` : null;
  }

  if (/^[A-Za-z0-9._]+$/.test(value) && !value.includes(".")) {
    return `https://instagram.com/${value}`;
  }

  if (/^https?:\/\//i.test(value)) return value;
  if (/^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(\/.*)?$/.test(value)) {
    return `https://${value}`;
  }

  return null;
}

export function formatPhoneHtml(rawPhone) {
  const label = String(rawPhone || "").trim() || FALLBACK;
  if (label === FALLBACK) return escapeHtml(FALLBACK);
  const href = phoneTelHref(label);
  if (!href) return escapeHtml(label);
  return `<a class="contact-link" href="${escapeHtml(href)}">${escapeHtml(label)}</a>`;
}

export function formatSocialHtml(rawSocial) {
  const label = String(rawSocial || "").trim() || FALLBACK;
  if (label === FALLBACK) return escapeHtml(FALLBACK);
  const href = socialHref(label);
  if (!href) return escapeHtml(label);
  return `<a class="contact-link" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}
