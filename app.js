// Wayfinder - Travel Itinerary Manager
// Integrated with Python FastAPI Backend, SQLite Database & User Authentication (US8 & US9)

const API_BASE_URL = 'http://localhost:8000';
const TOKEN_KEY = 'wayfinder_jwt_token';
const EMAIL_KEY = 'wayfinder_user_email';

let itineraries = [];
let pendingDeleteId = null;
let currentAuthMode = 'login'; // 'login' or 'register'

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  updateAuthUI();
  if (getAuthToken()) {
    loadData();
  } else {
    renderDashboard();
  }
});

function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getAuthHeaders() {
  const token = getAuthToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ----------------------------------------------------
// AUTH UI & STATE
// ----------------------------------------------------
function updateAuthUI() {
  const token = getAuthToken();
  const email = localStorage.getItem(EMAIL_KEY);
  const loggedOutBox = document.getElementById('auth-logged-out');
  const loggedInBox = document.getElementById('auth-logged-in');
  const emailDisplay = document.getElementById('user-display-email');

  if (token && email) {
    loggedOutBox.classList.add('hidden');
    loggedInBox.classList.remove('hidden');
    emailDisplay.innerText = email;
  } else {
    loggedInBox.classList.add('hidden');
    loggedOutBox.classList.remove('hidden');
  }
}

function openAuthModal(mode = 'login') {
  currentAuthMode = mode;
  const modal = document.getElementById('auth-modal');
  const title = document.getElementById('auth-modal-title');
  const submitBtn = document.getElementById('auth-submit-btn');
  const toggleText = document.getElementById('auth-toggle-text');
  const toggleBtn = document.getElementById('auth-toggle-btn');
  const errorMsg = document.getElementById('auth-error-msg');

  errorMsg.classList.add('hidden');
  errorMsg.innerText = '';
  document.getElementById('auth-form').reset();

  if (mode === 'register') {
    title.innerText = 'Create Account';
    submitBtn.innerText = 'Sign Up';
    toggleText.innerText = 'Already have an account?';
    toggleBtn.innerText = 'Log in';
  } else {
    title.innerText = 'Login';
    submitBtn.innerText = 'Login';
    toggleText.innerText = "Don't have an account?";
    toggleBtn.innerText = 'Sign Up';
  }

  modal.classList.remove('hidden');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
}

function handleLogout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
  itineraries = [];
  updateAuthUI();
  renderDashboard();
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;
  const errorMsg = document.getElementById('auth-error-msg');

  errorMsg.classList.add('hidden');
  errorMsg.innerText = '';

  try {
    if (currentAuthMode === 'register') {
      // US8: Register
      const regRes = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!regRes.ok) {
        const data = await regRes.json();
        throw new Error(data.detail || 'Registration failed');
      }

      // Auto-login after successful registration
      const loginRes = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const loginData = await loginRes.json();
      localStorage.setItem(TOKEN_KEY, loginData.access_token);
      localStorage.setItem(EMAIL_KEY, email);
    } else {
      // US9: Login
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Invalid email or password');
      }

      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(EMAIL_KEY, email);
    }

    closeAuthModal();
    updateAuthUI();
    await loadData();
  } catch (err) {
    errorMsg.innerText = err.message;
    errorMsg.classList.remove('hidden');
  }
}

// ----------------------------------------------------
// DATA FETCHING & SYNCHRONIZATION WITH API
// ----------------------------------------------------
async function loadData() {
  const token = getAuthToken();
  if (!token) {
    itineraries = [];
    renderDashboard();
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/trips`, {
      headers: getAuthHeaders()
    });

    if (response.status === 401) {
      console.warn('Session expired or unauthorized');
      handleLogout();
      openAuthModal('login');
      return;
    }

    if (response.ok) {
      itineraries = await response.json();
    } else {
      itineraries = [];
    }
  } catch (error) {
    console.warn('API not reachable:', error);
    itineraries = [];
  }

  renderDashboard();
  refreshIcons();
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function setupEventListeners() {
  document.getElementById('btn-new-itinerary').addEventListener('click', () => {
    if (!getAuthToken()) {
      openAuthModal('login');
    } else {
      openCreateModal();
    }
  });

  document.getElementById('itinerary-form').addEventListener('submit', handleSaveItinerary);
  document.getElementById('btn-confirm-delete').addEventListener('click', handleConfirmDelete);

  // Auth Event Listeners
  document.getElementById('btn-open-login').addEventListener('click', () => openAuthModal('login'));
  document.getElementById('btn-open-register').addEventListener('click', () => openAuthModal('register'));
  document.getElementById('btn-logout').addEventListener('click', handleLogout);
  document.getElementById('auth-form').addEventListener('submit', handleAuthSubmit);
  document.getElementById('auth-toggle-btn').addEventListener('click', () => {
    openAuthModal(currentAuthMode === 'login' ? 'register' : 'login');
  });
}

// ----------------------------------------------------
// DASHBOARD RENDERING
// ----------------------------------------------------
function renderDashboard() {
  const grid = document.getElementById('itinerary-grid');
  const emptyState = document.getElementById('empty-state');

  updateStats();

  if (!itineraries || itineraries.length === 0) {
    grid.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');
  grid.innerHTML = itineraries.map(trip => {
    const statusLabels = {
      'planned': { label: 'Planned', badge: 'bg-blue-50 text-blue-700 border-blue-200' },
      'in-progress': { label: 'In Progress', badge: 'bg-amber-50 text-amber-700 border-amber-200' },
      'completed': { label: 'Completed', badge: 'bg-gray-100 text-gray-700 border-gray-200' }
    };
    const status = statusLabels[trip.status] || statusLabels['planned'];
    const startDate = trip.start_date || trip.startDate;
    const endDate = trip.end_date || trip.endDate;

    return `
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col justify-between">
        ${trip.image ? `
          <div class="h-36 w-full bg-gray-100 overflow-hidden">
            <img src="${trip.image}" alt="${trip.title}" class="w-full h-full object-cover" onerror="this.parentElement.style.display='none'">
          </div>
        ` : ''}

        <div class="p-4 flex-1 flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-[11px] font-medium px-2 py-0.5 rounded border ${status.badge}">
                ${status.label}
              </span>
              <span class="text-xs font-semibold text-gray-800">
                ${trip.budget ? '$' + Number(trip.budget).toLocaleString() : 'No budget'}
              </span>
            </div>

            <h3 class="font-bold text-base text-gray-900 mt-2">${trip.title}</h3>
            <p class="text-xs text-gray-500 mt-0.5 flex items-center">
              <i data-lucide="map-pin" class="w-3.5 h-3.5 mr-1 text-gray-400"></i> ${trip.destination || 'No destination'}
            </p>

            ${(startDate || endDate) ? `
              <p class="text-xs text-gray-500 mt-1 flex items-center">
                <i data-lucide="calendar" class="w-3.5 h-3.5 mr-1 text-gray-400"></i> ${formatDates(startDate, endDate)}
              </p>
            ` : ''}

            ${trip.notes ? `
              <p class="text-xs text-gray-600 mt-2.5 bg-gray-50 p-2 rounded border border-gray-100 line-clamp-2">
                ${trip.notes}
              </p>
            ` : ''}
          </div>

          <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
            <button onclick="openEditModalById('${trip.id}')" class="px-2.5 py-1 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded transition">
              Edit
            </button>
            <button onclick="openDeleteModal('${trip.id}')" class="px-2.5 py-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded transition">
              Delete
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  refreshIcons();
}

// ----------------------------------------------------
// CRUD ACTIONS (CONNECTED TO API WITH JWT)
// ----------------------------------------------------
function openCreateModal() {
  document.getElementById('modal-title').innerText = 'New Trip';
  document.getElementById('itinerary-form').reset();
  document.getElementById('form-id').value = '';
  document.getElementById('form-status').value = 'planned';
  document.getElementById('itinerary-modal').classList.remove('hidden');
}

function openEditModalById(id) {
  const trip = itineraries.find(t => String(t.id) === String(id));
  if (!trip) return;

  document.getElementById('modal-title').innerText = 'Edit Trip';
  document.getElementById('form-id').value = trip.id;
  document.getElementById('form-title').value = trip.title;
  document.getElementById('form-destination').value = trip.destination || '';
  document.getElementById('form-start-date').value = trip.start_date || trip.startDate || '';
  document.getElementById('form-end-date').value = trip.end_date || trip.endDate || '';
  document.getElementById('form-budget').value = trip.budget || '';
  document.getElementById('form-status').value = trip.status || 'planned';
  document.getElementById('form-image').value = trip.image || '';
  document.getElementById('form-notes').value = trip.notes || '';

  document.getElementById('itinerary-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('itinerary-modal').classList.add('hidden');
}

async function handleSaveItinerary(e) {
  e.preventDefault();
  const id = document.getElementById('form-id').value;
  const payload = {
    title: document.getElementById('form-title').value.trim(),
    destination: document.getElementById('form-destination').value.trim(),
    start_date: document.getElementById('form-start-date').value || null,
    end_date: document.getElementById('form-end-date').value || null,
    budget: parseFloat(document.getElementById('form-budget').value) || 0,
    status: document.getElementById('form-status').value,
    image: document.getElementById('form-image').value.trim() || null,
    notes: document.getElementById('form-notes').value.trim() || null
  };

  try {
    if (id) {
      // UPDATE VIA API
      await fetch(`${API_BASE_URL}/trips/${id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });
    } else {
      // CREATE VIA API
      await fetch(`${API_BASE_URL}/trips`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });
    }
  } catch (error) {
    console.error('API error saving trip:', error);
  }

  closeModal();
  await loadData();
}

function openDeleteModal(tripId) {
  pendingDeleteId = tripId;
  document.getElementById('delete-modal').classList.remove('hidden');
}

function closeDeleteModal() {
  pendingDeleteId = null;
  document.getElementById('delete-modal').classList.add('hidden');
}

async function handleConfirmDelete() {
  if (!pendingDeleteId) return;

  try {
    await fetch(`${API_BASE_URL}/trips/${pendingDeleteId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
  } catch (error) {
    console.error('API error deleting trip:', error);
  }

  closeDeleteModal();
  await loadData();
}

function updateStats() {
  const totalTrips = itineraries ? itineraries.length : 0;
  let totalBudget = 0;
  if (itineraries) {
    itineraries.forEach(trip => {
      totalBudget += (Number(trip.budget) || 0);
    });
  }

  const elTrips = document.getElementById('stat-total-trips');
  const elBudg = document.getElementById('stat-total-budget');

  if (elTrips) elTrips.innerText = totalTrips;
  if (elBudg) elBudg.innerText = '$' + totalBudget.toLocaleString();
}

function formatDates(start, end) {
  if (!start && !end) return 'Flexible Dates';
  if (start && !end) return `From ${start}`;
  if (!start && end) return `Until ${end}`;
  return `${start} → ${end}`;
}
