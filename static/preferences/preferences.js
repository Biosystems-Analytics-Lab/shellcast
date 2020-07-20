'use strict';

const NOTIFICATION_PROB_PREFS = [25, 50, 75];

let profileInfo = {};
let leases = [];

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
  const cancelBtn = profForm.elements['prof-form-cancel-btn'];
  const saveBtn = profForm.elements['prof-form-save-btn'];

  // set values
  emailInput.value = profInfo.email;
  phoneNumberInput.value = maskPhoneNumber(profInfo.phone_number);

  // disable cancel and save buttons
  cancelBtn.disabled = true;
  saveBtn.disabled = true;

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
 * Enables the cancel and save buttons on the profile info form.
 * @param {object} e the change event
 */
function onProfileFormChange(e) {
  const profForm = e.target.form;
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

  // gather data from form
  const phoneNumber = profForm.elements['phone-number'].value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/)[0];
  const newProfileInfo = {
    email: profForm.elements['email-address'].value,
    phone_number: phoneNumber
  };

  // upload data to server and re-init form
  console.log('Uploading data to server', newProfileInfo);
  const res = await authorizedFetch('/userInfo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify(newProfileInfo)
  });
  if (res.ok) {
    // overwrite the client copy of the profile info
    profileInfo = newProfileInfo;
    // reset the form with the new info
    initProfileForm(newProfileInfo, true);
  } else {
    console.log('There was an error while saving the profile changes.');
    // reset the form with the old info
    initProfileForm(profileInfo, true);
  }
}

/**
 * Returns an HTML string describing a collapsible lease info form.
 * @param {object} lease the lease data to populate the form with
 */
function createLeaseInfoEl(lease) {
  const notificationsEnabled = lease.email_pref || lease.text_pref;
  const disabledOrNah = notificationsEnabled ? '' : 'disabled';
  const LEASE_INFO_EL = `
    <div class="card">
      <div class="card-header" id="heading-${lease.id}">
        <h2 class="mb-0">
          <button class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#collapse-${lease.id}" aria-expanded="false" aria-controls="collapse-${lease.id}">
            Lease: ${lease.ncdmf_lease_id}
          </button>
        </h2>
      </div>

      <div id="collapse-${lease.id}" class="collapse" aria-labelledby="heading-${lease.id}" data-parent="#leases-accordion">
        <div class="card-body">
          <form class="needs-validation mb-4" id="form-${lease.id}">
            <div class="mb-3 inline-text-input">
              <label for="lease-${lease.id}-lease-ncdmf-id">Lease ID</label>
              <input type="text" class="form-control" id="lease-${lease.id}-lease-ncdmf-id" value="${lease.ncdmf_lease_id}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-grow-area">Grow Area</label>
              <input type="text" class="form-control" id="lease-${lease.id}-grow-area" value="${lease.grow_area_name}" readonly>
            </div>

            <div class="mb-3">
              <label for="lease-${lease.id}-rainfall-threshold">Rainfall Threshold</label>
              <input type="text" class="form-control" id="lease-${lease.id}-rainfall-threshold" value="${lease.rainfall_thresh_in}" readonly>
            </div>

            <div class="form-check">
              <input class="form-check-input" type="checkbox" name="lease-enable-notifications" id="lease-${lease.id}-enable-notifications">
              <label class="form-check-label" for="lease-${lease.id}-enable-notifications">Enable notifications</label>
            </div>

            <div class="notification-options" id="lease-${lease.id}-notification-options">
              <label>Notification Type</label>
              <div class="form-check">
                <input class="form-check-input" type="checkbox" name="lease-email" id="lease-${lease.id}-email" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-email">Email</label>
              </div>
              <div class="form-check">
                <input class="form-check-input" type="checkbox" name="lease-text" id="lease-${lease.id}-text" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-text">Text</label>
              </div>
              <small class="form-text text-muted">
                Choose whether you want to receive email and/or text notifications for this lease.
              </small>

              <label>Notification Probability</label>
              <div class="form-check">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[0]}" value="${NOTIFICATION_PROB_PREFS[0]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[0]}">${NOTIFICATION_PROB_PREFS[0]}% or higher</label>
              </div>
              <div class="form-check">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[1]}" value="${NOTIFICATION_PROB_PREFS[1]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[1]}">${NOTIFICATION_PROB_PREFS[1]}% or higher</label>
              </div>
              <div class="form-check">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[2]}" value="${NOTIFICATION_PROB_PREFS[2]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[2]}">${NOTIFICATION_PROB_PREFS[2]}% or higher</label>
              </div>
              <small class="form-text text-muted">
                This is the minimum probability that you will be notified at for this lease.  For example, if you choose "50% or higher", then you will be notified whenever your lease has a 50% or higher chance of being closed.
              </small>

            <div style="text-align: right;">
              <button class="btn btn-primary" type="button" name="lease-form-cancel-btn" disabled>Cancel</button>
              <button class="btn btn-primary" type="button" name="lease-form-save-btn" disabled>Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
  return LEASE_INFO_EL;
}

/**
 * Resets the form that's associated with the lease with the given id.
 * @param {string} leaseId the id of the lease associated with the form whose changes are being cancelled
 */
function cancelLeaseFormChanges(leaseId) {
  const originalLeaseData = leases.find((lease) => lease.id === leaseId);
  initLeaseForm(originalLeaseData, true);
}

/**
 * Saves the changes made to the given form and uploads the data to the server.
 * @param {object} leaseForm the form that is being saved
 * @param {string} leaseId the id of the lease whose values are being updated 
 */
async function saveLeaseFormChanges(leaseForm, leaseId) {
  const leaseIdx = leases.findIndex((lease) => lease.id === leaseId);
  const originalLeaseData = leases[leaseIdx];

  // gather data from form inputs
  const emailCheckbox = leaseForm.elements[`lease-email`];
  const textCheckbox = leaseForm.elements[`lease-text`];
  const probRadios = leaseForm.elements[`lease-notification-prob`];
  let selectedProb;
  for (let radio of probRadios) {
    if (radio.checked) {
      selectedProb = Number(radio.value);
    }
  }

  // construct new lease data object
  const newLeaseData = {
    id: originalLeaseData.id,
    ncdmf_lease_id: originalLeaseData.ncdmf_lease_id,
    grow_area_name: originalLeaseData.grow_area_name,
    rainfall_thresh_in: originalLeaseData.rainfall_thresh_in,
    email_pref: emailCheckbox.checked,
    text_pref: textCheckbox.checked,
    prob_pref: selectedProb
  };

  const dataToUpload = {
    id: newLeaseData.id,
    ncdmf_lease_id: newLeaseData.ncdmf_lease_id,
    email_pref: newLeaseData.email_pref,
    text_pref: newLeaseData.text_pref,
    prob_pref: newLeaseData.prob_pref
  };

  // upload data to server and re-init form
  console.log('Uploading data to server', dataToUpload);
  const res = await authorizedFetch('/leases', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify(dataToUpload)
  });
  if (res.ok) {
    // overwrite the client copy of the lease info
    leases[leaseIdx] = newLeaseData;
    // reset the form with the new info
    initLeaseForm(newLeaseData, true);
  } else {
    console.log('There was an error while saving the lease data.');
    // reset the form with the old info
    initLeaseForm(originalLeaseData, true);
  }
}

/**
 * Enables the cancel and save buttons and disables the notification inputs if necessary.
 * @param {object} e the change event
 */
function onLeaseFormChange(e) {
  const leaseForm = e.target.form;
  leaseForm.elements['lease-form-cancel-btn'].disabled = false;
  leaseForm.elements['lease-form-save-btn'].disabled = false;
  // enable/disable notification inputs as appropriate
  enableDisableLeaseNotificationInputs(leaseForm);
}

/**
 * Enables or disables the notification inputs of the given form based on the
 * whether or not the enable notifications checkbox is selected.
 * @param {object} leaseForm the form to enable or disable
 */
function enableDisableLeaseNotificationInputs(leaseForm) {
  const notificationsCheckbox = leaseForm.elements[`lease-enable-notifications`];
  const emailCheckbox = leaseForm.elements[`lease-email`];
  const textCheckbox = leaseForm.elements[`lease-text`];
  const probRadios = leaseForm.elements[`lease-notification-prob`];
  // enable/disable notification inputs appropriately
  const notificationsEnabled = notificationsCheckbox.checked;
  emailCheckbox.disabled = textCheckbox.disabled = !notificationsEnabled;
  for (let radio of probRadios) {
    radio.disabled = !notificationsEnabled;
  }
  if (!notificationsEnabled) {
    emailCheckbox.checked = textCheckbox.checked = false;
  }
}

/**
 * Builds all of the lease forms based on the data in the global leases array.
 */
function buildLeaseForms() {
  // add lease forms to leases accordion
  const leasesAccordion = document.getElementById('leases-accordion');
  leasesAccordion.innerHTML = '';
  for (let lease of leases) {
    leasesAccordion.innerHTML += createLeaseInfoEl(lease);
  }

  // init values and setup event listeners
  for (let lease of leases) {
    initLeaseForm(lease);
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
function initLeaseForm(lease, ignoreAddingEventListeners) {
  const leaseForm = document.forms[`form-${lease.id}`];
  const notificationsCheckbox = leaseForm.elements[`lease-enable-notifications`];
  const emailCheckbox = leaseForm.elements[`lease-email`];
  const textCheckbox = leaseForm.elements[`lease-text`];
  const probRadios = leaseForm.elements[`lease-notification-prob`];
  const cancelBtn = leaseForm.elements[`lease-form-cancel-btn`];
  const saveBtn = leaseForm.elements[`lease-form-save-btn`];
  // set values for checkboxes
  notificationsCheckbox.checked = lease.email_pref || lease.text_pref;
  emailCheckbox.checked = lease.email_pref;
  textCheckbox.checked = lease.text_pref;
  // set values for radio buttons
  for (let radio of probRadios) {
    const value = lease.prob_pref && lease.prob_pref.toString();
    radio.checked = (radio.value === value);
  }

  // disable notification inputs as appropriate
  enableDisableLeaseNotificationInputs(leaseForm);

  // disable cancel and save buttons
  cancelBtn.disabled = true;
  saveBtn.disabled = true;

  // add event listeners
  if (!ignoreAddingEventListeners) {
    leaseForm.addEventListener('change', onLeaseFormChange);
    cancelBtn.addEventListener('click', () => cancelLeaseFormChanges(lease.id));
    saveBtn.addEventListener('click', () => saveLeaseFormChanges(leaseForm, lease.id));
  }
}

/**
 * Adds the given lease to the user's leases.
 * @param {string} leaseId the NCDMF lease id of the lease to add
 */
async function addLease(leaseId) {
  const res = await authorizedFetch('/leases', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify({ncdmf_lease_id: leaseId})
  });
  if (res.ok) {
    const lease = await res.json();
    leases.push(lease);
    buildLeaseForms();
  } else {
    console.log('There was a problem while adding a lease.');
  }

  clearLeaseSearch();
}

/**
 * Searches through leases by the NCDMF lease id with the text entered by the user.
 */
async function searchLeases() {
  const searchResultsDiv = document.getElementById('lease-search-results');
  const userInput = document.getElementById('lease-search-text-input').value;
  const res = await authorizedFetch('/searchLeases', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify({search: userInput})
  });
  if (res.ok) {
    const returnedLeases = await res.json();
    searchResultsDiv.innerHTML = '';
    for (let lease of returnedLeases) {
      searchResultsDiv.innerHTML += `<button type="button" class="list-group-item list-group-item-action" onclick="addLease('${lease}')">${lease}</button>`;
    }
    searchResultsDiv.style.display = 'flex';
  } else {
    console.log('There was an error while searching for leases.');
    // clear results
    const searchResultsDiv = document.getElementById('lease-search-results');
    searchResultsDiv.innerHTML = '';
    searchResultsDiv.style.display = 'none';
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

  // setup lease search bar
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
  buildLeaseForms();
};

/**
 * Displays the UI for a signed out user.
 */
function handleSignedOutUser() {
  document.getElementById('user-signed-in').style.display = 'none';
  document.getElementById('user-signed-out').style.display = 'block';
};

(async () => {
  // change UI based on auth state
  firebase.auth().onAuthStateChanged((user) => {
    user ? handleSignedInUser(user) : handleSignedOutUser();
  });
})();
