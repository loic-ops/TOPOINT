import { useState, useEffect, useCallback } from "react";
import {
  loginPin,
  logout,
  setAuthErrorHandler,
  getDashboard,
  getEmployees,
  createEmployee,
  updateEmployee,
  archiveEmployee,
  unarchiveEmployee,
  getPointages,
  forceClockout,
  exportPointagesPDF,
  deletePointage,
  deletePointages,
} from "./api.js";

function formatDuration(seconds) {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h${m.toString().padStart(2, "0")}`;
}

function formatTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Badge({ type, children }) {
  return <span className={`badge badge-${type}`}>{children}</span>;
}

function LoginScreen({ onLogin }) {
  const [matricule, setMatricule] = useState("ADMIN001");
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await loginPin(matricule, pin);
      onLogin(data.employee);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg)",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "white",
          padding: "40px 32px",
          borderRadius: 16,
          width: "100%",
          maxWidth: 380,
          boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 10,
              background: "var(--navy)",
              color: "white",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 800,
              fontSize: "1.1rem",
              marginBottom: 12,
            }}
          >
            T
          </div>
          <h1
            style={{
              fontFamily: "'Sora', sans-serif",
              fontSize: "1.2rem",
              color: "var(--navy)",
            }}
          >
              Admin
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
            Connexion administration
          </p>
        </div>
        <div className="form-group">
          <label>Matricule</label>
          <input
            value={matricule}
            onChange={(e) => setMatricule(e.target.value.toUpperCase())}
            placeholder="ADMIN001"
          />
        </div>
        <div className="form-group">
          <label>Code PIN</label>
          <input
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="••••"
            maxLength={8}
          />
        </div>
        {error && (
          <p style={{ color: "var(--red)", fontSize: "0.85rem", marginBottom: 12 }}>
            {error}
          </p>
        )}
        <button
          className="btn btn-primary"
          type="submit"
          disabled={loading}
          style={{ width: "100%", justifyContent: "center" }}
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </div>
  );
}

function Sidebar({ page, onNavigate }) {
  const links = [
    { key: "dashboard", label: "Tableau de bord" },
    { key: "employees", label: "Employés" },
    { key: "presences", label: "Présences du jour" },
    { key: "pointages", label: "Historique pointages" },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">T</div>
        <span>TOPOINT</span>
      </div>
      <div className="sidebar-nav">
        <div className="nav-section">Navigation</div>
        {links.map((l) => (
          <button
            key={l.key}
            className={`nav-link ${page === l.key ? "active" : ""}`}
            onClick={() => onNavigate(l.key)}
          >
            {l.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function DashboardPage({ search }) {
  const [data, setData] = useState(null);
  const load = useCallback(async () => {
    try {
      setData(await getDashboard());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    load();
    const i = setInterval(load, 30000);
    return () => clearInterval(i);
  }, [load]);

  if (!data) return <div className="page">Chargement...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Tableau de bord</h1>
      </div>

      <div className="kpi-row">
        <div className="kpi-card">
          <div className="kpi-value">{data.total_employees}</div>
          <div className="kpi-label">Employés actifs</div>
        </div>
        <div className="kpi-card teal">
          <div className="kpi-value">{data.present_now}</div>
          <div className="kpi-label">En poste</div>
        </div>
        <div className="kpi-card amber">
          <div className="kpi-value">{data.on_break}</div>
          <div className="kpi-label">En pause</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{data.completed}</div>
          <div className="kpi-label">Terminé</div>
        </div>
        <div className="kpi-card red">
          <div className="kpi-value">{data.absent}</div>
          <div className="kpi-label">Absents</div>
        </div>
        <div className="kpi-card red">
          <div className="kpi-value">{data.flagged}</div>
          <div className="kpi-label">Anomalies</div>
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Employé</th>
              <th>Heure d'arrivée</th>
              <th>Durée</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {data.employees
              .filter((emp) => {
                if (!search) return true;
                const q = search.toLowerCase();
                return (
                  emp.matricule.toLowerCase().includes(q) ||
                  emp.first_name.toLowerCase().includes(q) ||
                  emp.last_name.toLowerCase().includes(q)
                );
              })
              .map((emp) => {
                const status = data.employee_statuses?.[emp.id] || "absent";
                const ptg = data.today_pointages.find(
                  (p) => p.employee_id === emp.id
                );
                return (
                  <tr key={emp.id}>
                    <td>
                      <strong>
                        {emp.first_name} {emp.last_name}
                      </strong>
                      <br />
                      <small style={{ color: "var(--text-muted)" }}>
                        {emp.matricule}
                      </small>
                    </td>
                    <td>{ptg ? formatTime(ptg.clock_in) : "—"}</td>
                    <td>
                      {ptg
                        ? formatDuration(
                            ptg.duration_seconds ||
                              Math.floor(
                                (Date.now() -
                                  new Date(ptg.clock_in).getTime()) /
                                  1000
                              )
                          )
                        : "—"}
                    </td>
                    <td>
                      {status === "present" && (
                        <Badge type="working">En poste</Badge>
                      )}
                      {status === "on_break" && (
                        <Badge type="break">En pause</Badge>
                      )}
                      {status === "completed" && (
                        <Badge type="offline">Terminé</Badge>
                      )}
                      {status === "absent" && (
                        <Badge type="offline">Absent</Badge>
                      )}
                      {status === "flagged" && (
                        <Badge type="flagged">Anomalie</Badge>
                      )}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EmployeesPage({ search }) {
  const [employees, setEmployees] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editEmp, setEditEmp] = useState(null);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    matricule: "",
    pin: "",
  });

  const load = useCallback(async () => {
    try {
      setEmployees(await getEmployees());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openCreate = () => {
    setEditEmp(null);
    setForm({
      first_name: "",
      last_name: "",
      matricule: "",
      pin: "",
    });
    setShowModal(true);
  };

  const openEdit = (emp) => {
    setEditEmp(emp);
    setForm({
      first_name: emp.first_name,
      last_name: emp.last_name,
      matricule: emp.matricule,
      pin: "",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const body = {
        first_name: form.first_name,
        last_name: form.last_name,
      };

      if (editEmp) {
        if (form.pin) body.pin = form.pin;
        await updateEmployee(editEmp.id, body);
      } else {
        body.pin = form.pin;
        body.matricule = form.matricule || undefined;
        await createEmployee(body);
      }
      setShowModal(false);
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleToggleActive = async (emp) => {
    try {
      if (emp.is_active) {
        await archiveEmployee(emp.id);
      } else {
        await unarchiveEmployee(emp.id);
      }
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Employés</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          + Nouvel employé
        </button>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Matricule</th>
              <th>Nom</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees
              .filter((emp) => {
                if (!search) return true;
                const q = search.toLowerCase();
                return (
                  emp.matricule.toLowerCase().includes(q) ||
                  emp.first_name.toLowerCase().includes(q) ||
                  emp.last_name.toLowerCase().includes(q)
                );
              })
              .map((emp) => (
              <tr key={emp.id}>
                <td>
                  <code>{emp.matricule}</code>
                </td>
                <td>
                  {emp.first_name} {emp.last_name}
                </td>
                <td>
                  <Badge type={emp.is_active ? "active" : "inactive"}>
                    {emp.is_active ? "Actif" : "Inactif"}
                  </Badge>
                </td>
                <td>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => openEdit(emp)}
                  >
                    Modifier
                  </button>
                  <button
                    className={`btn btn-sm ${emp.is_active ? "btn-danger" : "btn-teal"}`}
                    onClick={() => handleToggleActive(emp)}
                  >
                    {emp.is_active ? "Archiver" : "Activer"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={`modal-bg ${showModal ? "" : "hidden"}`}>
        <div className="modal-box">
          <h3>{editEmp ? "Modifier l'employé" : "Nouvel employé"}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Prénom</label>
              <input
                value={form.first_name}
                onChange={(e) =>
                  setForm({ ...form, first_name: e.target.value })
                }
                required
              />
            </div>
            <div className="form-group">
              <label>Nom</label>
              <input
                value={form.last_name}
                onChange={(e) =>
                  setForm({ ...form, last_name: e.target.value })
                }
                required
              />
            </div>
            {!editEmp && (
              <div className="form-group">
                <label>Matricule (auto si vide)</label>
                <input
                  value={form.matricule}
                  onChange={(e) =>
                    setForm({ ...form, matricule: e.target.value })
                  }
                  placeholder="EMP0006"
                />
              </div>
            )}
            <div className="form-group">
              <label>
                {editEmp
                  ? "Nouveau PIN (laisser vide pour garder)"
                  : "PIN (4+ chiffres)"}
              </label>
              <input
                type="password"
                value={form.pin}
                onChange={(e) => setForm({ ...form, pin: e.target.value })}
                required={!editEmp}
                maxLength={8}
              />
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setShowModal(false)}
              >
                Annuler
              </button>
              <button type="submit" className="btn btn-primary">
                {editEmp ? "Enregistrer" : "Créer"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function PresencesPage({ search }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setData(await getDashboard());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    load();
    const i = setInterval(load, 15000);
    return () => clearInterval(i);
  }, [load]);

  const handleForce = async (pointageId) => {
    if (!confirm("Forcer la sortie de cet employé ?")) return;
    setLoading(true);
    try {
      await forceClockout(pointageId);
      load();
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!data) return <div className="page">Chargement...</div>;

  const activeEmployees = data.employees.filter((emp) => {
    const status = data.employee_statuses?.[emp.id] || "absent";
    return status === "present" || status === "on_break";
  });

  const completedEmployees = data.employees.filter((emp) => {
    const status = data.employee_statuses?.[emp.id] || "absent";
    return status === "completed";
  });

  const absentEmployees = data.employees.filter((emp) => {
    const status = data.employee_statuses?.[emp.id] || "absent";
    return status === "absent";
  });

  const filteredActive = activeEmployees.filter((emp) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      emp.matricule.toLowerCase().includes(q) ||
      emp.first_name.toLowerCase().includes(q) ||
      emp.last_name.toLowerCase().includes(q)
    );
  });

  const filteredCompleted = completedEmployees.filter((emp) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      emp.matricule.toLowerCase().includes(q) ||
      emp.first_name.toLowerCase().includes(q) ||
      emp.last_name.toLowerCase().includes(q)
    );
  });

  const filteredAbsent = absentEmployees.filter((emp) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      emp.matricule.toLowerCase().includes(q) ||
      emp.first_name.toLowerCase().includes(q) ||
      emp.last_name.toLowerCase().includes(q)
    );
  });

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Présences du jour</h1>
      </div>

      <div className="kpi-row">
        <div className="kpi-card teal">
          <div className="kpi-value">{data.present_now}</div>
          <div className="kpi-label">En poste</div>
        </div>
        <div className="kpi-card amber">
          <div className="kpi-value">{data.on_break}</div>
          <div className="kpi-label">En pause</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{data.completed}</div>
          <div className="kpi-label">Terminé</div>
        </div>
        <div className="kpi-card red">
          <div className="kpi-value">{data.absent}</div>
          <div className="kpi-label">Absents</div>
        </div>
        <div className="kpi-card red">
          <div className="kpi-value">{data.flagged}</div>
          <div className="kpi-label">Anomalies</div>
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Employé</th>
              <th>Arrivée</th>
              <th>Durée</th>
              <th>Statut</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredActive.map((emp) => {
              const ptg = data.today_pointages.find(
                (p) =>
                  p.employee_id === emp.id && p.status !== "completed"
              );
              if (!ptg) return null;
              const elapsed = Math.floor(
                (Date.now() - new Date(ptg.clock_in).getTime()) / 1000
              );
              return (
                <tr key={emp.id}>
                  <td>
                    <strong>
                      {emp.first_name} {emp.last_name}
                    </strong>
                    <br />
                    <small style={{ color: "var(--text-muted)" }}>
                      {emp.matricule}
                    </small>
                  </td>
                  <td>{formatTime(ptg.clock_in)}</td>
                  <td>{formatDuration(elapsed)}</td>
                  <td>
                    {ptg.status === "in_progress" ? (
                      <Badge type="working">En poste</Badge>
                    ) : (
                      <Badge type="break">En pause</Badge>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      disabled={loading}
                      onClick={() => handleForce(ptg.id)}
                    >
                      Forcer sortie
                    </button>
                  </td>
                </tr>
              );
            })}
            {filteredCompleted.map((emp) => {
              const ptg = data.today_pointages.find(
                (p) => p.employee_id === emp.id
              );
              return (
                <tr key={emp.id}>
                  <td>
                    <strong>
                      {emp.first_name} {emp.last_name}
                    </strong>
                    <br />
                    <small style={{ color: "var(--text-muted)" }}>
                      {emp.matricule}
                    </small>
                  </td>
                  <td>{formatTime(ptg.clock_in)}</td>
                  <td>
                    {ptg.duration_seconds
                      ? formatDuration(ptg.duration_seconds)
                      : "—"}
                  </td>
                  <td>
                    <Badge type="offline">Terminé</Badge>
                  </td>
                  <td></td>
                </tr>
              );
            })}
            {filteredAbsent.map((emp) => (
              <tr key={emp.id} style={{ opacity: 0.5 }}>
                <td>
                  {emp.first_name} {emp.last_name}
                  <br />
                  <small>{emp.matricule}</small>
                </td>
                <td>—</td>
                <td>—</td>
                <td>
                  <Badge type="offline">Absent</Badge>
                </td>
                <td></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const MONTHS = [
  "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];

function PointagesPage({ search }) {
  const [pointages, setPointages] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const now = new Date();
  const [filters, setFilters] = useState({
    employee_id: "",
    month: String(now.getMonth() + 1),
    year: String(now.getFullYear()),
    date_from: "",
    date_to: "",
    status: "",
  });

  const loadEmployees = useCallback(async () => {
    try {
      setEmployees(await getEmployees());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    loadEmployees();
  }, [loadEmployees]);

  const load = useCallback(async () => {
    try {
      const params = {};
      if (filters.employee_id) params.employee_id = filters.employee_id;
      if (filters.month && filters.year) {
        params.month = filters.month;
        params.year = filters.year;
      } else {
        if (filters.date_from) params.date_from = filters.date_from;
        if (filters.date_to) params.date_to = filters.date_to;
      }
      if (filters.status) params.status = filters.status;
      setPointages(await getPointages(params));
    } catch (e) {
      console.error(e);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  const handleExportPDF = async () => {
    setExporting(true);
    try {
      const params = {};
      if (filters.employee_id) params.employee_id = filters.employee_id;
      if (filters.month && filters.year) {
        params.month = filters.month;
        params.year = filters.year;
      } else {
        if (filters.date_from) params.date_from = filters.date_from;
        if (filters.date_to) params.date_to = filters.date_to;
      }
      await exportPointagesPDF(params);
    } catch (e) {
      alert(e.message);
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteOne = async (id) => {
    if (!confirm("Supprimer ce pointage ?")) return;
    setDeleting(true);
    try {
      await deletePointage(id);
      load();
    } catch (e) {
      alert(e.message);
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteBulk = async () => {
    const label = filters.employee_id
      ? "cet employé"
      : `${MONTHS[filters.month]} ${filters.year}`;
    if (!confirm(`Supprimer tous les pointages de ${label} ? Cette action est irréversible.`)) return;
    setDeleting(true);
    try {
      const params = {};
      if (filters.employee_id) params.employee_id = filters.employee_id;
      if (filters.month && filters.year) {
        params.month = filters.month;
        params.year = filters.year;
      } else {
        if (filters.date_from) params.date_from = filters.date_from;
        if (filters.date_to) params.date_to = filters.date_to;
      }
      await deletePointages(params);
      load();
    } catch (e) {
      alert(e.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Historique des pointages</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn btn-primary"
            onClick={handleExportPDF}
            disabled={exporting}
          >
            {exporting ? "Export..." : "Exporter PDF"}
          </button>
          <button
            className="btn btn-danger"
            onClick={handleDeleteBulk}
            disabled={deleting}
          >
            {deleting ? "Suppression..." : "Supprimer"}
          </button>
        </div>
      </div>

      <div className="table-card">
        <div className="table-filters" style={{ flexWrap: "wrap", gap: 8 }}>
          <select
            className="filter-select"
            value={filters.employee_id}
            onChange={(e) =>
              setFilters({ ...filters, employee_id: e.target.value })
            }
          >
            <option value="">Tous les employés</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.first_name} {emp.last_name} ({emp.matricule})
              </option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.month}
            onChange={(e) =>
              setFilters({ ...filters, month: e.target.value, date_from: "", date_to: "" })
            }
          >
            <option value="">Mois</option>
            {MONTHS.map((name, i) =>
              i > 0 ? <option key={i} value={i}>{name}</option> : null
            )}
          </select>

          <select
            className="filter-select"
            value={filters.year}
            onChange={(e) =>
              setFilters({ ...filters, year: e.target.value, date_from: "", date_to: "" })
            }
          >
            <option value="">Année</option>
            {[2026, 2025, 2024, 2023].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.8rem", color: "var(--text-muted)" }}>
            ou
          </div>

          <input
            type="date"
            className="filter-input"
            value={filters.date_from}
            onChange={(e) =>
              setFilters({ ...filters, date_from: e.target.value, month: "", year: "" })
            }
            placeholder="Date début"
          />
          <input
            type="date"
            className="filter-input"
            value={filters.date_to}
            onChange={(e) =>
              setFilters({ ...filters, date_to: e.target.value, month: "", year: "" })
            }
            placeholder="Date fin"
          />

          <select
            className="filter-select"
            value={filters.status}
            onChange={(e) =>
              setFilters({ ...filters, status: e.target.value })
            }
          >
            <option value="">Tous les statuts</option>
            <option value="in_progress">En cours</option>
            <option value="completed">Terminé</option>
            <option value="flagged">Anomalie</option>
          </select>

          <button className="btn btn-teal btn-sm" onClick={load}>
            Filtrer
          </button>
        </div>

        <table>
          <thead>
            <tr>
              <th>Employé</th>
              <th>Entrée</th>
              <th>Sortie</th>
              <th>Durée</th>
              <th>Pause</th>
              <th>Statut</th>
              <th>IP</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {pointages
              .filter((p) => {
                if (!search) return true;
                const q = search.toLowerCase();
                return (
                  p.employee_name.toLowerCase().includes(q) ||
                  p.matricule.toLowerCase().includes(q)
                );
              })
              .map((p) => (
              <tr key={p.id}>
                <td>
                  <strong>{p.employee_name}</strong>
                  <br />
                  <small style={{ color: "var(--text-muted)" }}>
                    {p.matricule}
                  </small>
                </td>
                <td>{formatTime(p.clock_in)}</td>
                <td>{formatTime(p.clock_out)}</td>
                <td>{formatDuration(p.duration_seconds)}</td>
                <td>{formatDuration(p.total_break_seconds)}</td>
                <td>
                  <Badge
                    type={
                      p.status === "in_progress"
                        ? "working"
                        : p.status === "on_break"
                        ? "break"
                        : p.status === "flagged"
                        ? "flagged"
                        : "offline"
                    }
                  >
                    {p.status === "in_progress"
                      ? "En cours"
                      : p.status === "on_break"
                      ? "En pause"
                      : p.status === "flagged"
                      ? "Anomalie"
                      : "Terminé"}
                  </Badge>
                </td>
                <td>
                  <code style={{ fontSize: "0.75rem" }}>{p.source_ip}</code>
                </td>
                <td>
                  <button
                    className="btn btn-danger btn-sm"
                    disabled={deleting}
                    onClick={() => handleDeleteOne(p.id)}
                    title="Supprimer"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
            {pointages.length === 0 && (
              <tr>
                <td colSpan={8}>
                    <div className="empty-state">
                      <p>Aucun pointage trouvé</p>
                    </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function App() {
  const [employee, setEmployee] = useState(() => {
    const saved = localStorage.getItem("adminEmployee");
    return saved ? JSON.parse(saved) : null;
  });
  const [page, setPage] = useState("dashboard");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setAuthErrorHandler(() => {
      setEmployee(null);
      setPage("dashboard");
    });
  }, []);

  if (!employee) return <LoginScreen onLogin={(emp) => {
    localStorage.setItem("adminEmployee", JSON.stringify(emp));
    setEmployee(emp);
  }} />;

  const handleLogout = () => {
    logout();
    setEmployee(null);
    setPage("dashboard");
  };

  const crumbs = {
    dashboard: "Tableau de bord",
    employees: "Employés",
    presences: "Présences du jour",
    pointages: "Historique des pointages",
  };

  return (
    <div className="layout">
      <Sidebar page={page} onNavigate={setPage} />
      <div className="main">
        <div className="topbar">
          <div className="breadcrumb">
            <span className="current">{crumbs[page]}</span>
          </div>
          <div className="topbar-spacer" />
          <input
            className="topbar-search"
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
            {employee.first_name} {employee.last_name}
          </span>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleLogout}
            style={{ marginLeft: 8, fontSize: "0.8rem" }}
          >
            Déconnexion
          </button>
        </div>

        {page === "dashboard" && <DashboardPage search={search} />}
        {page === "employees" && <EmployeesPage search={search} />}
        {page === "presences" && <PresencesPage search={search} />}
        {page === "pointages" && <PointagesPage search={search} />}
      </div>
    </div>
  );
}
