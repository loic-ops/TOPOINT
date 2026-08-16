const API_BASE = import.meta.env.VITE_API_URL || "";

export async function apiFetch(path, opts = {}) {
  const token = localStorage.getItem("authToken");
  const headers = {
    "Content-Type": "application/json",
    ...opts.headers,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(API_BASE + path, { ...opts, headers });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("Erreur de connexion au serveur");
  }
  if (!res.ok) {
    throw new Error(data.detail || "Erreur");
  }
  return data;
}

export async function loginPin(matricule, pin) {
  const data = await apiFetch("/api/auth/pin", {
    method: "POST",
    body: JSON.stringify({ matricule, pin }),
  });
  localStorage.setItem("authToken", data.access_token);
  return data;
}

export async function clockIn() {
  return apiFetch("/api/pointage/clock-in", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function clockOut() {
  return apiFetch("/api/pointage/clock-out", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function breakStart() {
  return apiFetch("/api/pointage/break/start", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function breakEnd() {
  return apiFetch("/api/pointage/break/end", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getCurrentStatus() {
  return apiFetch("/api/pointage/current");
}

export async function getTimesheet(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch("/api/pointage/timesheet" + (qs ? "?" + qs : ""));
}
