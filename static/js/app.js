/* ID GPS — umumiy UI xatti-harakatlari (kutubxonasiz) */
(function () {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const store = {
    get(key) { try { return localStorage.getItem(key); } catch (e) { return null; } },
    set(key, val) { try { localStorage.setItem(key, val); } catch (e) { /* private rejim */ } },
  };

  const icon = (name, cls = 'icon') =>
    `<svg class="${cls}" aria-hidden="true"><use href="#i-${name}"></use></svg>`;

  /* ---------- Raqamlar ---------- */
  const IDGPS = window.IDGPS = {
    parseMoney(v) { return parseInt(String(v || '').replace(/[^\d-]/g, ''), 10) || 0; },
    formatMoney(n) { return String(Math.round(n || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); },
    getCookie(name) {
      const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
      return m ? decodeURIComponent(m.pop()) : null;
    },
    icon,
  };

  /* ---------- Tema ---------- */
  function currentTheme() {
    const set = document.documentElement.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function syncThemeButtons() {
    const dark = currentTheme() === 'dark';
    $$('[data-theme-toggle]').forEach(btn => {
      btn.innerHTML = icon(dark ? 'sun' : 'moon');
      btn.setAttribute('aria-label', dark ? "Yorug' rejim" : 'Qorong\'i rejim');
      btn.title = btn.getAttribute('aria-label');
    });
  }
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-theme-toggle]');
    if (!btn) return;
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    store.set('idgps-theme', next);
    syncThemeButtons();
    document.dispatchEvent(new CustomEvent('themechange', { detail: next }));
  });

  /* ---------- Sidebar (mobil) ---------- */
  document.addEventListener('click', e => {
    const app = $('.app');
    if (!app) return;
    if (e.target.closest('[data-nav-toggle]')) app.classList.toggle('nav-open');
    else if (e.target.closest('.backdrop')) app.classList.remove('nav-open');
  });

  /* ---------- Dropdown ---------- */
  document.addEventListener('click', e => {
    const trigger = e.target.closest('[data-dropdown]');
    $$('.dropdown__menu').forEach(m => {
      if (!trigger || m !== trigger.parentElement.querySelector('.dropdown__menu')) m.hidden = true;
    });
    if (trigger) {
      const menu = trigger.parentElement.querySelector('.dropdown__menu');
      menu.hidden = !menu.hidden;
      trigger.setAttribute('aria-expanded', String(!menu.hidden));
    }
  });

  /* ---------- Toast ---------- */
  const TOAST_ICONS = { success: 'check-circle', error: 'alert', warning: 'alert', info: 'info' };
  function dismissToast(el) {
    el.classList.add('is-leaving');
    setTimeout(() => el.remove(), 250);
  }
  function wireToast(el) {
    const timeout = el.classList.contains('toast--error') ? 8000 : 4500;
    let timer = setTimeout(() => dismissToast(el), timeout);
    el.addEventListener('mouseenter', () => clearTimeout(timer));
    el.addEventListener('mouseleave', () => { timer = setTimeout(() => dismissToast(el), 2500); });
    el.querySelector('[data-dismiss]')?.addEventListener('click', () => dismissToast(el));
  }
  IDGPS.toast = function (message, type = 'success') {
    let box = $('.toasts');
    if (!box) { box = document.createElement('div'); box.className = 'toasts'; document.body.appendChild(box); }
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');
    el.innerHTML = `<span class="toast__icon">${icon(TOAST_ICONS[type] || 'info', 'icon icon-sm')}</span>
      <div class="toast__body"></div>
      <button type="button" class="btn-icon" data-dismiss aria-label="Yopish">${icon('x', 'icon icon-sm')}</button>`;
    el.querySelector('.toast__body').textContent = message;
    box.appendChild(el);
    wireToast(el);
  };

  /* ---------- Tasdiqlash oynasi ---------- */
  let pendingForm = null;
  function openConfirm(form) {
    const modal = $('#confirm-modal');
    if (!modal) return form.submit();
    pendingForm = form;
    $('#confirm-title', modal).textContent = form.dataset.confirmTitle || "O'chirishni tasdiqlang";
    $('#confirm-text', modal).textContent = form.dataset.confirm || 'Bu amalni qaytarib bo\'lmaydi.';
    $('#confirm-ok', modal).textContent = form.dataset.confirmOk || "Ha, o'chirish";
    modal.hidden = false;
    $('#confirm-cancel', modal).focus();
  }
  function closeConfirm() { const m = $('#confirm-modal'); if (m) m.hidden = true; pendingForm = null; }
  document.addEventListener('submit', e => {
    const form = e.target;
    if (form.dataset.confirm !== undefined && !form.dataset.confirmed) {
      e.preventDefault();
      openConfirm(form);
    }
  });
  document.addEventListener('click', e => {
    if (e.target.closest('#confirm-cancel') || e.target.id === 'confirm-modal') closeConfirm();
    if (e.target.closest('#confirm-ok') && pendingForm) {
      const f = pendingForm;
      f.dataset.confirmed = '1';
      closeConfirm();
      f.requestSubmit ? f.requestSubmit() : f.submit();
    }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeConfirm();
      $('.app')?.classList.remove('nav-open');
      $$('.dropdown__menu').forEach(m => { m.hidden = true; });
    }
    // "/" — sahifadagi qidiruvga fokus
    if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
      const s = $('[data-table-search]');
      if (s) { e.preventDefault(); s.focus(); }
    }
  });

  /* ---------- Summa inputlari: yozayotganda 1 000 000 ko'rinishi ---------- */
  function formatMoneyInput(input) {
    const raw = input.value.replace(/\D/g, '');
    const caretFromEnd = input.value.length - (input.selectionStart ?? input.value.length);
    input.value = raw ? IDGPS.formatMoney(parseInt(raw, 10)) : '';
    const pos = Math.max(0, input.value.length - caretFromEnd);
    if (document.activeElement === input) {
      try { input.setSelectionRange(pos, pos); } catch (e) { /* type=number emas */ }
    }
  }
  document.addEventListener('input', e => {
    if (e.target.matches('[data-money]')) formatMoneyInput(e.target);
  });
  // Yuborishdan oldin probellarni olib tashlaymiz (server ham tozalaydi — bu qo'shimcha himoya)
  document.addEventListener('submit', e => {
    if (e.defaultPrevented) return;
    $$('[data-money]', e.target).forEach(i => { i.value = i.value.replace(/\s/g, ''); });
    const btn = e.target.querySelector('[type=submit]');
    if (btn && !e.target.dataset.noLock) {
      btn.classList.add('is-disabled');
      setTimeout(() => btn.classList.remove('is-disabled'), 4000);
    }
  });

  /* ---------- Parolni ko'rsatish / nusxalash ---------- */
  document.addEventListener('click', e => {
    const reveal = e.target.closest('[data-reveal]');
    if (reveal) {
      const target = reveal.dataset.reveal ? $(reveal.dataset.reveal) : reveal.parentElement.querySelector('input, .secret__value');
      if (target.tagName === 'INPUT') {
        const show = target.type === 'password';
        target.type = show ? 'text' : 'password';
        reveal.innerHTML = icon(show ? 'eye-off' : 'eye', 'icon icon-sm');
      } else {
        const show = target.dataset.hidden !== 'false';
        target.textContent = show ? target.dataset.value : '••••••';
        target.dataset.hidden = show ? 'false' : 'true';
        reveal.innerHTML = icon(show ? 'eye-off' : 'eye', 'icon icon-sm');
      }
    }
    const copy = e.target.closest('[data-copy]');
    if (copy) {
      navigator.clipboard?.writeText(copy.dataset.copy).then(
        () => IDGPS.toast('Nusxalandi', 'info'),
        () => IDGPS.toast('Nusxalab bo\'lmadi', 'error'),
      );
    }
  });

  /* ---------- Jadval: qidiruv ---------- */
  // Guruhlangan jadvallarda (rowspan) bir mijozning qatorlari data-group orqali birga ko'rsatiladi.
  function applySearch(input) {
    const table = $(input.dataset.tableSearch);
    if (!table) return;
    const q = input.value.trim().toLowerCase();
    const rows = $$('tbody tr:not(.no-results)', table);
    const groups = new Map();
    rows.forEach(r => {
      const key = r.dataset.group || r;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(r);
    });
    let visible = 0;
    const filter = table.dataset.filter || '';
    groups.forEach(list => {
      const text = list.map(r => r.dataset.search || r.textContent).join(' ').toLowerCase();
      const statusOk = !filter || list[0].dataset.status === filter;
      const show = statusOk && (!q || text.includes(q));
      list.forEach(r => { r.hidden = !show; });
      if (show) visible++;
    });
    let empty = $('tbody tr.no-results', table);
    if (!visible && rows.length) {
      if (!empty) {
        empty = document.createElement('tr');
        empty.className = 'no-results';
        empty.innerHTML = `<td colspan="99">Hech narsa topilmadi</td>`;
        $('tbody', table).appendChild(empty);
      }
      empty.hidden = false;
    } else if (empty) empty.hidden = true;
    const counter = $(`[data-count-for="${input.dataset.tableSearch}"]`);
    if (counter) counter.textContent = visible;
  }
  document.addEventListener('input', e => {
    if (e.target.matches('[data-table-search]')) applySearch(e.target);
  });

  // Holat filtri (segmented) — sahifani qayta yuklamasdan
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-filter-table]');
    if (!btn) return;
    const table = $(btn.dataset.filterTable);
    table.dataset.filter = btn.dataset.filterValue || '';
    $$(`[data-filter-table="${btn.dataset.filterTable}"]`).forEach(b => b.classList.toggle('is-active', b === btn));
    const search = $(`[data-table-search="${btn.dataset.filterTable}"]`);
    if (search) applySearch(search);
  });

  /* ---------- Jadval: saralash ---------- */
  document.addEventListener('click', e => {
    const th = e.target.closest('th[data-sort]');
    if (!th) return;
    const table = th.closest('table');
    const tbody = $('tbody', table);
    const idx = Array.from(th.parentElement.children).indexOf(th);
    const type = th.dataset.sort;
    const asc = !th.classList.contains('is-asc');
    $$('th[data-sort]', table).forEach(h => h.classList.remove('is-asc', 'is-desc'));
    th.classList.add(asc ? 'is-asc' : 'is-desc');
    const val = r => {
      const cell = r.children[idx];
      const v = cell?.dataset.value ?? cell?.textContent.trim() ?? '';
      return type === 'num' ? parseFloat(v) || 0 : v.toLowerCase();
    };
    $$('tr:not(.no-results)', tbody)
      .sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * (asc ? 1 : -1))
      .forEach(r => tbody.appendChild(r));
  });

  /* ---------- Fayl tanlash nomi ---------- */
  document.addEventListener('change', e => {
    if (e.target.matches('.upload input[type=file]')) {
      const name = e.target.files[0]?.name;
      const label = e.target.closest('.upload').querySelector('.upload__name');
      if (label) label.textContent = name || 'Excel fayl';
      const submit = e.target.closest('form').querySelector('[type=submit]');
      if (submit) submit.hidden = !name;
    }
  });

  /* ---------- Belgilar hisoblagichi ---------- */
  function updateCounter(ta) {
    const out = $(`[data-counter-for="${ta.id}"]`);
    if (!out) return;
    const left = (parseInt(ta.getAttribute('maxlength'), 10) || 0) - ta.value.length;
    out.textContent = `${left} ta belgi qoldi`;
    out.classList.toggle('is-warn', left < 100);
  }
  document.addEventListener('input', e => { if (e.target.matches('textarea[maxlength]')) updateCounter(e.target); });

  /* ---------- Boshlang'ich holat ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    syncThemeButtons();
    $$('.toast').forEach(wireToast);
    $$('textarea[maxlength]').forEach(updateCounter);
    $$('[data-money]').forEach(i => { if (i.value) formatMoneyInput(i); });
    const firstInvalid = $('.is-invalid');
    if (firstInvalid) firstInvalid.focus();
  });
})();
