"use strict";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";
import { auth, authorizedFetch } from "../common/common.js";
import { initNotificationForm } from "../common/js/notification_prefs.js";

/* The number of milliseconds between when a user changes the lease search
   text and when an API request is sent for a lease search */
const LEASE_SEARCH_DELAY = 400;
/** The path to the growing unit boundaries file. */
const LEASES_BOUNDS_PATH = "static/fl_leases_boundary.geojson";

let profileInfo = {};
let savedProfileData = {}; // Original data from database for comparison
let leases = [];

// the id of the latest lease search timer
let leaseSearchTimer = null;

/**
 * Retrieves the current user's profile information from the server.
 * @return {object} the user's profile information (email and phone number)
 */
async function getProfileInfo() {
  try {
    const res = await authorizedFetch("/userInfo");
    if (res.ok) {
      return await res.json();
    }
    console.log("Problem retrieving user profile information.");
    return null;
  } catch (error) {
    console.error("Error retrieving user profile information:", error);
    return null;
  }
}

async function getGeoJsonLeases() {
  let auz_leases = [];
  let individual_leases = [];
  let data = fetch(LEASES_BOUNDS_PATH)
    .then((response) => response.json())
    .then((data) => {
      data.features.forEach((feature) => {
        if (feature.properties.src == "AUZ") {
          if (auz_leases.indexOf(feature.properties.parcel_nam) === -1) {
            auz_leases.push(feature.properties.parcel_nam);
          }
        } else if (feature.properties.src == "Individual") {
          if (individual_leases.indexOf(feature.properties.waterbody) === -1) {
            individual_leases.push(feature.properties.waterbody);
          }
        }
      });
    });
  //  const auzDiv = document.querySelector("#auz-menu");
  //  for (let i = 0; auz_leases.length; i++) {
  //    // console.log(auz_leases[i]);
  //    // auzDiv.innerHTML += `<a class="dropdown-item" href="#">auz_leases[i]</a>`;
  //  }
}

// function createDropdowns(leases) {
//   const auzDiv = document.querySelector("#auz-menu");
//   console.log(leases.auz.length);
//   // leases.auz.forEach((name) => {
//   //   auzDiv.innerHTML += `<a class="dropdown-item" href="#">${name}</a>`;
//   // });
// }

/**
 * Returns an HTML string describing a collapsible lease info form.
 * @param {object} lease the lease data to populate the form with
 */
function createLeaseInfoEl(lease) {
  // const leaseType =
  //   lease.grow_area_type.charAt(0).toUpperCase() +
  //   lease.grow_area_type.slice(1);
  const threshold = lease.rainfall_desc.replace('"', '"');
  const LEASE_INFO_EL = `
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
              <label for="lease-${lease.lease_id}-grow-area">Shellfish Growing Unit ID</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-grow-area" value="${lease.sh_id}" readonly>
            </div>
            <div class="mb-3">
              <label for="lease-${lease.lease_id}-grow-area">Shellfish Growing Area Type</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-grow-area" value="${lease.grow_area_type}" readonly>
            </div>
            <div class="mb-3">
              <label for="lease-${lease.lease_id}-grow-area-name">Growing Area Name</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-grow-area-name" value="${lease.sh_name}" readonly>
            </div>
            <div class="mb-3">
              <label for="lease-${lease.lease_id}-rainfall-threshold">Lease Closure Rainfall Threshold (inches)</label>
              <input type="text" class="form-control" id="lease-${lease.lease_id}-rainfall-threshold" value="${lease.rainfall_desc}" readonly>
            </div>

            <small class="form-text text-muted">
              The rainfall threshold is the amount of rainfall in inches within a
              24-hour period that results in a lease being temporarily closed for
              harvest. The Florida Department of Agriculture and Consumer Services determines the threshold.
            </small>
          </form>
        </div>
      </div>
    </div>
  `;
  return LEASE_INFO_EL;
}

/**
 * Builds all of the lease forms based on the data in the global leases array.
 */
function buildLeaseInfoEls() {
  // add lease forms to leases accordion
  const leasesAccordion = document.getElementById("leases-accordion");
  leasesAccordion.innerHTML = "";
  for (let lease of leases) {
    console.log("building lease form", lease);
    lease.rainfall = lease.rainfall_desc.replace(/\"/g, "&quot;");
    leasesAccordion.innerHTML += createLeaseInfoEl(lease);
  }

  // init values and setup event listeners
  for (let lease of leases) {
    initLeaseInfoEl(lease);
  }
}

/**
 * Initializes the form that corresponds to the lease with the given id and data.
 * @param {object} lease the lease data to initialize the form with
 * @param {string} lease.id the id of the lease
 * @param {boolean} ignoreAddingEventListeners whether or not to ignore adding
 *    event listeners as part of the form initialization. This is useful if the
 *    form has already been created, but you are resetting the values.
 */
function initLeaseInfoEl(lease, ignoreAddingEventListeners) {
  const deleteBtn = document.getElementById(`delete-btn-${lease.lease_id}`);

  // add event listeners
  if (!ignoreAddingEventListeners) {
    deleteBtn.addEventListener("click", () => deleteLease(lease.lease_id));
  }
}

/**
 * Adds the given lease to the user's leases.
 * @param {string} leaseId the lease id of the lease to add
 */
async function addLease(leaseId) {
  console.log("adding lease", leaseId);
  try {
    const res = await authorizedFetch("/leases", {
      method: "POST",
      headers: { "Content-Type": "application/json;charset=utf-8" },
      body: JSON.stringify({ lease_id: leaseId }),
    });
    if (res.ok) {
      const lease = await res.json();
      // check if the lease is already added
      const idxOfLease = leases.findIndex((x) => x.lease_id === lease.lease_id);
      if (idxOfLease === -1) {
        leases.push(lease);
      }
      buildLeaseInfoEls();
    } else {
      try {
        const errors = (await res.json()).errors;
        console.log("There was a problem while adding the lease.");
        console.log(errors);
      } catch (parseError) {
        console.log("There was a problem while adding the lease.");
      }
    }
  } catch (error) {
    console.error("Error adding lease:", error);
  }

  clearLeaseSearch();
}

async function deleteLease(leaseId) {
  // console.log(leaseId);
  try {
    const res = await authorizedFetch("/leases", {
      method: "DELETE",
      headers: { "Content-Type": "application/json;charset=utf-8" },
      body: JSON.stringify({ lease_id: leaseId }),
    });
    if (res.ok) {
      // find where the lease is in the local array of leases
      const idxOfLease = leases.findIndex((x) => x.lease_id === leaseId);
      leases.splice(idxOfLease, 1); // and delete it
      buildLeaseInfoEls();
    } else {
      try {
        const errors = (await res.json()).errors;
        console.log("There was a problem while deleting the lease.");
        console.log(errors);
      } catch (parseError) {
        console.log("There was a problem while deleting the lease.");
      }
    }
  } catch (error) {
    console.error("Error deleting lease:", error);
  }
}

/**
 * Searches through leases by the lease id with the text entered by the user.
 */
async function searchLeases() {
  const searchResultsDiv = document.getElementById("lease-search-results");
  const userInput = document.getElementById("lease-search-text-input").value;
  if (userInput === "") {
    clearLeaseSearch();
    return;
  }
  try {
    const res = await authorizedFetch("/searchLeases", {
      method: "POST",
      headers: { "Content-Type": "application/json;charset=utf-8" },
      body: JSON.stringify({ search: userInput }),
    });
    if (res.ok) {
      const returnedLeases = await res.json();
      searchResultsDiv.innerHTML = "";
      if (returnedLeases.length > 0) {
        for (let lease of returnedLeases) {
          searchResultsDiv.innerHTML += `<button class="list-group-item list-group-item-action">${lease}</button>`;
        }
        for (let button of searchResultsDiv.children) {
          button.addEventListener("click", () => addLease(button.textContent));
        }
      } else {
        // show message saying no results were found
        searchResultsDiv.innerHTML =
          '<button type="button" class="list-group-item list-group-item-action">No leases with a similar ID were found.</button>';
      }
      searchResultsDiv.style.display = "flex";
    } else {
      console.log("There was an error while searching for leases.");
      // show an error message
      searchResultsDiv.innerHTML =
        '<button type="button" class="list-group-item list-group-item-action">An error occurred. Please try again.</button>';
      searchResultsDiv.style.display = "flex";
    }
  } catch (error) {
    console.error("Error searching leases:", error);
    searchResultsDiv.innerHTML =
      '<button type="button" class="list-group-item list-group-item-action">An error occurred. Please try again.</button>';
    searchResultsDiv.style.display = "flex";
  }
}

/**
 * Clears the search box and removes all search results from the UI.
 */
function clearLeaseSearch() {
  // clear search input
  document.getElementById("lease-search-text-input").value = "";
  // clear results
  const searchResultsDiv = document.getElementById("lease-search-results");
  searchResultsDiv.innerHTML = "";
  searchResultsDiv.style.display = "none";
}

// function showSearchResultsDiv() {
//   const searchResultsDiv = document.getElementById("lease-search-results");
//   searchResultsDiv.style.display = "flex";
// }
//
// function hideSearchResultsDiv() {
//   const searchResultsDiv = document.getElementById("lease-search-results");
//   searchResultsDiv.style.display = "none";
// }

function searchLeasesOnDelay() {
  if (leaseSearchTimer !== null) {
    clearTimeout(leaseSearchTimer);
  }
  leaseSearchTimer = setTimeout(searchLeases, LEASE_SEARCH_DELAY);
}

async function deleteAccount() {
  try {
    const res = await authorizedFetch("/deleteAccount");
    if (res.ok) {
      window.location.replace("/");
    } else {
      try {
        const errors = (await res.json()).errors;
        console.log("There was a problem while deleting the account.");
        console.log(errors);
      } catch (parseError) {
        console.log("There was a problem while deleting the account.");
      }
    }
  } catch (error) {
    console.error("Error deleting account:", error);
  }
}

/**
 * Displays the UI for a signed in user and initializes the lease forms.
 * @param {firebase.User} user
 */
async function handleSignedInUser(user) {
  // hide signed-out view and show signed-in view
  document.getElementById("user-signed-in").style.display = "block";
  document.getElementById("user-signed-out").style.display = "none";

  // get user's profile information
  profileInfo = await getProfileInfo();
  window.userProfileInfo = profileInfo;
  initNotificationForm({
    authorizedFetch,
    getProfileInfo: () => profileInfo,
    setProfileInfo: (v) => { profileInfo = v; },
    getSavedProfileData: () => savedProfileData,
    setSavedProfileData: (v) => { savedProfileData = v; },
  });

  // setup delete account button
  document
    .getElementById("confirm-account-deletion-btn")
    .addEventListener("click", deleteAccount);

  // setup lease search bar
  document
    .getElementById("lease-search-text-input")
    .addEventListener("input", searchLeasesOnDelay);
  document
    .getElementById("lease-search-btn")
    .addEventListener("click", searchLeases);
  document
    .getElementById("lease-clear-btn")
    .addEventListener("click", clearLeaseSearch);

  // get user's leases
  try {
    const res = await authorizedFetch("/leases");
    if (res.ok) {
      leases = await res.json();
    } else {
      console.log("There was a problem while retrieving the user's leases");
    }
  } catch (error) {
    console.error("Error retrieving user's leases:", error);
  }

  // setup lease forms
  buildLeaseInfoEls();
  await getGeoJsonLeases();
  // console.log(leases_lst);
  // createDropdowns(leases_lst);
}

/**
 * Displays the UI for a signed out user.
 */
function handleSignedOutUser() {
  window.location.replace("/map");
}

(async () => {
  // change UI based on auth state
  onAuthStateChanged(auth, (user) => {
    user ? handleSignedInUser(user) : handleSignedOutUser();
  });
})();
