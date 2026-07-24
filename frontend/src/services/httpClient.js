export async function apiFetch(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: {
        ...options.headers,
      },
    });
  } catch {
    throw new Error("The application service is offline. Restart RagMiddleware and try again.");
  }

  return response;
}

export async function apiJson(path, options = {}, schema) {
  const response = await apiFetch(path, options);
  const contentType = response.headers.get("content-type") || "";

  if (!contentType.includes("application/json")) {
    throw new Error(`The API returned an unexpected response (${response.status}).`);
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.error || `Request failed (${response.status}).`);
  }

  if (!schema) return data;

  const result = schema.safeParse(data);
  if (!result.success) {
    throw new Error("The API returned data in an unexpected format.");
  }
  return result.data;
}
