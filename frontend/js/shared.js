// ==========================================
// CONFIGURATION
// ==========================================
const CONFIG = {
  API_URL: "https://f1-git-test-dvajfs-projects.vercel.app/api",
  TOKEN_KEY: "f1_access_token",
};

// ==========================================
// API SERVICE
// ==========================================
class ApiService {
  constructor() { this.baseUrl = CONFIG.API_URL; }
  getToken() { return localStorage.getItem(CONFIG.TOKEN_KEY); }
  setToken(t) { localStorage.setItem(CONFIG.TOKEN_KEY, t); }
  removeToken() { localStorage.removeItem(CONFIG.TOKEN_KEY); }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(this.getToken() && { Authorization: `Bearer ${this.getToken()}` }),
        ...options.headers,
      },
      ...options,
    };
    if (options.body && typeof options.body === "object") config.body = JSON.stringify(options.body);
    try {
      const response = await fetch(url, config);
      if (response.status === 401) { this.removeToken(); updateAuthUI(); throw new Error("Сессия истекла. Пожалуйста, войдите снова."); }
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(error.detail || `Ошибка ${response.status}`);
      }
      if (response.status === 204) return null;
      return response.json();
    } catch (error) {
      if (error.message === "Failed to fetch") throw new Error("Нет соединения с сервером");
      throw error;
    }
  }

  async login(email, password) {
    const fd = new URLSearchParams();
    fd.append("username", email); fd.append("password", password);
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: fd,
    });
    if (!response.ok) { const e = await response.json().catch(() => ({ detail: "Неверный логин или пароль" })); throw new Error(e.detail); }
    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }
  async updateMyProfile(data) {
  return this.request('/auth/users/me', { method: 'PATCH', body: data });
}
  async getPublicProfile(userId) { return this.request(`/auth/users/${userId}/public`); }
  async register(email, password) { return this.request("/auth/register", { method: "POST", body: { email, password } }); }
  async getCurrentUser() { return this.request("/auth/users/me"); }
  async getRaces() { return this.request("/races/"); }
  async getRace(id) { return this.request(`/races/${id}`); }
  async createRace(data) { if (data.time) data.time = new Date(data.time).toISOString(); return this.request("/races/", { method: "POST", body: data }); }
  async updateRace(id, data) { if (data.time) data.time = new Date(data.time).toISOString(); return this.request(`/races/${id}`, { method: "PATCH", body: data }); }
  async registerForRace(id) { return this.request(`/races/${id}/register`, { method: "POST" }); }
  async unregisterFromRace(id) { return this.request(`/races/${id}/unregister`, { method: "DELETE" }); }
  async getRaceParticipants(id) { return this.request(`/races/${id}/all_users`); }
  async getRaceResults(id) { return this.request(`/races/${id}/results`); }
  async setRaceResults(id, results) { return this.request(`/races/${id}/results`, { method: "POST", body: { results } }); }
  async submitReview(raceId, vote) { return this.request(`/races/${raceId}/review`, { method: "POST", body: { vote } }); }
  async deleteReview(raceId) { return this.request(`/races/${raceId}/review`, { method: "DELETE" }); }
  async getLeaderboard() { return this.request("/auth/users/leaderboard"); }
  async getNews() { return this.request("/news/"); }
  async getNewsItem(id) { return this.request(`/news/${id}`); }
  async createNews(data) { return this.request("/news/", { method: "POST", body: data }); }
  async updateNews(id, data) { return this.request(`/news/${id}`, { method: "PATCH", body: data }); }
  async deleteNews(id) { return this.request(`/news/${id}`, { method: "DELETE" }); }
}

const api = new ApiService();
let currentUser = null;

// ==========================================
// UTILITIES
// ==========================================
function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" }) + ", " +
    d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

function pluralize(n, a, b, c) {
  const m = n % 100;
  if (m >= 11 && m <= 14) return c;
  const m2 = n % 10;
  if (m2 === 1) return a;
  if (m2 >= 2 && m2 <= 4) return b;
  return c;
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = "toast show" + (isError ? " error" : "");
  setTimeout(() => (toast.className = "toast"), 3000);
}

function openModal(id) { document.getElementById(id)?.classList.add("open"); document.body.style.overflow = "hidden"; }
function closeModal(id) {
  document.getElementById(id)?.classList.remove("open");
  document.body.style.overflow = "";
  document.querySelectorAll(".form-error").forEach(el => el.classList.remove("visible"));
}

function getStatusClass(status) {
  if (status === "Регистрация") return "status-reg";
  if (status === "Завершена") return "status-done";
  return "status-cancel";
}

// ==========================================
// AUTH
// ==========================================
async function initAuth() {
  if (api.getToken()) {
    try { currentUser = await api.getCurrentUser(); } catch (e) { api.removeToken(); currentUser = null; }
  }
  updateAuthUI();
  return currentUser;
}

function updateAuthUI() {
  const btnLogin = document.getElementById("btn-login");
  const btnRegister = document.getElementById("btn-register-nav");
  const btnCreate = document.getElementById("btn-create");
  const btnAdmin = document.getElementById("btn-admin");
  const btnProfile = document.getElementById("btn-profile");
  if (!btnLogin) return;

  if (currentUser) {
    btnLogin.style.display = "none";
    btnRegister.textContent = "Выйти";
    btnRegister.onclick = logout;
    if (btnProfile) btnProfile.style.display = "";
    const canCreate = currentUser.is_verified || currentUser.is_superuser;
    if (btnCreate) btnCreate.style.display = canCreate ? "" : "none";
    if (btnAdmin) btnAdmin.style.display = currentUser.is_superuser ? "" : "none";
  } else {
    btnLogin.style.display = "";
    btnRegister.textContent = "Регистрация";
    btnRegister.onclick = () => openAuthModal("signup");
    if (btnCreate) btnCreate.style.display = "none";
    if (btnAdmin) btnAdmin.style.display = "none";
    if (btnProfile) btnProfile.style.display = "none";
  }
}

function logout() {
  api.removeToken(); currentUser = null;
  updateAuthUI(); showToast("Вы вышли из аккаунта");
  setTimeout(() => window.location.href = "/", 800);
}

function openAuthModal(tab = "login") { switchAuthTab(tab); openModal("modal-auth"); }

function switchAuthTab(tab) {
  document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
  document.querySelector(`[data-tab="${tab}"]`)?.classList.add("active");
  ["login", "signup", "forgot", "reset"].forEach(f => {
    const el = document.getElementById(`form-${f}`);
    if (el) el.style.display = f === tab ? "block" : "none";
  });
}

async function handleLogin(e) {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById("btn-submit-login");
  btn.disabled = true; btn.textContent = "Вход...";
  try {
    await api.login(form.email.value, form.password.value);
    currentUser = await api.getCurrentUser();
    updateAuthUI(); closeModal("modal-auth");
    showToast(`Добро пожаловать, ${currentUser.email}!`);
    form.reset();
    if (typeof onLoginSuccess === "function") onLoginSuccess();
  } catch (error) {
    const el = document.getElementById("error-login-email");
    if (el) { el.textContent = error.message; el.classList.add("visible"); }
  } finally { btn.disabled = false; btn.textContent = "Войти"; }
}

async function handleRegister(e) {
  e.preventDefault();
  const form = e.target;
  const errorEl = document.getElementById("error-signup-general");
  if (form.password.value !== form.password2.value) {
    errorEl.textContent = "Пароли не совпадают"; errorEl.classList.add("visible"); return;
  }
  const btn = document.getElementById("btn-submit-signup");
  btn.disabled = true; btn.textContent = "Создание...";
  try {
    await api.register(form.email.value, form.password.value);
    await api.login(form.email.value, form.password.value);
    currentUser = await api.getCurrentUser();
    updateAuthUI(); closeModal("modal-auth");
    showToast("Аккаунт создан! Добро пожаловать!");
    form.reset();
    if (typeof onLoginSuccess === "function") onLoginSuccess();
  } catch (error) { errorEl.textContent = error.message; errorEl.classList.add("visible"); }
  finally { btn.disabled = false; btn.textContent = "Создать аккаунт"; }
}

async function handleForgotPassword(e) { e.preventDefault(); showToast("Функция в разработке", true); }
async function handleResetPassword(e) { e.preventDefault(); showToast("Функция в разработке", true); }

// ==========================================
// HEADER RENDER
// ==========================================
function renderHeader(activePage) {
  const header = document.getElementById("site-header");
  if (!header) return;
  header.innerHTML = `
    <div class="header-top">
      <a class="nav-logo" href="/">F1<span class="nav-logo-badge">online</span></a>
      <div class="header-top-center">
        <a href="https://discord.gg/dsCxutnVft" class="header-discord-link" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057.1 18.08.113 18.1.131 18.11a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/></svg>
          Discord
        </a>
        <div class="header-streams">
          <a href="https://www.twitch.tv/?lang=ru" class="stream-pill" target="_blank" rel="noopener">
            <span class="live-dot"></span>Twitch
          </a>
        </div>
      </div>
      <div class="header-top-right">
        <button class="nav-btn" id="btn-admin" style="display:none" onclick="toggleAdmin()">Панель</button>
        <button class="nav-btn" id="btn-create" style="display:none" onclick="openCreateRace()">+ Создать</button>
        <button class="nav-btn" id="btn-profile" style="display:none" onclick="window.location.href='/profile'">Профиль</button>
        <button class="nav-btn" id="btn-login" onclick="openAuthModal('login')">Войти</button>
        <button class="nav-btn primary" id="btn-register-nav" onclick="openAuthModal('signup')">Регистрация</button>
      </div>
    </div>
    <nav class="header-nav">
      ${[
        ['/', 'home', 'Главная'],
        ['/news', 'news', 'Новости'],
        ['/download', 'download', 'Скачать'],
        ['/rating', 'rating', 'Рейтинг пилотов'],
        ['/info', 'info', 'Информация'],
      ].map(([href, page, label]) =>
        `<div class="hnav-item"><a class="hnav-link${activePage === page ? ' active' : ''}" href="${href}">${label}</a></div>`
      ).join('')}
    </nav>
  `;
}

function openCreateRace() {
  if (document.getElementById('modal-create')) { openModal('modal-create'); }
  else { window.location.href = '/?action=create'; }
}

function toggleAdmin() {
  const panel = document.getElementById('admin-panel');
  if (panel) panel.classList.toggle('visible');
  else window.location.href = '/?action=admin';
}

// ==========================================
// AUTH MODAL (injected into every page)
// ==========================================
function injectAuthModal() {
  if (document.getElementById("modal-auth")) return;
  const div = document.createElement("div");
  div.innerHTML = `
    <div class="modal-overlay" id="modal-auth">
      <div class="modal">
        <div class="modal-header" style="padding-bottom:1rem">
          <div class="modal-title">Аккаунт</div>
          <button class="modal-close" onclick="closeModal('modal-auth')">✕</button>
        </div>
        <div class="modal-body" style="padding-top:0">
          <div class="auth-tabs">
            <button class="auth-tab active" data-tab="login" onclick="switchAuthTab('login')">Войти</button>
            <button class="auth-tab" data-tab="signup" onclick="switchAuthTab('signup')">Создать аккаунт</button>
          </div>
          <form id="form-login" onsubmit="handleLogin(event)">
            <div class="form-group">
              <label class="form-label">Имя</label>
              <input class="form-input" name="email" placeholder="Ваше имя" required/>
              <div class="form-error" id="error-login-email"></div>
            </div>
            <div class="form-group">
              <label class="form-label">Пароль</label>
              <input class="form-input" type="password" name="password" placeholder="••••••••" required minlength="6"/>
            </div>
            <div style="text-align:right;margin-bottom:1rem;">
              <a onclick="switchAuthTab('forgot')" style="color:var(--red);cursor:pointer;font-size:12px;">Забыли пароль?</a>
            </div>
            <button type="submit" class="btn btn-red" style="width:100%" id="btn-submit-login">Войти</button>
            <div class="form-footer">Нет аккаунта? <a onclick="switchAuthTab('signup')">Зарегистрироваться</a></div>
          </form>
          <form id="form-signup" style="display:none" onsubmit="handleRegister(event)">
            <div class="form-group">
              <label class="form-label">Имя</label>
              <input class="form-input" name="email" placeholder="Ваше имя" required/>
              <div class="form-error" id="error-signup-email"></div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Пароль</label>
                <input class="form-input" type="password" name="password" placeholder="••••••••" required minlength="6"/>
              </div>
              <div class="form-group">
                <label class="form-label">Повтор пароля</label>
                <input class="form-input" type="password" name="password2" placeholder="••••••••" required minlength="6"/>
              </div>
            </div>
            <div class="form-error" id="error-signup-general"></div>
            <button type="submit" class="btn btn-red" style="width:100%" id="btn-submit-signup">Создать аккаунт</button>
            <div class="form-footer">Уже есть аккаунт? <a onclick="switchAuthTab('login')">Войти</a></div>
          </form>
          <form id="form-forgot" style="display:none" onsubmit="handleForgotPassword(event)">
            <div class="form-group">
              <label class="form-label">Имя</label>
              <input class="form-input" name="email" placeholder="Ваше имя" required/>
              <div class="form-error" id="error-forgot-email"></div>
            </div>
            <div class="form-error" id="error-forgot-general"></div>
            <button type="submit" class="btn btn-red" style="width:100%" id="btn-submit-forgot">Отправить ссылку</button>
            <div class="form-footer"><a onclick="switchAuthTab('login')">Вернуться к входу</a></div>
          </form>
          <form id="form-reset" style="display:none" onsubmit="handleResetPassword(event)">
            <input type="hidden" name="token" id="reset-token"/>
            <div class="form-group">
              <label class="form-label">Новый пароль</label>
              <input class="form-input" type="password" name="password" placeholder="••••••••" required minlength="6"/>
            </div>
            <div class="form-group">
              <label class="form-label">Повтор пароля</label>
              <input class="form-input" type="password" name="password2" placeholder="••••••••" required minlength="6"/>
            </div>
            <div class="form-error" id="error-reset-general"></div>
            <button type="submit" class="btn btn-red" style="width:100%" id="btn-submit-reset">Сменить пароль</button>
          </form>
        </div>
      </div>
    </div>`;
  document.body.appendChild(div.firstElementChild);
}

function injectToast() {
  if (document.getElementById("toast")) return;
  const t = document.createElement("div");
  t.className = "toast"; t.id = "toast";
  document.body.appendChild(t);
}

// ==========================================
// POINTS TABLE
// ==========================================
const POINTS_TABLE = {1:60,2:55,3:50,4:47,5:44,6:42,7:40,8:38,9:35,10:32,11:28,12:25,13:22,14:20,15:18,16:16,17:13,18:10,19:5,20:0};
