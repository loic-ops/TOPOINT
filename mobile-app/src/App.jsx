import { useState, useEffect, useCallback, useRef } from "react";
import {
  loginPin,
  clockIn,
  clockOut,
  breakStart,
  breakEnd,
  getCurrentStatus,
} from "./api.js";

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
    .toString()
    .padStart(2, "0");
  const m = Math.floor((seconds % 3600) / 60)
    .toString()
    .padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function initials(first, last) {
  return `${(first || "")[0] || ""}${(last || "")[0] || ""}`.toUpperCase();
}

function showToast(msg, type, setToast) {
  setToast({ msg, type });
  setTimeout(() => setToast(null), 2500);
}

function PinScreen({ onLogin, onError }) {
  const [pin, setPin] = useState("");
  const [matricule, setMatricule] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const addDigit = (d) => {
    if (pin.length >= 4) return;
    const next = pin + d;
    setPin(next);
    setError("");
  };
  const delDigit = () => {
    setPin(pin.slice(0, -1));
    setError("");
  };

  const handleSubmit = async () => {
    if (!matricule.trim() || pin.length < 4) {
      setError("Matricule et 4 chiffres requis");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onLogin(matricule.trim(), pin);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pin-screen">
      <div className="pin-header">
        <h1>Entrez votre code PIN</h1>
        <p>Saisissez votre matricule et code</p>
      </div>

      <input
        type="text"
        placeholder="Matricule (ex: EMP0001)"
        value={matricule}
        onChange={(e) => setMatricule(e.target.value.toUpperCase())}
        style={{
          width: "100%",
          maxWidth: 300,
          padding: "14px 16px",
          border: "1.5px solid var(--border)",
          borderRadius: "var(--radius-sm)",
          fontSize: "0.95rem",
          textAlign: "center",
          marginBottom: 24,
          fontFamily: "inherit",
          letterSpacing: 1,
        }}
      />

      <div className="pin-dots">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className={`pin-dot ${i < pin.length ? "filled" : ""}`} />
        ))}
      </div>

      <div className="pin-keypad">
        {["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"].map(
          (key, i) => {
            if (key === "") return <div key={i} className="pin-key empty" />;
            if (key === "⌫")
              return (
                <button key={i} className="pin-key del" onClick={delDigit}>
                  ⌫
                </button>
              );
            return (
              <button
                key={i}
                className={`pin-key ${pin.length >= 4 ? "disabled" : ""}`}
                onClick={() => addDigit(key)}
              >
                {key}
              </button>
            );
          }
        )}
      </div>

      <button
        className="btn-validate"
        disabled={loading || pin.length < 4 || !matricule.trim()}
        onClick={handleSubmit}
      >
        {loading ? "Connexion..." : "Valider"}
      </button>
      <div className="pin-error">{error}</div>
    </div>
  );
}

function ClockScreen({ employee, onLogout }) {
  const [status, setStatus] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [breakElapsed, setBreakElapsed] = useState(0);
  const [toast, setToast] = useState(null);
  const [showConfirm, setShowConfirm] = useState(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);
  const breakTimerRef = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getCurrentStatus();
      setStatus(data);
      setElapsed(data.elapsed_seconds);
      setBreakElapsed(data.break_elapsed_seconds);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    if (status?.status === "in_progress") {
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [status?.status]);

  useEffect(() => {
    if (status?.status === "on_break") {
      breakTimerRef.current = setInterval(
        () => setBreakElapsed((e) => e + 1),
        1000
      );
    } else {
      clearInterval(breakTimerRef.current);
    }
    return () => clearInterval(breakTimerRef.current);
  }, [status?.status]);

  const handleAction = async (action) => {
    setLoading(true);
    try {
      if (action === "clock-in") await clockIn();
      else if (action === "clock-out") await clockOut();
      else if (action === "break-start") await breakStart();
      else if (action === "break-end") await breakEnd();

      if (navigator.vibrate) navigator.vibrate(10);
      const labels = {
        "clock-in": "Check In enregistré",
        "clock-out": "Check Out enregistré",
        "break-start": "Pause démarrée",
        "break-end": "Pause terminée",
      };
      showToast(labels[action], "success", setToast);
      await refresh();
    } catch (e) {
      showToast(e.message, "error", setToast);
    } finally {
      setLoading(false);
      setShowConfirm(null);
    }
  };

  const currentStatus = status?.status || "completed";
  const isWorking = currentStatus === "in_progress";
  const isOnBreak = currentStatus === "on_break";

  const statusLabel = isWorking
    ? "En poste"
    : isOnBreak
    ? "En pause"
    : "Hors service";
  const statusClass = isWorking
    ? "working"
    : isOnBreak
    ? "break"
    : "offline";

  return (
    <div className="clock-screen">
      <div className="clock-header">
        <div className="clock-header-top">
          <div className="clock-employee">
            <div className="clock-avatar">
              {initials(employee.first_name, employee.last_name)}
            </div>
            <div>
              <div className="clock-name">
                {employee.first_name} {employee.last_name}
              </div>
              <div className="clock-role">{employee.matricule}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="clock-center">
        <div className={`status-badge ${statusClass}`}>{statusLabel}</div>
        <div className="chrono">{formatTime(isOnBreak ? breakElapsed : elapsed)}</div>
        <div className="since">
          {status?.clock_in
            ? `Depuis ${new Date(status.clock_in).toLocaleTimeString("fr-FR", {
                hour: "2-digit",
                minute: "2-digit",
              })}`
            : ""}
        </div>

        {!isWorking && !isOnBreak && (
          <button
            className="btn-main clock-in"
            disabled={loading}
            onClick={() => setShowConfirm("clock-in")}
          >
            ▶
          </button>
        )}
        {isWorking && (
          <>
            <button
              className="btn-main clock-out"
              disabled={loading}
              onClick={() => setShowConfirm("clock-out")}
            >
              ⏹
            </button>
            <button
              className="btn-secondary"
              disabled={loading}
              onClick={() => setShowConfirm("break-start")}
            >
              ⏸ Faire une pause
            </button>
          </>
        )}
        {isOnBreak && (
          <>
            <button
              className="btn-main clock-in"
              disabled={loading}
              onClick={() => setShowConfirm("break-end")}
            >
              ▶
            </button>
            <button
              className="btn-main clock-out"
              style={{ width: 48, height: 48, fontSize: "1rem" }}
              disabled={loading}
              onClick={() => setShowConfirm("clock-out")}
            >
              ⏹
            </button>
          </>
        )}
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{formatTime(elapsed)}</div>
          <div className="stat-label">Temps total</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatTime(status?.total_break_seconds || 0)}</div>
          <div className="stat-label">Pause cumulée</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {employee.hourly_rate ? `${employee.hourly_rate}€` : "—"}
          </div>
          <div className="stat-label">Taux horaire</div>
        </div>
      </div>

      <div className="bottom-nav">
        <button className="nav-item active">
          Pointage
        </button>
        <button className="nav-item" onClick={onLogout}>
          Sortir
        </button>
      </div>

      <div className={`toast ${toast ? "" : "hidden"} ${toast?.type || ""}`}>
        {toast?.msg}
      </div>

      <div className={`modal-overlay ${showConfirm ? "" : "hidden"}`}>
        <div className="modal-card">
          <h3>
            {showConfirm === "clock-in"
              ? "Confirmer l'arrivée ?"
              : showConfirm === "clock-out"
              ? "Confirmer la sortie ?"
              : showConfirm === "break-start"
              ? "Commencer la pause ?"
              : "Terminer la pause ?"}
          </h3>
          <div className="modal-actions">
            <button
              className="modal-btn cancel"
              onClick={() => setShowConfirm(null)}
            >
              Annuler
            </button>
            <button
              className="modal-btn confirm"
              disabled={loading}
              onClick={() => handleAction(showConfirm)}
            >
              {loading ? "..." : "Confirmer"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [employee, setEmployee] = useState(() => {
    const saved = localStorage.getItem("authEmployee");
    return saved ? JSON.parse(saved) : null;
  });

  const handleLogin = async (matricule, pin) => {
    const data = await loginPin(matricule, pin);
    localStorage.setItem("authEmployee", JSON.stringify(data.employee));
    setEmployee(data.employee);
  };

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("authEmployee");
    setEmployee(null);
  };

  if (!employee) return <PinScreen onLogin={handleLogin} />;
  return <ClockScreen employee={employee} onLogout={handleLogout} />;
}
