import QRCode from "qrcode";

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(textarea);
  if (!ok) throw new Error("Não foi possível copiar o código Pix.");
}

export function mountDonation(container, options = {}) {
  const payload = String(options.payload ?? "").trim();

  container.innerHTML = `
    <div class="donation">
      <h2>Apoie nosso projeto</h2>
      <p>
        Sua contribuição ajuda a manter o Missas Perto de Mim no ar e acessível para mais pessoas.
        Você pode doar qualquer valor — não é necessário cadastro.
      </p>
      <p class="donation-note">
        A confirmação e a execução do Pix acontecem no aplicativo do seu banco.
        Copiar o código ou escanear o QR Code não confirma o recebimento da doação.
      </p>
      <div class="donation-body" data-donation-body></div>
      <div class="status" data-donation-status role="status" aria-live="polite"></div>
    </div>
  `;

  const body = container.querySelector("[data-donation-body]");
  const statusEl = container.querySelector("[data-donation-status]");

  if (!payload) {
    body.innerHTML = `
      <p class="donation-empty">
        O Pix ainda não está configurado. Em breve você poderá apoiar o projeto por aqui.
      </p>
    `;
    return;
  }

  body.innerHTML = `
    <div class="donation-qr-wrap">
      <p class="donation-loading">Gerando QR Code…</p>
      <img class="donation-qr hidden" alt="QR Code Pix para doação" width="220" height="220" />
    </div>
    <button type="button" class="donation-copy" data-copy-pix>Copiar código Pix</button>
  `;

  const img = body.querySelector(".donation-qr");
  const loading = body.querySelector(".donation-loading");
  const copyBtn = body.querySelector("[data-copy-pix]");
  let copyTimer = null;

  function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.style.color = isError ? "#b91c1c" : "#0b5f59";
  }

  const qrOptions = {
    errorCorrectionLevel: "M",
    margin: 2,
    width: 220,
    color: { dark: "#0f172a", light: "#ffffff" },
  };

  void (async () => {
    try {
      const dataUrl = await QRCode.toDataURL(payload, qrOptions);
      if (!img.isConnected) return;
      img.src = dataUrl;
      img.classList.remove("hidden");
      loading.classList.add("hidden");
    } catch {
      if (!loading.isConnected) return;
      loading.textContent = "Não foi possível gerar o QR Code. Use o botão abaixo para copiar o código Pix.";
      loading.classList.remove("hidden");
      setStatus("Falha ao gerar o QR Code.", true);
    }
  })();

  copyBtn.addEventListener("click", async () => {
    try {
      await copyText(payload);
      const previous = copyBtn.textContent;
      copyBtn.textContent = "Código copiado!";
      copyBtn.disabled = true;
      setStatus("Código Pix copiado. Cole no app do seu banco para concluir a doação.");
      if (copyTimer) clearTimeout(copyTimer);
      copyTimer = setTimeout(() => {
        copyBtn.textContent = previous;
        copyBtn.disabled = false;
      }, 2200);
    } catch {
      setStatus("Não foi possível copiar. Selecione e copie o código manualmente no app do banco.", true);
    }
  });
}
