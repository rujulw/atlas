export type HealthResponse = {
  status: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type ApiError = {
  detail?: string;
};

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorBody = (await response.json()) as ApiError;
      if (errorBody.detail) {
        message = errorBody.detail;
      }
    } catch {
      // Preserve generic message when response body is not JSON.
    }

    throw new Error(message);
  }

  return (await response.json()) as T;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health", { method: "GET" });
}

export function login(payload: { email: string; password: string }): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function register(payload: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<{ detail: string }> {
  return request<{ detail: string }>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
