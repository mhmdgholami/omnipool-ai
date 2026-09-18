export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function request(
  path,
  { method = "GET", body = undefined, timeoutMs = 10000 } = {},
) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(path, {
      method,
      headers: body === undefined
        ? undefined
        : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });

    const text = await response.text();
    let payload = null;
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = text;
      }
    }

    if (!response.ok) {
      const message =
        payload && typeof payload === "object" && payload.detail
          ? payload.detail
          : String(payload || response.statusText);
      throw new ApiError(response.status, message);
    }

    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}
