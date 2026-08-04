const API_BASE = "";

export async function apiFetch(path, opts = {}) {
  const token = localStorage.getItem("adminToken");
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
    throw new Error("Erreur de connexion");
  }
  if (!res.ok) throw new Error(data.detail || "Erreur");
  return data;
}

export async function loginPin(matricule, pin) {
  const data = await apiFetch("/api/auth/pin", {
    method: "POST",
    body: JSON.stringify({ matricule, pin }),
  });
  localStorage.setItem("adminToken", data.access_token);
  return data;
}

export async function getDashboard() {
  return apiFetch("/api/admin/dashboard");
}

export async function getEmployees() {
  return apiFetch("/api/admin/employees");
}

export async function createEmployee(body) {
  return apiFetch("/api/admin/employees", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateEmployee(id, body) {
  return apiFetch(`/api/admin/employees/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function archiveEmployee(id) {
  return updateEmployee(id, { is_active: false });
}

export async function unarchiveEmployee(id) {
  return updateEmployee(id, { is_active: true });
}

export async function getPointages(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch("/api/admin/pointages" + (qs ? "?" + qs : ""));
}

export async function forceClockout(pointageId) {
  return apiFetch(`/api/admin/pointages/${pointageId}/force-clockout`, {
    method: "POST",
  });
}
