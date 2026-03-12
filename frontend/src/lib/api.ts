import { apiBaseUrl } from "../config";
import type { ApiEnvelope } from "../types";

export class ApiError extends Error {
  status: number;
  errorCode?: string;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, errorCode?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
    this.details = details;
  }
}

function buildHeaders(token?: string, existing?: HeadersInit): Headers {
  const headers = new Headers(existing);
  headers.set("Accept", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

export async function apiRequest<T>(
  path: string,
  options: Omit<RequestInit, "body"> & { token?: string; body?: unknown } = {},
): Promise<T> {
  const { token, body, headers, ...requestInit } = options;
  const requestHeaders = buildHeaders(token, headers);

  let requestBody: BodyInit | undefined;
  if (body !== undefined) {
    if (
      typeof body === "string" ||
      body instanceof FormData ||
      body instanceof Blob ||
      body instanceof URLSearchParams
    ) {
      requestBody = body;
    } else {
      requestHeaders.set("Content-Type", "application/json");
      requestBody = JSON.stringify(body);
    }
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...requestInit,
    headers: requestHeaders,
    body: requestBody,
  });

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const payload = (await response.json()) as ApiEnvelope<T>;
    if (!response.ok || payload.success === false) {
      throw new ApiError(
        payload.message || `Request failed with status ${response.status}`,
        response.status,
        payload.error_code,
        payload.details,
      );
    }
    return payload.data;
  }

  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`, response.status);
  }

  return undefined as T;
}

export async function downloadFile(path: string, token: string, filename: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: buildHeaders(token),
  });

  if (!response.ok) {
    let errorMessage = `Download failed with status ${response.status}`;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as ApiEnvelope<unknown>;
      errorMessage = payload.message || errorMessage;
    }
    throw new ApiError(errorMessage, response.status);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 500);
}
