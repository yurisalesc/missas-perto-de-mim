export function buildDirectionsUrl({ origin, destination }) {
  const params = new URLSearchParams();
  params.set("api", "1");
  params.set("destination", `${destination.lat},${destination.lon}`);
  params.set("travelmode", "driving");
  if (origin && Number.isFinite(origin.lat) && Number.isFinite(origin.lon)) {
    params.set("origin", `${origin.lat},${origin.lon}`);
  }
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

function isMobileDevice() {
  return /Android|iPhone|iPad|iPod|Mobile/i.test(window.navigator.userAgent || "");
}

export function openDirections(url) {
  if (isMobileDevice()) {
    window.location.assign(url);
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
}
