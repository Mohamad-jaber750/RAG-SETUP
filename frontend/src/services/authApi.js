import { apiFetch, apiJson } from "./httpClient";
import { logoutResponseSchema, userSchema } from "./schemas";

export function consumeAuthErrorFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("auth_error");
  if (!error) return null;

  params.delete("auth_error");
  const nextUrl = `${window.location.pathname}${params.toString() ? `?${params}` : ""}${window.location.hash}`;
  window.history.replaceState({}, document.title, nextUrl);
  return error;
}

export function startGoogleLogin() {
  const returnUrl = `${window.location.origin}${window.location.pathname}`;
  window.location.href = `/api/auth/login/google?returnUrl=${encodeURIComponent(returnUrl)}`;
}

export async function getCurrentUser() {
  const response = await apiFetch("/api/auth/me");
  if (response.status === 401) return null;
  if (!response.ok) throw new Error(`Could not load your profile (${response.status}).`);
  const data = await response.json();
  const result = userSchema.safeParse(data);
  if (!result.success) throw new Error("The profile response has an unexpected format.");
  return result.data;
}

export async function logout() {
  await apiJson("/api/auth/logout", { method: "POST" }, logoutResponseSchema);
}
