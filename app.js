// Wayfinder - Travel Itinerary Manager
import {
    LeafletMap,
    TileLayer,
    Marker,
    Circle,
    Polygon,
    Popup
} from 'leaflet';
const STORAGE_KEY = 'wayfinder_itineraries_v2';

// Seed sample itineraries
const SAMPLE_ITINERARIES = [
  {
    id: 'trip-1',
    title: 'Highlights of Japan',
    destination: 'Tokyo & Kyoto, Japan',
    startDate: '2026-10-10',
    endDate: '2026-10-20',
    budget: 2800,
    status: 'planned',
    image: 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80',
    notes: 'JR Pass activated on arrival. Shinkansen between Tokyo and Kyoto. Hotel bookings in Shinjuku.'
  },
  {
    id: 'trip-2',
    title: 'Weekend in Rome',
    destination: 'Rome, Italy',
    startDate: '2026-07-05',
    endDate: '2026-07-08',
    budget: 650,
    status: 'in-progress',
    image: 'https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80',
    notes: 'Visit the Colosseum and Vatican museums. Walking tour around the historic center.'
  }
];

let itineraries = [];
let pendingDeleteId = null;
let map;
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  setupEventListeners();
  renderDashboard();
  refreshIcons();
  initializeMap();
});

function initializeMap() {
  map = new LeafletMap('map')
    .setView([56.1829, 15.59], 20);

  new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  const marker = new Marker([56.1829, 15.59]).addTo(map);
  const marker2 = new Marker([56.182999, 15.59123]).addTo(map);
  
}
async function geocodeDestination(destination) {
    const url =
        `https://nominatim.openstreetmap.org/search?` +
        `q=${encodeURIComponent(destination)}` +
        `&format=jsonv2&limit=1`;

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error('Nominatim request failed');
    }

    const results = await response.json();

    if (results.length === 0) {
        return null;
    }

    return {
        latitude: Number(results[0].lat),
        longitude: Number(results[0].lon)
    };
}

function loadData() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      itineraries = JSON.parse(stored);
    } catch (e) {
      console.error('Error loading data:', e);
      itineraries = SAMPLE_ITINERARIES;
    }
  } else {
    itineraries = SAMPLE_ITINERARIES;
    saveData();
  }
}

function saveData() {
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

  if (itineraries.length === 0) {
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

    return `
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col justify-between">
        ${trip.image ? `
          <div class="h-36 w-full bg-gray-100 overflow-hidden">
            <img src="${trip.image}" alt="${trip.title}" class="w-full h-full object-cover">
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
              <i data-lucide="map-pin" class="w-3.5 h-3.5 mr-1 text-gray-400"></i> ${trip.destination}
            </p>

            ${(trip.startDate || trip.endDate) ? `
              <p class="text-xs text-gray-500 mt-1 flex items-center">
                <i data-lucide="calendar" class="w-3.5 h-3.5 mr-1 text-gray-400"></i> ${formatDates(trip.startDate, trip.endDate)}
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
// CRUD ACTIONS
// ----------------------------------------------------
function openCreateModal() {
  document.getElementById('modal-title').innerText = 'New Trip';
  document.getElementById('itinerary-form').reset();
  document.getElementById('form-id').value = '';
  document.getElementById('form-status').value = 'planned';
  document.getElementById('itinerary-modal').classList.remove('hidden');
}

function openEditModalById(id) {
  const trip = itineraries.find(t => t.id === id);
  if (!trip) return;

  document.getElementById('modal-title').innerText = 'Edit Trip';
  document.getElementById('form-id').value = trip.id;
  document.getElementById('form-title').value = trip.title;
  document.getElementById('form-destination').value = trip.destination;
  document.getElementById('form-start-date').value = trip.startDate || '';
  document.getElementById('form-end-date').value = trip.endDate || '';
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
  const title = document.getElementById('form-title').value.trim();
  const destination = document.getElementById('form-destination').value.trim();
  const coordinates = await geocodeDestination(destination);
  if (!coordinates) {
    alert('Could not find that destination.');
    return;
  }
  const startDate = document.getElementById('form-start-date').value;
  const endDate = document.getElementById('form-end-date').value;
  const budget = parseFloat(document.getElementById('form-budget').value) || 0;
  const status = document.getElementById('form-status').value;
  const image = document.getElementById('form-image').value.trim();
  const notes = document.getElementById('form-notes').value.trim();
  

  if (id) {
    const trip = itineraries.find(t => t.id === id);
    if (trip) {
      trip.title = title;
      trip.destination = destination;
      trip.latitude = coordinates.latitude;
      trip.longitude = coordinates.longitude;
      trip.startDate = startDate;
      trip.endDate = endDate;
      trip.budget = budget;
      trip.status = status;
      trip.image = image;
      trip.notes = notes;
      new Marker([trip.latitude, trip.longitude])
                .addTo(map)
                .bindPopup(trip.destination);
    }
  } else {
    const newTrip = {
        id: 'trip-' + Date.now(),
        title,
        destination,
        latitude: coordinates.latitude,
        longitude: coordinates.longitude,
        startDate,
        endDate,
        budget,
        status,
        image,
        notes
    };
    itineraries.unshift(newTrip);
    new Marker([newTrip.latitude, newTrip.longitude])
        .addTo(map)
        .bindPopup(newTrip.destination);

    };
  
  

  saveData();
  closeModal();
  renderDashboard();
}

function openDeleteModal(tripId) {
  pendingDeleteId = tripId;
  document.getElementById('delete-modal').classList.remove('hidden');
}

function closeDeleteModal() {
  pendingDeleteId = null;
  document.getElementById('delete-modal').classList.add('hidden');
}

function handleConfirmDelete() {
  if (!pendingDeleteId) return;
  itineraries = itineraries.filter(t => t.id !== pendingDeleteId);
  saveData();
  closeDeleteModal();
  renderDashboard();
}

function updateStats() {
  const totalTrips = itineraries.length;
  let totalBudget = 0;
  itineraries.forEach(trip => {
    totalBudget += (Number(trip.budget) || 0);
  });

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
window.openCreateModal = openCreateModal;
window.openEditModalById = openEditModalById;
window.openDeleteModal = openDeleteModal;
window.closeModal = closeModal;
window.closeDeleteModal = closeDeleteModal;