// Wayfinder - Travel Itinerary Manager
// Integrated with Python FastAPI Backend & SQLite Database

const API_BASE_URL = 'http://localhost:8000';
const STORAGE_KEY = 'wayfinder_itineraries_v2';

let itineraries = [];
let pendingDeleteId = null;

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadData();
});

// ----------------------------------------------------
// DATA FETCHING & SYNCHRONIZATION WITH API
// ----------------------------------------------------
async function loadData() {
  try {
    const response = await fetch(`${API_BASE_URL}/trips`);
    if (response.ok) {
      itineraries = await response.json();
    } else {
      console.warn('API returned non-200, falling back to local cache');
      loadFallbackData();
    }
  } catch (error) {
    console.info('Backend API not reachable at http://localhost:8000, using local storage cache.');
    loadFallbackData();
  }
  renderDashboard();
  refreshIcons();
}

function loadFallbackData() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      itineraries = JSON.parse(stored);
    } catch (e) {
      itineraries = [];
    }
  } else {
    itineraries = [];
  }
}

function syncLocalCache() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(itineraries));
  updateStats();
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function setupEventListeners() {
  document.getElementById('btn-new-itinerary').addEventListener('click', () => openCreateModal());
  document.getElementById('itinerary-form').addEventListener('submit', handleSaveItinerary);
  document.getElementById('btn-confirm-delete').addEventListener('click', handleConfirmDelete);
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
// CRUD ACTIONS (CONNECTED TO API)
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
      const response = await fetch(`${API_BASE_URL}/trips/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        console.error('Failed to update trip via API');
      }
    } else {
      // CREATE VIA API
      const response = await fetch(`${API_BASE_URL}/trips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        console.error('Failed to create trip via API');
      }
    }
  } catch (error) {
    console.warn('API error during save, applying changes locally:', error);
    // Local fallback update
    if (id) {
      const idx = itineraries.findIndex(t => String(t.id) === String(id));
      if (idx !== -1) itineraries[idx] = { ...itineraries[idx], ...payload };
    } else {
      itineraries.unshift({ id: Date.now(), ...payload });
    }
    syncLocalCache();
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
    const response = await fetch(`${API_BASE_URL}/trips/${pendingDeleteId}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      console.error('Failed to delete trip via API');
    }
  } catch (error) {
    console.warn('API error during delete, removing locally:', error);
    itineraries = itineraries.filter(t => String(t.id) !== String(pendingDeleteId));
    syncLocalCache();
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
