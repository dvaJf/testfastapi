let bets = [];
let currentFilter = "открыта";
let currentBetId = null;
let selectedOptionId = null;
let currentBetData = null;

async function init() {
  renderHeader("bets");
  injectAuthModal();
  injectToast();
  await initAuth();

  if (currentUser?.is_superuser) {
    document.getElementById("btn-create-bet").style.display = "";
    document.getElementById("admin-panel").style.display = "";
    await loadAdminTable();
  }

  await loadBets();
  document.getElementById("loading-overlay").classList.add("hidden");
}

async function loadBets() {
  try {
    bets = await api.getBets();
    renderBets();
  } catch (e) {
    showToast(e.message, true);
  }
}

function renderBets() {
  const grid = document.getElementById("bets-grid");
  const filtered = currentFilter === "all"
    ? bets
    : bets.filter(b => b.status === currentFilter);

  if (!filtered.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="empty-state-icon">🎲</div>Нет ставок</div>`;
    return;
  }

  grid.innerHTML = filtered.map(bet => `
    <div class="bet-card" onclick="openBetDetail(${bet.id})">
      <div class="bet-card-top">
        <div class="bet-type">Ставки</div>
        <span class="bet-status ${getBetStatusClass(bet.status)}">${bet.status}</span>
      </div>
      <h3>${bet.title}</h3>
      ${bet.description ? `<div class="bet-card-desc">${bet.description}</div>` : ''}
      <div class="bet-options">
        ${bet.options_count} ${pluralize(bet.options_count, 'вариант', 'варианта', 'вариантов')}
      </div>
      <div class="bet-card-meta">
        <span>📅 ${formatDate(bet.closes_at)}</span>
        ${bet.creator_email ? `<span>👤 ${bet.creator_email}</span>` : ''}
      </div>
      <div class="bet-card-footer">
        <div>
          <div style="font-size:11px;color:var(--text3);">Пул</div>
          <div class="pool-amount">${bet.total_pool} ★</div>
        </div>
        ${bet.status === 'открыта' ? `<button class="register-btn" onclick="event.stopPropagation();openPlaceBetModal(${bet.id})">Ставка</button>` : ''}
      </div>
    </div>
  `).join('');
}

function getBetStatusClass(status) {
  if (status === "открыта") return "open";
  if (status === "закрыта") return "closed";
  return "resolved";
}

function setFilter(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll(".filter-chip").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderBets();
}

// ==========================================
// CREATE BET (Admin)
// ==========================================
function openCreateBetModal() {
  document.getElementById("form-create-bet").reset();
  document.getElementById("error-create-bet").classList.remove("visible");
  // Set min datetime to now
  const now = new Date();
  now.setMinutes(now.getMinutes() + 30); // 30 min from now
  document.getElementById("create-closes-at").min = now.toISOString().slice(0, 16);
  // Initialize with two empty option rows
  const container = document.getElementById("create-options-container");
  container.innerHTML = "";
  addCreateOptionRow();
  addCreateOptionRow();
  openModal("modal-create-bet");
}

function addCreateOptionRow() {
  const container = document.getElementById("create-options-container");
  const row = document.createElement("div");
  row.className = "edit-option-row";
  row.innerHTML = `
    <input class="form-input" type="text" placeholder="Вариант ответа" required />
    <button type="button" class="btn btn-red btn-sm" onclick="this.closest('.edit-option-row').remove()">✕</button>
  `;
  container.appendChild(row);
}

async function handleCreateBet(e) {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById("btn-submit-create-bet");
  btn.disabled = true;

  try {
    const options = [];
    const optionRows = document.querySelectorAll("#create-options-container .edit-option-row input");
    optionRows.forEach(input => {
      const label = input.value.trim();
      if (label) {
        options.push({ label });
      }
    });

    if (options.length < 2) {
      throw new Error("Нужно минимум 2 варианта");
    }

    const closesAt = new Date(form.closes_at.value);

    await api.createBet({
      title: form.title.value,
      description: form.description.value || null,
      closes_at: closesAt.toISOString(),
      options: options,
    });

    closeModal("modal-create-bet");
    showToast("Ставка создана!");
    await loadBets();
    if (currentUser?.is_superuser) await loadAdminTable();
  } catch (e) {
    const el = document.getElementById("error-create-bet");
    el.textContent = e.message;
    el.classList.add("visible");
  } finally {
    btn.disabled = false;
  }
}

// ==========================================
// PLACE BET
// ==========================================
async function openPlaceBetModal(betId) {
  currentBetId = betId;
  selectedOptionId = null;

  try {
    const bet = await api.getBet(betId);
    currentBetData = bet;

    document.getElementById("bet-modal-title").textContent = `Ставка: ${bet.title}`;
    document.getElementById("user-score-display").innerHTML = `Ваши очки: <span>${currentUser?.score || 0} ★</span>`;

    const container = document.getElementById("bet-options-container");
    container.innerHTML = `
      <div class="bet-options-list">
        ${bet.options.map(opt => `
          <div class="bet-option-item" onclick="selectBetOption(${opt.id}, this)">
            <div class="bet-option-radio"></div>
            <div class="bet-option-label">${opt.label}</div>
            <div class="bet-option-pool">${opt.total_stakes || 0} ★</div>
          </div>
        `).join('')}
      </div>
    `;

    document.getElementById("bet-stake").value = "";
    document.getElementById("error-bet-stake").classList.remove("visible");
    openModal("modal-place-bet");
  } catch (e) {
    showToast(e.message, true);
  }
}

function selectBetOption(optionId, el) {
  selectedOptionId = optionId;
  document.querySelectorAll(".bet-option-item").forEach(item => item.classList.remove("selected"));
  el.classList.add("selected");
}

async function submitBet() {
  const stake = parseInt(document.getElementById("bet-stake").value);
  if (!selectedOptionId) {
    showToast("Выберите вариант", true);
    return;
  }
  if (!stake || stake < 1) {
    const el = document.getElementById("error-bet-stake");
    el.textContent = "Введите сумму от 1 очка";
    el.classList.add("visible");
    return;
  }

  try {
    await api.placeBet(currentBetId, { option_id: selectedOptionId, stake: stake });
    closeModal("modal-place-bet");
    showToast("Ставка принята!");
    // Refresh user data
    currentUser = await api.getCurrentUser();
    await loadBets();
  } catch (e) {
    const el = document.getElementById("error-bet-stake");
    el.textContent = e.message;
    el.classList.add("visible");
  }
}

// ==========================================
// EDIT BET (Admin)
// ==========================================
let editOptionCounter = 0;

async function openEditBetModal(betId) {
  try {
    const bet = await api.getBet(betId);
    currentBetId = betId;
    currentBetData = bet;

    document.getElementById("edit-bet-id").value = betId;
    document.getElementById("edit-bet-title").value = bet.title;
    document.getElementById("edit-bet-description").value = bet.description || "";
    document.getElementById("edit-bet-status").value = bet.status;

    // Format datetime-local
    const d = new Date(bet.closes_at);
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    document.getElementById("edit-bet-closes-at").value = d.toISOString().slice(0, 16);

    // Populate options
    const container = document.getElementById("edit-options-container");
    container.innerHTML = "";
    editOptionCounter = 0;

    if (bet.options && bet.options.length) {
      bet.options.forEach(opt => {
        addEditOptionRow(opt.label, opt.id, opt.total_stakes || 0);
      });
    }

    document.getElementById("error-edit-bet").classList.remove("visible");
    openModal("modal-edit-bet");
  } catch (e) {
    showToast(e.message, true);
  }
}

function addEditOptionRow(label = "", id = null, totalStakes = 0) {
  const container = document.getElementById("edit-options-container");
  const rowId = id || ("new_" + (editOptionCounter++));
  const canDelete = totalStakes === 0;

  const row = document.createElement("div");
  row.className = "edit-option-row";
  row.dataset.optionId = rowId;
  row.innerHTML = `
    <input type="hidden" name="option_id" value="${id || ''}" />
    <input class="form-input" type="text" name="option_label" placeholder="Вариант ответа" value="${label}" required />
    ${canDelete ? `<button type="button" class="btn btn-red btn-sm" onclick="removeEditOptionRow(this)">✕</button>` : '<span style="font-size:11px;color:var(--text3);">Ставки есть</span>'}
  `;
  container.appendChild(row);
}

function removeEditOptionRow(btn) {
  btn.closest(".edit-option-row").remove();
}

async function handleEditBet(e) {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById("btn-submit-edit-bet");
  btn.disabled = true;

  try {
    const betId = document.getElementById("edit-bet-id").value;
    const options = [];
    const optionRows = document.querySelectorAll("#edit-options-container .edit-option-row");

    optionRows.forEach(row => {
      const labelInput = row.querySelector('input[name="option_label"]');
      const idInput = row.querySelector('input[name="option_id"]');
      const label = labelInput.value.trim();
      if (label) {
        const opt = { label };
        if (idInput && idInput.value) {
          opt.id = parseInt(idInput.value);
        }
        options.push(opt);
      }
    });

    if (options.length < 2) {
      throw new Error("Нужно минимум 2 варианта");
    }

    const closesAt = new Date(form.closes_at.value);

    const data = {
      title: form.title.value,
      description: form.description.value || null,
      closes_at: closesAt.toISOString(),
      status: form.status.value,
      options: options,
    };

    await api.updateBet(betId, data);
    closeModal("modal-edit-bet");
    showToast("Ставка обновлена!");
    await loadBets();
    if (currentUser?.is_superuser) await loadAdminTable();
  } catch (e) {
    const el = document.getElementById("error-edit-bet");
    el.textContent = e.message;
    el.classList.add("visible");
  } finally {
    btn.disabled = false;
  }
}

async function deleteBet(betId) {
  if (!confirm("Удалить эту ставку? Средства будут возвращены участникам.")) return;
  try {
    await api.deleteBet(betId);
    showToast("Ставка удалена");
    await loadBets();
    if (currentUser?.is_superuser) await loadAdminTable();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// RESOLVE BET (Admin)
// ==========================================
async function openResolveModal(betId) {
  currentBetId = betId;
  try {
    const bet = await api.getBet(betId);
    const container = document.getElementById("resolve-options-container");
    container.innerHTML = `
      <div class="bet-options-list">
        ${bet.options.map(opt => `
          <div class="bet-option-item" onclick="selectResolveOption(${opt.id}, this)">
            <div class="bet-option-radio"></div>
            <div class="bet-option-label">${opt.label}</div>
            <div class="bet-option-pool">${opt.total_stakes || 0} ★</div>
          </div>
        `).join('')}
      </div>
    `;
    openModal("modal-resolve-bet");
  } catch (e) {
    showToast(e.message, true);
  }
}

function selectResolveOption(optionId, el) {
  selectedOptionId = optionId;
  document.querySelectorAll("#resolve-options-container .bet-option-item").forEach(item => item.classList.remove("selected"));
  el.classList.add("selected");
}

async function submitResolve() {
  if (!selectedOptionId) {
    showToast("Выберите выигрышный вариант", true);
    return;
  }

  try {
    await api.resolveBet(currentBetId, { winning_option_id: selectedOptionId });
    closeModal("modal-resolve-bet");
    showToast("Ставка завершена, очки распределены!");
    await loadBets();
    if (currentUser?.is_superuser) await loadAdminTable();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// ADMIN TABLE
// ==========================================
async function loadAdminTable() {
  try {
    const allBets = await api.getBets();
    const tbody = document.getElementById("admin-bets-tbody");
    tbody.innerHTML = allBets.map(bet => `
      <tr>
        <td>${bet.id}</td>
        <td>${bet.title}</td>
        <td><span class="bet-status ${getBetStatusClass(bet.status)}">${bet.status}</span></td>
        <td>${formatDate(bet.closes_at)}</td>
        <td>${bet.total_pool} ★</td>
        <td>
          <div class="admin-actions-cell">
            <button class="btn btn-sm" onclick="openEditBetModal(${bet.id})">Редактировать</button>
            <button class="btn btn-red btn-sm" onclick="deleteBet(${bet.id})">Удалить</button>
            ${bet.status !== 'завершена' ? `
              <button class="btn btn-red btn-sm" onclick="openResolveModal(${bet.id})">Завершить</button>
            ` : '<span style="color:var(--text3);font-size:11px;">Завершена</span>'}
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// BET DETAIL (view options)
// ==========================================
async function openBetDetail(betId) {
  try {
    const bet = await api.getBet(betId);
    currentBetData = bet;

    if (bet.status === 'открыта' && !bet.user_has_bet) {
      openPlaceBetModal(betId);
      return;
    }

    // Just show the bet details in a simple alert for now
    const optionsText = bet.options.map(o => `${o.label}: ${o.total_stakes || 0} ★`).join('\n');
    alert(`Ставка: ${bet.title}\nСтатус: ${bet.status}\n\nВарианты:\n${optionsText}`);
  } catch (e) {
    showToast(e.message, true);
  }
}

// Init
init();
