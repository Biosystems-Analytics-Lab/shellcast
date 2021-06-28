'use strict';

/* The number of milliseconds between when a user changes the lease search
   text and when an API request is sent for a lease search */
const LEASE_SEARCH_DELAY = 400;

let profileInfo = {};
let leases = [];

// the id of the latest lease search timer
let leaseSearchTimer = null;

/**
 * Retrieves the current user's profile information from the server.
 * @return {object} the user's profile information (email and phone number)
 */
async function getProfileInfo() {
  const res = await authorizedFetch('/userInfo');
  if (res.ok) {
    return await res.json();
  }
  console.log('Problem retrieving user profile information.');
  console.log(res);
  return null;
}

/**
 * Initializes the profile form with the given profile information.
 * @param {object} profInfo the profile information to initialize the form with
 * @param {boolean} ignoreAddingEventListeners whether or not to ignore adding
 *    event listeners as part of the form initialization. This is useful if the
 *    form has already been created, but you are resetting the values.
 */
function initProfileForm(profInfo, ignoreAddingEventListeners) {
  // setup profile information form
  const profForm = document.forms['profile-information-form'];
  const emailInput = profForm.elements['email-address'];
  const phoneNumberInput = profForm.elements['phone-number'];
  const serviceProviderInput = profForm.elements['service-provider'];
  const noNotificationsCheckbox = profForm.elements['no-notifications'];
  const emailCheckbox = profForm.elements['email-pref'];
  const textCheckbox = profForm.elements['text-pref'];
  const textCheckboxLabel = textCheckbox.labels[0];
  const probRadios = profForm.elements['notification-prob'];
  const cancelBtn = profForm.elements['prof-form-cancel-btn'];
  const saveBtn = profForm.elements['prof-form-save-btn'];

  // set values for inputs
  emailInput.value = profInfo.email;
  phoneNumberInput.value = maskPhoneNumber(profInfo.phone_number);
  serviceProviderInput.value = profInfo.service_provider_id;
  noNotificationsCheckbox.checked = !profInfo.email_pref && !profInfo.text_pref;
  emailCheckbox.checked = profInfo.email_pref;
  // don't allow text notifications to be enabled unless user entered a phone number and service provider
  if (profInfo.phone_number === undefined || profInfo.service_provider_id === undefined) {
    textCheckboxLabel.innerHTML = 'Text (You must enter a phone number and service provider to enable text notitifications.)';
    textCheckbox.disabled = true;
    textCheckbox.checked = false;
  } else {
    textCheckboxLabel.innerHTML = 'Text';
    textCheckbox.disabled = false;
    textCheckbox.checked = profInfo.text_pref;
  }
  // set values for radio buttons
  for (let radio of probRadios) {
    const value = profInfo.prob_pref && profInfo.prob_pref.toString();
    radio.checked = (radio.value === value);
    // disable the radios if "No notifications" is checked
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // disable cancel and save buttons
  cancelBtn.disabled = true;
  saveBtn.disabled = true;

  // show example notification
  document.getElementById('example-notification').innerHTML = generateExampleNotification(noNotificationsCheckbox.checked, profInfo.prob_pref);

  // add event listeners
  if (!ignoreAddingEventListeners) {
    profForm.addEventListener('input', onProfileFormChange);
    cancelBtn.addEventListener('click', cancelProfileFormChanges);
    saveBtn.addEventListener('click', saveProfileFormChanges);
    phoneNumberInput.addEventListener('input', (e) => (phoneNumberInput.value = maskPhoneNumber(e.target.value)));
  }
}

/**
 * Formats a given string into a phone number (pulls out all digits and formats them).
 * @param {string} phoneNumber the string to format
 */
function maskPhoneNumber(phoneNumber='') {
  // get the digits from the input
  const digits = phoneNumber.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
  
  // format the digits based on how many there are
  const numDigitsEntered = digits[0].length;
  if (numDigitsEntered > 0) {
    if (numDigitsEntered > 3) {
      if (numDigitsEntered > 6) {
        return `(${digits[1]}) ${digits[2]}-${digits[3]}`;
      }
      return `(${digits[1]}) ${digits[2]}`;
    }
    return `(${digits[1]}`;
  }
  return '';
}

/**
 * 
 * @param {boolean} noNotifications whether or not the user enabled notifications
 * @param {number} selectedProb the user's selected probabity preference
 */
function generateExampleNotification(noNotifications, selectedProb) {
  if (noNotifications) {
    return '<p>-- You will not receive any notifications. --</p>';
  }
  return `<pre>One or more of your leases has a high percent chance of closing today, tomorrow or in 2 days.\nVisit <a href="https://ncsu-shellcast.appspot.com/">go.ncsu.edu/shellcast</a> for details.</pre>`;
}

/**
 * Enables the cancel and save buttons on the profile info form.
 * @param {object} e the change event
 */
function onProfileFormChange(e) {
  const profForm = e.target.form;
  const phoneNumberInput = profForm.elements['phone-number'];
  const serviceProviderInput = profForm.elements['service-provider'];
  const noNotificationsCheckbox = profForm.elements['no-notifications'];
  const emailCheckbox = profForm.elements['email-pref'];
  const textCheckbox = profForm.elements['text-pref'];
  const textCheckboxLabel = textCheckbox.labels[0];
  const probRadios = profForm.elements['notification-prob'];

  // noNotifications/email/text logic
  if (e.target === noNotificationsCheckbox) {
    noNotificationsCheckbox.checked = true;
    emailCheckbox.checked = textCheckbox.checked = false;
  } else if (e.target === emailCheckbox || e.target === textCheckbox) {
    noNotificationsCheckbox.checked = !emailCheckbox.checked && !textCheckbox.checked;
  }

  // don't allow text notifications to be enabled unless user entered a phone number and service provider
  const noPhoneNumber = phoneNumberInput.value === undefined || phoneNumberInput.value === '';
  const noServiceProvider = serviceProviderInput.value === undefined || serviceProviderInput.value === '';
  if (noPhoneNumber || noServiceProvider) {
    textCheckboxLabel.innerHTML = 'Text (You must enter a phone number and service provider to enable text notitifications.)';
    textCheckbox.disabled = true;
    textCheckbox.checked = false;
  } else {
    textCheckboxLabel.innerHTML = 'Text';
    textCheckbox.disabled = false;
  }

  // enable/disable prob inputs as appropriate
  for (let radio of probRadios) {
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // show example notification
  let selectedProb;
  for (let radio of probRadios) {
    if (radio.checked) {
      selectedProb = Number(radio.value);
    }
  }
  console.log(selectedProb);
  document.getElementById('example-notification').innerHTML = generateExampleNotification(noNotificationsCheckbox.checked, selectedProb);

  // enable save and cancel buttons
  profForm.elements['prof-form-cancel-btn'].disabled = false;
  profForm.elements['prof-form-save-btn'].disabled = false;
}

/**
 * Resets the form that's associated with the lease with the given id.
 */
function cancelProfileFormChanges() {
  initProfileForm(profileInfo, true);
}

/**
 * Saves the changes made to the user's profile info and uploads the data to the server.
 */
async function saveProfileFormChanges() {
  const profForm = document.forms['profile-information-form'];
  const helpText = document.getElementById('profile-form-help-text');

  // gather data from form
  const email = profForm.elements['email-address'].value;
  const phoneNumber = profForm.elements['phone-number'].value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/)[0];
  const serviceProviderId = profForm.elements['service-provider'].value;
  const emailPref = profForm.elements['email-pref'].checked;
  const textPref = profForm.elements['text-pref'].checked;
  const probRadios = profForm.elements['notification-prob'];
  let selectedProb;
  for (let radio of probRadios) {
    if (radio.checked) {
      selectedProb = Number(radio.value);
    }
  }

  const newProfileInfo = {
    email: email,
    phone_number: phoneNumber,
    service_provider_id: serviceProviderId,
    email_pref: emailPref,
    text_pref: textPref,
    prob_pref: selectedProb
  };

  // upload data to server and re-init form
  const res = await authorizedFetch('/userInfo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify(newProfileInfo)
  });
  if (res.ok) {
    // overwrite the client copy of the profile info
    profileInfo = await res.json();
    helpText.style.color = 'green';
    helpText.innerHTML = 'Changes saved successfully!';
  } else {
    const json = await res.json();
    helpText.style.color = 'red';
    helpText.innerHTML = json.errors[0];
  }
  initProfileForm(profileInfo, true);
}

/**
 * Returns an HTML string describing a collapsible lease info form.
 * @param {object} lease the lease data to populate the form with
 */
function createLeaseInfoEl(lease) {
  const LEASE_INFO_EL = `
    <div class="card">
      <div class="card-header" id="heading-${lease.id}">
        <h2 class="mb-0 d-flex">
          <button class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#collapse-${lease.id}" aria-expanded="false" aria-controls="collapse-${lease.id}">
            Lease: ${lease.ncdmf_lease_id}
          </button>
          <div>
            <button class="btn btn-danger" type="button" id="delete-btn-${lease.id}">Delete</button>
          </div>
        </h2>
      </div>

      <div id="collapse-${lease.id}" class="collapse" aria-labelledby="heading-${lease.id}" data-parent="#leases-accordion">
        <div class="card-body">
          <form class="needs-validation mb-4" id="form-${lease.id}">
            <div class="mb-3 inline-text-input">
              <label for="lease-${lease.id}-lease-ncdmf-id">Lease ID</label>
              <input type="text" class="form-control" id="lease-${lease.id}-lease-ncdmf-id" value="${lease.ncdmf_lease_id}" name="lease-ncdmf-id" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-grow-area">NC Division of Marine Fisheries Shellfish Growing Area</label>
              <input type="text" class="form-control" id="lease-${lease.id}-grow-area" value="${lease.grow_area_name}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-grow-area-desc">Growing Area Description</label>
              <input type="text" class="form-control" id="lease-${lease.id}-grow-area-desc" value="${lease.grow_area_desc}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-grow-unit">NC Division of Marine Fisheries Shellfish Growing Unit</label>
              <input type="text" class="form-control" id="lease-${lease.id}-grow-unit" value="${lease.cmu_name}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-rainfall-threshold">Lease Closure Rainfall Threshold (inches)</label>
              <input type="text" class="form-control" id="lease-${lease.id}-rainfall-threshold" value="${lease.rainfall_thresh_in}" readonly>
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
  return LEASE_INFO_EL;
}

/**
 * Builds all of the lease forms based on the data in the global leases array.
 */
function buildLeaseInfoEls() {
  // add lease forms to leases accordion
  const leasesAccordion = document.getElementById('leases-accordion');
  leasesAccordion.innerHTML = '';
  for (let lease of leases) {
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
  const deleteBtn = document.getElementById(`delete-btn-${lease.id}`);

  // add event listeners
  if (!ignoreAddingEventListeners) {
    deleteBtn.addEventListener('click', () => deleteLease(lease.id));
  }
}

/**
 * Adds the given lease to the user's leases.
 * @param {string} leaseId the NCDMF lease id of the lease to add
 */
async function addLease(leaseNCDMFId) {
  const res = await authorizedFetch('/leases', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify({ncdmf_lease_id: leaseNCDMFId})
  });
  if (res.ok) {
    const lease = await res.json();
    // check if the lease is already added
    const idxOfLease = leases.findIndex((x) => x.ncdmf_lease_id === lease.ncdmf_lease_id);
    if (idxOfLease === -1) {
      leases.push(lease);
    }
    buildLeaseInfoEls();
  } else {
    const errors = (await res.json()).errors;
    console.log('There was a problem while adding the lease.');
    console.log(errors);
  }

  clearLeaseSearch();
}

async function deleteLease(leaseId) {
  const res = await authorizedFetch('/leases', {
    method: 'DELETE',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify({lease_id: leaseId})
  });
  if (res.ok) {
    // find where the lease is in the local array of leases
    const idxOfLease = leases.findIndex((x) => x.id === leaseId);
    leases.splice(idxOfLease, 1); // and delete it
    buildLeaseInfoEls();
  } else {
    const errors = (await res.json()).errors;
    console.log('There was a problem while deleting the lease.');
    console.log(errors);
  }
}

/**
 * Searches through leases by the NCDMF lease id with the text entered by the user.
 */
async function searchLeases() {
  const searchResultsDiv = document.getElementById('lease-search-results');
  const userInput = document.getElementById('lease-search-text-input').value;
  if (userInput === '') {
    clearLeaseSearch();
    return;
  }
  const res = await authorizedFetch('/searchLeases', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify({search: userInput})
  });
  if (res.ok) {
    const returnedLeases = await res.json();
    searchResultsDiv.innerHTML = '';
    if (returnedLeases.length > 0) {
      for (let lease of returnedLeases) {
        searchResultsDiv.innerHTML += `<button type="button" class="list-group-item list-group-item-action" onclick="addLease('${lease}')">${lease}</button>`;
      }
    } else {
      // show message saying no results were found
      searchResultsDiv.innerHTML = '<button type="button" class="list-group-item list-group-item-action">No leases with a similar ID were found.</button>';
    }
    searchResultsDiv.style.display = 'flex';
  } else {
    console.log('There was an error while searching for leases.');
    // show error message
    const searchResultsDiv = document.getElementById('lease-search-results');
    searchResultsDiv.innerHTML = '<button type="button" class="list-group-item list-group-item-action">An error occurred. Please try again.</button>';
    searchResultsDiv.style.display = 'flex';
  }
}

/**
 * Clears the search box and removes all search results from the UI.
 */
function clearLeaseSearch() {
  // clear search input
  document.getElementById('lease-search-text-input').value = '';
  // clear results
  const searchResultsDiv = document.getElementById('lease-search-results');
  searchResultsDiv.innerHTML = '';
  searchResultsDiv.style.display = 'none';
}

function showSearchResultsDiv() {
  const searchResultsDiv = document.getElementById('lease-search-results');
  searchResultsDiv.style.display = 'flex';
}

function hideSearchResultsDiv() {
  const searchResultsDiv = document.getElementById('lease-search-results');
  searchResultsDiv.style.display = 'none';
}

function searchLeasesOnDelay() {
  if (leaseSearchTimer !== null) {
    clearTimeout(leaseSearchTimer);
  }
  leaseSearchTimer = setTimeout(searchLeases, LEASE_SEARCH_DELAY);
}

async function deleteAccount() {
  const res = await authorizedFetch('/deleteAccount');
  if (res.ok) {
    window.location.replace('/');
  } else {
    const errors = (await res.json()).errors;
    console.log('There was a problem while deleting the account.');
    console.log(errors);
  }
}

/**
 * Displays the UI for a signed in user and initializes the lease forms.
 * @param {firebase.User} user
 */
async function handleSignedInUser(user) {
  // hide signed-out view and show signed-in view
  document.getElementById('user-signed-in').style.display = 'block';
  document.getElementById('user-signed-out').style.display = 'none';

  // get user's profile information
  profileInfo = await getProfileInfo();
  initProfileForm(profileInfo);

  // setup delete account button
  document.getElementById('confirm-account-deletion-btn').addEventListener('click', deleteAccount);

  // setup lease search bar
  document.getElementById('lease-search-text-input').addEventListener('input', searchLeasesOnDelay);
  document.getElementById('lease-search-btn').addEventListener('click', searchLeases);
  document.getElementById('lease-clear-btn').addEventListener('click', clearLeaseSearch);

  // get user's leases
  const res = await authorizedFetch('/leases');
  if (res.ok) {
    leases = await res.json();
  } else {
    console.log('There was a problem while retrieving the user\'s leases');
  }

  // setup lease forms
  buildLeaseInfoEls();
};

/**
 * Displays the UI for a signed out user.
 */
function handleSignedOutUser() {
  window.location.replace('/');
};

(async () => {
  // change UI based on auth state
  firebase.auth().onAuthStateChanged((user) => {
    user ? handleSignedInUser(user) : handleSignedOutUser();
  });
})();
