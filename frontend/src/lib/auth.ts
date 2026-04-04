export function isLoggedIn(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("colorfit_token");
}

export function sanitizeReturnUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("/") && !url.startsWith("//")) return url;
  return null;
}

export function requireLogin(returnUrl?: string): boolean {
  if (isLoggedIn()) return true;

  const safe = sanitizeReturnUrl(returnUrl);
  if (safe) {
    sessionStorage.setItem("colorfit_return_url", safe);
  }
  window.location.href = `/login${safe ? `?returnUrl=${encodeURIComponent(safe)}` : ""}`;
  return false;
}
