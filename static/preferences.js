'use strict';

const NOTIFICATION_WINDOW_PREFS = [1, 2, 3];
const NOTIFICATION_PROB_PREFS = [60, 70, 80, 90];

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
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="checkbox" name="lease-email" id="lease-${lease.id}-email" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-email">Email</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="checkbox" name="lease-text" id="lease-${lease.id}-text" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-text">Text</label>
              </div>
              <small class="form-text text-muted notification-window-help">
                Choose whether you want to receive email and/or text notifications for this lease.
              </small>

              <label>Notification Probability</label>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[0]}" value="${NOTIFICATION_PROB_PREFS[0]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[0]}">${NOTIFICATION_PROB_PREFS[0]} %</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[1]}" value="${NOTIFICATION_PROB_PREFS[1]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[1]}">${NOTIFICATION_PROB_PREFS[1]} %</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[2]}" value="${NOTIFICATION_PROB_PREFS[2]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[2]}">${NOTIFICATION_PROB_PREFS[2]} %</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-prob" id="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[3]}" value="${NOTIFICATION_PROB_PREFS[3]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-prob-${NOTIFICATION_PROB_PREFS[3]}">${NOTIFICATION_PROB_PREFS[3]} %</label>
              </div>
              <small class="form-text text-muted notification-window-help">
                The minimum probability that you want to be notified at for this lease.
              </small>

              <label>Notification Window</label>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-window" id="lease-${lease.id}-notification-window-${NOTIFICATION_WINDOW_PREFS[0]}" value="${NOTIFICATION_WINDOW_PREFS[0]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-window-${NOTIFICATION_WINDOW_PREFS[0]}">${NOTIFICATION_WINDOW_PREFS[0]}-day</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-window" id="lease-${lease.id}-notification-window-${NOTIFICATION_WINDOW_PREFS[1]}" value="${NOTIFICATION_WINDOW_PREFS[1]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-window-${NOTIFICATION_WINDOW_PREFS[1]}">${NOTIFICATION_WINDOW_PREFS[1]}-day</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="lease-notification-window" id="lease-${lease.id}-notification-window-${NOTIFICATION_WINDOW_PREFS[2]}" value="${NOTIFICATION_WINDOW_PREFS[2]}" ${disabledOrNah}>
                <label class="form-check-label" for="lease-${lease.id}-notification-window-${NOTIFICATION_WINDOW_PREFS[2]}">${NOTIFICATION_WINDOW_PREFS[2]}-day</label>
              </div>
              <small class="form-text text-muted notification-window-help">
                The period of time over which a closure probability is calculated for this lease.
              </small>
            </div>

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
  const windowRadios = leaseForm.elements[`lease-notification-window`];
  let selectedProb;
  for (let radio of probRadios) {
    if (radio.checked) {
      selectedProb = Number(radio.value);
    }
  }
  let selectedWindow;
  for (let radio of windowRadios) {
    if (radio.checked) {
      selectedWindow = Number(radio.value);
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
    window_pref: selectedWindow,
    prob_pref: selectedProb
  };

  // upload data to server and re-init form
  console.log('TODO upload data to server', newLeaseData);
  leases[leaseIdx] = newLeaseData;
  initLeaseForm(newLeaseData, true);
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
  const windowRadios = leaseForm.elements[`lease-notification-window`];
  // enable/disable notification inputs appropriately
  const notificationsEnabled = notificationsCheckbox.checked;
  emailCheckbox.disabled = textCheckbox.disabled = !notificationsEnabled;
  for (let radio of probRadios) {
    radio.disabled = !notificationsEnabled;
  }
  for (let radio of windowRadios) {
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
  const windowRadios = leaseForm.elements[`lease-notification-window`];
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
  for (let radio of windowRadios) {
    const value = lease.window_pref && lease.window_pref.toString();
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
 * Displays the UI for a signed in user and initializes the lease forms.
 * @param {firebase.User} user
 */
async function handleSignedInUser(user) {
  document.getElementById('user-signed-in').style.display = 'block';
  document.getElementById('user-signed-out').style.display = 'none';

  // get user's profile information
  profileInfo = await getProfileInfo();
  initProfileForm(profileInfo);

  // get user's leases
  console.log('TODO get user\'s leases from server');
  leases = [
    {id: 0, ncdmf_lease_id: '4-C-89', grow_area_name: 'A03', rainfall_thresh_in: 1.5, email_pref: false, text_pref: false, window_pref: undefined, prob_pref: undefined},
    {id: 1, ncdmf_lease_id: '819401', grow_area_name: 'B05', rainfall_thresh_in: 2.5, email_pref: true, text_pref: false, window_pref: 2, prob_pref: 75},
    {id: 2, ncdmf_lease_id: '82-389B', grow_area_name: 'C11', rainfall_thresh_in: 3.5, email_pref: false, text_pref: true, window_pref: 3, prob_pref: 90},
    {id: 3, ncdmf_lease_id: '123456', grow_area_name: 'D05', rainfall_thresh_in: 4.5, email_pref: true, text_pref: true, window_pref: 2, prob_pref: 90},
  ];

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
