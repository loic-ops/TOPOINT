const API_BASE = import.meta.env.VITE_API_URL || "";

let onAuthError = null;

export function setAuthErrorHandler(handler) {
  onAuthError = handler;
}

function handleAuthError() {
  localStorage.removeItem("adminToken");
  localStorage.removeItem("adminEmployee");
  if (onAuthError) onAuthError();
}

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

  if (res.status === 401) {
    handleAuthError();
    throw new Error("Session expirée. Veuillez vous reconnecter.");
  }

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

export function logout() {
  localStorage.removeItem("adminToken");
  localStorage.removeItem("adminEmployee");
  if (onAuthError) onAuthError();
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

export async function exportPointagesPDF(params = {}) {
  const token = localStorage.getItem("adminToken");
  const qs = new URLSearchParams(params).toString();
  const url = API_BASE + "/api/admin/pointages/export-pdf" + (qs ? "?" + qs : "");
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Erreur lors de l'export");
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "pointages.pdf";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export async function deletePointage(pointageId) {
  return apiFetch(`/api/admin/pointages/${pointageId}`, {
    method: "DELETE",
  });
}

export async function deletePointages(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch("/api/admin/pointages" + (qs ? "?" + qs : ""), {
    method: "DELETE",
  });
}
