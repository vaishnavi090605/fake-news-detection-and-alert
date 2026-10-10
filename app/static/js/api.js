// Shared API helper — used by login.html, dashboard.html, admin.html
// Since these are served BY the FastAPI app itself (same origin), relative
// URLs work directly without CORS issues.

const API = {
  base: "", // same-origin; FastAPI serves these static files itself

  getToken() {
    return localStorage.getItem("fnd_token");
  },
  getRole() {
    return localStorage.getItem("fnd_role");
  },
  getUsername() {
    return localStorage.getItem("fnd_username");
  },
  setSession(token, role, username) {
    localStorage.setItem("fnd_token", token);
    localStorage.setItem("fnd_role", role);
    localStorage.setItem("fnd_username", username);
  },
  clearSession() {
    localStorage.removeItem("fnd_token");
    localStorage.removeItem("fnd_role");
    localStorage.removeItem("fnd_username");
  },
  requireAuth() {
    if (!this.getToken()) {
      window.location.href = "/static/login.html";
    }
  },
  logout() {
    this.clearSession();
    window.location.href = "/static/login.html";
  },

  async request(path, { method = "GET", body = null, form = false } = {}) {
    const headers = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let fetchBody = undefined;
    if (body) {
      if (form) {
        headers["Content-Type"] = "application/x-www-form-urlencoded";
        fetchBody = new URLSearchParams(body).toString();
      } else {
        headers["Content-Type"] = "application/json";
        fetchBody = JSON.stringify(body);
      }
    }

    const res = await fetch(this.base + path, { method, headers, body: fetchBody });

    if (res.status === 401) {
      this.clearSession();
      window.location.href = "/static/login.html";
      throw new Error("Not authenticated");
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((d) => d.msg).join(", ")
        : (data.detail || "Something went wrong");
      throw new Error(detail);
    }
    return data;
  },

  register(username, email, password, adminCode) {
    const body = { username, email, password };
    if (adminCode) body.admin_code = adminCode;
    return this.request("/register", { method: "POST", body });
  },

  login(username, password) {
    return this.request("/login", {
      method: "POST",
      form: true,
      body: { grant_type: "password", username, password },
    });
  },

  predict(text, category, source_url, evidence_link, user_location) {
    const body = { text };
    if (category) body.category = category;
    if (source_url) body.source_url = source_url;
    if (evidence_link) body.evidence_link = evidence_link;
    if (user_location) body.user_location = user_location;
    return this.request("/predict", { method: "POST", body });
  },


  history() {
    return this.request("/history");
  },

  stats() {
    return this.request("/stats");
  },

  alerts() {
    return this.request("/alerts");
  },

  userReports() {
    return this.request("/user/reports");
  },

  report(text, reason) {
    return this.request("/report", { method: "POST", body: { text, reason } });
  },

  getProfile() {
    return this.request("/user/profile");
  },

  updateProfile(data) {
    return this.request("/user/profile", { method: "PUT", body: data });
  },

  async exportCSV() {
    const token = this.getToken();
    try {
      const res = await fetch(this.base + "/reports/export/csv", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to download CSV");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "truthguard_analysis_report.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      window.location.href = `/reports/export/csv?token=${encodeURIComponent(token)}`;
    }
  },


  generatePoliceReport(alertId = 1) {
    return this.request(`/police-report/${alertId}`, { method: "POST" });
  },

  adminStats() {
    return this.request("/admin/stats");
  },

  adminAlerts() {
    return this.request("/admin/alerts");
  },

  adminReports() {
    return this.request("/admin/reports");
  },

  updateReportStatus(reportId, statusValue) {
    return this.request(`/admin/reports/${reportId}?status_value=${encodeURIComponent(statusValue)}`, {
      method: "PATCH",
    });
  },
};
