const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TOKEN_KEY = "estante_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, auth = true, signal } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch {
    throw new ApiError(
      "Não foi possível conectar à API. Ela está rodando em " + API_URL + "?",
      0
    );
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    // corpo vazio ou não-JSON
  }

  if (!response.ok) {
    const detail =
      (data && (data.detail || data.message)) ||
      `Erro ${response.status} ao chamar ${path}`;
    throw new ApiError(
      typeof detail === "string" ? detail : JSON.stringify(detail),
      response.status
    );
  }

  return data;
}

export const api = {
  register: (payload) =>
    request("/api/v1/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) =>
    request("/api/v1/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => request("/api/v1/auth/me"),

  listGoals: (apenasAtivos = true) =>
    request(`/api/v1/goals/?apenas_ativos=${apenasAtivos}`),
  createGoal: (payload) => request("/api/v1/goals/", { method: "POST", body: payload }),
  updateGoal: (id, payload) =>
    request(`/api/v1/goals/${id}`, { method: "PATCH", body: payload }),
  deleteGoal: (id) => request(`/api/v1/goals/${id}`, { method: "DELETE" }),

  listPreferences: () => request("/api/v1/preferences/"),
  createPreference: (payload) =>
    request("/api/v1/preferences/", { method: "POST", body: payload }),
  updatePreference: (id, payload) =>
    request(`/api/v1/preferences/${id}`, { method: "PATCH", body: payload }),
  deletePreference: (id) =>
    request(`/api/v1/preferences/${id}`, { method: "DELETE" }),

  getRecommendations: (goalId, signal) =>
    request(`/api/v1/recommendations/${goalId ? `?goal_id=${goalId}` : ""}`, { signal }),

  listHistory: (statusFiltro) =>
    request(
      `/api/v1/reading-history/${statusFiltro ? `?status_filtro=${statusFiltro}` : ""}`
    ),
  createHistoryEntry: (payload) =>
    request("/api/v1/reading-history/", { method: "POST", body: payload }),
  updateHistoryEntry: (id, payload) =>
    request(`/api/v1/reading-history/${id}`, { method: "PATCH", body: payload }),
  deleteHistoryEntry: (id) =>
    request(`/api/v1/reading-history/${id}`, { method: "DELETE" }),
};

export { ApiError };
