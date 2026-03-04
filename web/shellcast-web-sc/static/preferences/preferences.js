"use strict";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";
import { auth, authorizedFetch } from "../common/js/common.js";
import { initNotificationForm } from "../common/js/notification_prefs.js";

// ============================================================================
// CONSTANTS
// ============================================================================
const LEASE_SEARCH_DELAY = 400;

// ============================================================================
// GLOBAL STATE
// ============================================================================
let profileInfo = {};
let savedProfileData = {}; // Original data from database for comparison
let leases = [];
let leaseSearchTimer = null;

// ============================================================================
// PROFILE FORM FUNCTIONS
// ============================================================================

/**
 * Retrieves the current user's profile information from the server.
 * @return {object} the user's profile information (email and phone number)
 */
async function getProfileInfo() {
  const res = await authorizedFetch("/user-info");
  if (res.ok) {
    return await res.json();
  }
  console.log("Problem retrieving user profile information.");
  return null;
}

/**
 * Builds all of the lease forms based on the provided leases data.
 * @param {Array} leasesData the array of lease objects to display
 */
function buildLeaseInfoEls(leasesData = leases) {
  const leasesAccordion = document.getElementById("leases-accordion");
  leasesAccordion.innerHTML = "";

  if (leasesData && leasesData.length > 0) {
    for (let lease of leasesData) {
      leasesAccordion.innerHTML += createLeaseInfoEl(lease);
    }

    // Initialize event listeners
    for (let lease of leasesData) {
      initLeaseInfoEl(lease);
    }
  } else {
    leasesAccordion.innerHTML =
      '<div class="text-muted text-center p-3">No leases found. Use the search above to add your first lease.</div>';
  }
}

/**
 * Returns an HTML string describing a collapsible lease info form.
 * @param {object} lease the lease data to populate the form with
 * @return {string} HTML string for the lease form
 */
function createLeaseInfoEl(lease) {
  return `
    <div class="card">
      <div class="card-header" id="heading-${lease.lease_id}">
        <h2 class="mb-0 d-flex">
          <button class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#collapse-${lease.lease_id}" aria-expanded="false" aria-controls="collapse-${lease.lease_id}">
            Lease: ${lease.lease_id}
          </button>
          <div>
            <button class="btn btn-danger" type="button" id="delete-btn-${lease.lease_id}">Delete</button>
          </div>
        </h2>
      </div>

      <div id="collapse-${lease.lease_id}" class="collapse" aria-labelledby="heading-${lease.lease_id}" data-parent="#leases-accordion">
        <div class="card-body">
          <form class="needs-validation mb-4" id="form-${lease.id}">
            <div class="mb-3 inline-text-input">
              <label for="lease-${lease.lease_id}-lease-id">Lease ID</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-lease-id" value="${lease.lease_id}" name="lease-id" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.lease_id}-grow-area">NC Division of Marine Fisheries Shellfish Growing Area</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-grow-area" value="${lease.grow_area_name}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.lease_id}-grow-area-desc">Growing Area Description</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-grow-area-desc" value="${lease.grow_area_desc}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-grow-unit">NC Division of Marine Fisheries Shellfish Growing Unit</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-grow-unit" value="${lease.cmu_name}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.lease_id}-rainfall-threshold">Lease Closure Rainfall Threshold (inches)</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-rainfall-threshold" value="${lease.rainfall_thresh_in}" readonly>
            </div>
            <small class="form-text text-muted">
              The rainfall threshold is the amount of rainfall in inches within a
              24-hour period that results in a lease being temporarily closed for
              harvest. The NC Division of Marine Fisheries determines the threshold.
            </small>
          </form>
        </div>
      </div>
    </div>
  `;
}

/**
 * Initializes the form that corresponds to the lease with the given id and data.
 * @param {object} lease the lease data to initialize the form with
 * @param {boolean} ignoreAddingEventListeners whether or not to ignore adding event listeners
 */
function initLeaseInfoEl(lease, ignoreAddingEventListeners) {
  const deleteBtn = document.getElementById(`delete-btn-${lease.lease_id}`);

  if (!ignoreAddingEventListeners) {
    deleteBtn.addEventListener("click", () => deleteLease(lease.lease_id));
  }
}

/**
 * Adds the given lease to the user's leases.
 * @param {string} leaseId the NCDMF lease id of the lease to add
 */
async function addLease(leaseId) {
  const res = await authorizedFetch("/leases", {
    method: "POST",
    headers: { "Content-Type": "application/json;charset=utf-8" },
    body: JSON.stringify({ lease_id: leaseId }),
  });

  if (res.ok) {
    const lease = await res.json();
    const idxOfLease = leases.findIndex((x) => x.lease_id === lease.lease_id);
    if (idxOfLease === -1) {
      leases.push(lease);
    }
    buildLeaseInfoEls(leases);
  } else {
    const errors = (await res.json()).errors;
    console.log("There was a problem while adding the lease:", errors);
  }

  clearLeaseSearch();
}

/**
 * Deletes the given lease from the user's leases.
 * @param {string} leaseId the NCDMF lease id of the lease to delete
 */
async function deleteLease(leaseId) {
  const res = await authorizedFetch("/leases", {
    method: "DELETE",
    headers: { "Content-Type": "application/json;charset=utf-8" },
    body: JSON.stringify({ lease_id: leaseId }),
  });

  if (res.ok) {
    const idxOfLease = leases.findIndex((x) => x.lease_id === leaseId);
    leases.splice(idxOfLease, 1);
    buildLeaseInfoEls(leases);
  } else {
    const errors = (await res.json()).errors;
    console.log("There was a problem while deleting the lease:", errors);
  }
}

// ============================================================================
// LEASE SEARCH FUNCTIONS
// ============================================================================

/**
 * Searches through leases by the NCDMF lease id with the text entered by the user.
 */
async function searchLeases() {
  const searchResultsDiv = document.getElementById("lease-search-results");
  const userInput = document.getElementById("lease-search-text-input").value;

  if (userInput === "") {
    clearLeaseSearch();
    return;
  }

  const res = await authorizedFetch("/search-leases", {
    method: "POST",
    headers: { "Content-Type": "application/json;charset=utf-8" },
    body: JSON.stringify({ search: userInput }),
  });

  if (res.ok) {
    const returnedLeases = await res.json();
    searchResultsDiv.innerHTML = "";

    if (returnedLeases.length > 0) {
      for (let lease of returnedLeases) {
        searchResultsDiv.innerHTML += `<button type="button" class="list-group-item list-group-item-action">${lease}</button>`;
      }
      for (let button of searchResultsDiv.children) {
        button.addEventListener("click", () => addLease(button.textContent));
      }
    } else {
      searchResultsDiv.innerHTML =
        '<button type="button" class="list-group-item list-group-item-action">No leases with a similar ID were found.</button>';
    }
    searchResultsDiv.style.display = "flex";
  } else {
    console.log("There was an error while searching for leases.");
    searchResultsDiv.innerHTML =
      '<button type="button" class="list-group-item list-group-item-action">An error occurred. Please try again.</button>';
    searchResultsDiv.style.display = "flex";
  }
}

/**
 * Clears the search box and removes all search results from the UI.
 */
function clearLeaseSearch() {
  document.getElementById("lease-search-text-input").value = "";
  const searchResultsDiv = document.getElementById("lease-search-results");
  searchResultsDiv.innerHTML = "";
  searchResultsDiv.style.display = "none";
}

/**
 * Debounced search function to avoid excessive API calls.
 */
function searchLeasesOnDelay() {
  if (leaseSearchTimer !== null) {
    clearTimeout(leaseSearchTimer);
  }
  leaseSearchTimer = setTimeout(searchLeases, LEASE_SEARCH_DELAY);
}

// ============================================================================
// ACCOUNT MANAGEMENT FUNCTIONS
// ============================================================================

/**
 * Deletes the user's account.
 */
async function deleteAccount() {
  const res = await authorizedFetch("/delete-account");
  if (res.ok) {
    window.location.replace("/");
  } else {
    const errors = (await res.json()).errors;
    console.log("There was a problem while deleting the account:", errors);
  }
}

// ============================================================================
// AUTHENTICATION HANDLERS
// ============================================================================

/**
 * Displays the UI for a signed-in user and initializes the lease forms.
 * Called when Firebase auth state is signed in; the check is done by the caller (onAuthStateChanged).
 */
async function handleSignedInUser() {
  // Show signed in view
  document.getElementById("user-signed-in").style.display = "block";
  document.getElementById("user-signed-out").style.display = "none";

  // Get user's profile information
  profileInfo = await getProfileInfo();
  window.userProfileInfo = profileInfo;
  initNotificationForm({
    authorizedFetch,
    getProfileInfo: () => profileInfo,
    setProfileInfo: (v) => {
      profileInfo = v;
    },
    getSavedProfileData: () => savedProfileData,
    setSavedProfileData: (v) => {
      savedProfileData = v;
    },
  });

  // Setup delete account button
  document.getElementById("confirm-account-deletion-btn").addEventListener("click", deleteAccount);

  // Setup lease search functionality
  document.getElementById("lease-search-text-input").addEventListener("input", searchLeasesOnDelay);
  document.getElementById("lease-search-btn").addEventListener("click", searchLeases);
  document.getElementById("lease-clear-btn").addEventListener("click", clearLeaseSearch);

  // Get user's leases
  const res = await authorizedFetch("/leases");
  if (res.ok) {
    leases = await res.json();
  } else {
    console.log("There was a problem while retrieving the user's leases");
  }

  // Setup lease forms
  buildLeaseInfoEls(leases);
}

/**
 * Displays the UI for a signed-out user.
 */
function handleSignedOutUser() {
  window.location.replace("/map");
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Initialize the application when the page loads
(async () => {
  onAuthStateChanged(auth, (user) => {
    user ? handleSignedInUser() : handleSignedOutUser();
  });
})();
