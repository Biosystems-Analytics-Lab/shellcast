"use strict";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";
import { auth, authorizedFetch } from "../common/common.js";

// ============================================================================
// CONSTANTS
// ============================================================================
const LEASE_SEARCH_DELAY = 400;

// ============================================================================
// GLOBAL STATE
// ============================================================================
let profileInfo = {};
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
  const res = await authorizedFetch("/userInfo");
  if (res.ok) {
    return await res.json();
  }
  console.log("Problem retrieving user profile information.");
  return null;
}

/**
 * Initializes the profile form with the given profile information.
 * @param {object} profInfo the profile information to initialize the form with
 * @param {boolean} ignoreAddingEventListeners whether or not to ignore adding
 *    event listeners as part of the form initialization
 */
function initProfileForm(profInfo, ignoreAddingEventListeners) {
  const profForm = document.forms["profile-information-form"];
  const emailInput = profForm.elements["email-address"];
  const phoneNumberInput = profForm.elements["phone-number"];
  const noNotificationsCheckbox = profForm.elements["no-notifications"];
  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const probRadios = profForm.elements["notification-prob"];
  const cancelBtn = profForm.elements["prof-form-cancel-btn"];
  const saveBtn = profForm.elements["prof-form-save-btn"];

  // Set form values
  emailInput.value = profInfo.email;
  phoneNumberInput.value = maskPhoneNumber(profInfo.phone_number);
  emailCheckbox.checked = profInfo.email_pref;
  textCheckbox.checked = profInfo.text_pref;

  // Set "no notifications" based on email and text preferences
  // If neither email nor text is enabled, check "no notifications"
  noNotificationsCheckbox.checked = !profInfo.email_pref && !profInfo.text_pref;

  // Set consent checkboxes based on preferences (for initial load)
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  if (emailConsentCheckbox) {
    emailConsentCheckbox.checked = profInfo.email_pref;
  }
  if (textConsentCheckbox) {
    textConsentCheckbox.checked = profInfo.text_pref;
  }

  // Initially expand accordions if user has preferences enabled
  // (but don't auto-collapse them later - let user control with OK button)
  if (profInfo.email_pref || profInfo.text_pref) {
    updateAccordionVisibility(profInfo.email_pref, profInfo.text_pref);
  }

  // Initialize original states for accordion revert functionality
  // Try to load from localStorage first, fallback to server data
  const cachedEmailState = localStorage.getItem("shellcast_email_preferences");
  const cachedTextState = localStorage.getItem("shellcast_text_preferences");

  originalEmailState = cachedEmailState
    ? JSON.parse(cachedEmailState)
    : {
        email: profInfo.email,
        email_pref: profInfo.email_pref,
        email_consent: profInfo.email_pref,
      };

  originalTextState = cachedTextState
    ? JSON.parse(cachedTextState)
    : {
        phone_number: profInfo.phone_number,
        text_pref: profInfo.text_pref,
        text_consent: profInfo.text_pref,
      };

  // Set probability preference
  for (let radio of probRadios) {
    const value = profInfo.prob_pref && profInfo.prob_pref.toString();
    radio.checked = radio.value === value;
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // Reset button states
  cancelBtn.disabled = true;
  saveBtn.disabled = true;

  // Add event listeners
  if (!ignoreAddingEventListeners) {
    profForm.addEventListener("input", onProfileFormChange);
    cancelBtn.addEventListener("click", cancelProfileFormChanges);
    saveBtn.addEventListener("click", saveProfileFormChanges);
    phoneNumberInput.addEventListener(
      "input",
      (e) => (phoneNumberInput.value = maskPhoneNumber(e.target.value)),
    );

    // Add consent checkbox validation
    const emailConsentCheckbox = profForm.elements["email-consent"];
    const textConsentCheckbox = profForm.elements["text-consent"];
    if (emailConsentCheckbox) {
      emailConsentCheckbox.addEventListener("change", validateForm);
    }
    if (textConsentCheckbox) {
      textConsentCheckbox.addEventListener("change", validateForm);
    }

    setupAccordionTabs();
    setupAccordionButtons();
  }
}

/**
 * Handles form input changes and updates UI accordingly.
 * @param {object} e the change event
 */
function onProfileFormChange(e) {
  const profForm = e.target.form;
  const noNotificationsCheckbox = profForm.elements["no-notifications"];
  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  const probRadios = profForm.elements["notification-prob"];

  // Clear any existing status message when form changes
  const helpText = document.getElementById("profile-form-help-text");
  if (helpText) {
    helpText.innerHTML = "";
    helpText.style.color = "";
  }

  // Prevent text checkbox from being checked during system update
  if (e.target === textCheckbox && textCheckbox.checked) {
    textCheckbox.checked = false;
    return;
  }

  // Prevent email consent checkbox from being checked during system update
  if (e.target === emailConsentCheckbox && emailConsentCheckbox.checked) {
    emailConsentCheckbox.checked = false;
    return;
  }

  // Handle consent withdrawal logic (highest priority)
  if (e.target === emailConsentCheckbox) {
    // If email consent is unchecked, uncheck email preference and clear email
    if (!emailConsentCheckbox.checked) {
      emailCheckbox.checked = false;
      profForm.elements["email-address"].value = "";
    }
  } else if (e.target === textConsentCheckbox) {
    // If text consent is unchecked, uncheck text preference and clear phone
    if (!textConsentCheckbox.checked) {
      textCheckbox.checked = false;
      profForm.elements["phone-number"].value = "";
    }
  }

  // Handle preference checkbox logic (lower priority)
  // Note: We don't auto-check consent - user must do this deliberately

  // Handle "no notifications" logic
  if (e.target === noNotificationsCheckbox) {
    // If "no notifications" is checked, uncheck email and text preferences
    if (noNotificationsCheckbox.checked) {
      emailCheckbox.checked = textCheckbox.checked = false;
      // Also uncheck consent boxes but don't clear data
      if (emailConsentCheckbox) {
        emailConsentCheckbox.checked = false;
      }
      if (textConsentCheckbox) {
        textConsentCheckbox.checked = false;
      }
    }
  } else if (e.target === emailCheckbox || e.target === textCheckbox) {
    // If email or text is checked, uncheck "no notifications"
    if (emailCheckbox.checked || textCheckbox.checked) {
      noNotificationsCheckbox.checked = false;
    } else {
      // If neither email nor text is checked, check "no notifications"
      noNotificationsCheckbox.checked = true;
    }
  }

  // Handle email checkbox logic - set user's email when checked
  if (e.target === emailCheckbox && emailCheckbox.checked) {
    const emailInput = profForm.elements["email-address"];
    console.log(
      "Email checkbox checked, current email value:",
      emailInput.value,
    );
    console.log("User profile info:", window.userProfileInfo);

    // Set email if we have user profile data and either:
    // 1. Email field is empty, OR
    // 2. Email field contains placeholder-like value
    const currentEmail = emailInput.value.trim();
    const isPlaceholderOrEmpty =
      !currentEmail ||
      currentEmail === "you@example.com" ||
      currentEmail === "You@example.com" ||
      currentEmail.includes("example.com");

    if (
      isPlaceholderOrEmpty &&
      window.userProfileInfo &&
      window.userProfileInfo.email
    ) {
      console.log("Setting email to:", window.userProfileInfo.email);
      emailInput.value = window.userProfileInfo.email;
    }
  }

  // Update accordion visibility
  if (e.target === noNotificationsCheckbox && noNotificationsCheckbox.checked) {
    // Auto-collapse when "no notifications" is checked
    updateAccordionVisibility(false, false);
  } else if (e.target === emailCheckbox && emailCheckbox.checked) {
    // Open email accordion when email preference is checked
    updateAccordionVisibility(true, textCheckbox.checked);
  } else if (e.target === textCheckbox && textCheckbox.checked) {
    // Open text accordion when text preference is checked
    updateAccordionVisibility(emailCheckbox.checked, true);
  }

  // Update probability radio button states
  for (let radio of probRadios) {
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // Validate form and update button states
  validateForm();
  profForm.elements["prof-form-cancel-btn"].disabled = false;
}

// Setup expand/collapse buttons only
function setupAccordionButtons() {
  setupExpandCollapseButtons();
}

/**
 * Sets up expand/collapse buttons for accordions
 */
function setupExpandCollapseButtons() {
  const emailExpandBtn = document.getElementById("email-expand-btn");
  const emailCollapseBtn = document.getElementById("email-collapse-btn");
  const textExpandBtn = document.getElementById("text-expand-btn");
  const textCollapseBtn = document.getElementById("text-collapse-btn");

  if (emailExpandBtn) {
    emailExpandBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent accordion header click
      expandEmailAccordion();
    });
  }

  if (emailCollapseBtn) {
    emailCollapseBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent accordion header click
      collapseEmailAccordion();
    });
  }

  if (textExpandBtn) {
    textExpandBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent accordion header click
      expandTextAccordion();
    });
  }

  if (textCollapseBtn) {
    textCollapseBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent accordion header click
      collapseTextAccordion();
    });
  }
}

/**
 * Expands the email accordion
 */
function expandEmailAccordion() {
  const emailAccordion = document.getElementById("email-accordion");
  const emailExpandBtn = document.getElementById("email-expand-btn");
  const emailCollapseBtn = document.getElementById("email-collapse-btn");

  if (emailAccordion) {
    emailAccordion.classList.add("expanded");
  }

  if (emailExpandBtn) emailExpandBtn.style.display = "none";
  if (emailCollapseBtn) emailCollapseBtn.style.display = "inline-flex";
}

/**
 * Collapses the email accordion
 */
function collapseEmailAccordion() {
  const emailAccordion = document.getElementById("email-accordion");
  const emailExpandBtn = document.getElementById("email-expand-btn");
  const emailCollapseBtn = document.getElementById("email-collapse-btn");

  if (emailAccordion) {
    emailAccordion.classList.remove("expanded");
  }

  if (emailExpandBtn) emailExpandBtn.style.display = "inline-flex";
  if (emailCollapseBtn) emailCollapseBtn.style.display = "none";
}

/**
 * Expands the text accordion
 */
function expandTextAccordion() {
  const textAccordion = document.getElementById("text-accordion");
  const textExpandBtn = document.getElementById("text-expand-btn");
  const textCollapseBtn = document.getElementById("text-collapse-btn");

  if (textAccordion) {
    textAccordion.classList.add("expanded");
  }

  if (textExpandBtn) textExpandBtn.style.display = "none";
  if (textCollapseBtn) textCollapseBtn.style.display = "inline-flex";
}

/**
 * Collapses the text accordion
 */
function collapseTextAccordion() {
  const textAccordion = document.getElementById("text-accordion");
  const textExpandBtn = document.getElementById("text-expand-btn");
  const textCollapseBtn = document.getElementById("text-collapse-btn");

  if (textAccordion) {
    textAccordion.classList.remove("expanded");
  }

  if (textExpandBtn) textExpandBtn.style.display = "inline-flex";
  if (textCollapseBtn) textCollapseBtn.style.display = "none";
}

// Store original accordion states for reverting changes
let originalEmailState = null;
let originalTextState = null;

// Track if changes have been made
let emailChangesMade = false;
let textChangesMade = false;

/**
 * Resets the profile form to its original state.
 */
function cancelProfileFormChanges() {
  initProfileForm(profileInfo, true);
}

/**
 * Saves the profile form changes to the server.
 */
async function saveProfileFormChanges() {
  const profForm = document.forms["profile-information-form"];
  const helpText = document.getElementById("profile-form-help-text");

  if (!profForm || !helpText) {
    console.error("Required form elements not found!");
    return;
  }

  // Validate form before saving
  if (!validateForm()) {
    console.log("Form validation failed - cannot save");
    return;
  }

  // Gather form data
  const email = profForm.elements["email-address"].value;
  const phoneNumberRaw = profForm.elements["phone-number"].value.replace(
    /\D/g,
    "",
  );
  const phoneNumberMatch = phoneNumberRaw.match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
  const phoneNumber = phoneNumberMatch ? phoneNumberMatch[0] : "";
  const emailPref = profForm.elements["email-pref"].checked;
  const textPref = profForm.elements["text-pref"].checked;
  const emailConsentChecked = profForm.elements["email-consent"]
    ? profForm.elements["email-consent"].checked
    : false;
  const textConsentChecked = profForm.elements["text-consent"]
    ? profForm.elements["text-consent"].checked
    : false;
  const probRadios = profForm.elements["notification-prob"];

  let selectedProb;
  for (let radio of probRadios) {
    if (radio.checked) {
      selectedProb = Number(radio.value);
    }
  }

  // Privacy-first approach: Remove email/phone if preference is unchecked
  const newProfileInfo = {
    email: emailPref ? email : null,
    phone_number: textPref ? phoneNumber : null,
    service_provider_id: null, // NC doesn't have service provider field
    email_pref: emailPref,
    text_pref: textPref,
    prob_pref: selectedProb,
    email_consent: emailConsentChecked,
    text_consent: textConsentChecked,
  };

  // Send data to server
  try {
    const res = await authorizedFetch("/userInfo", {
      method: "POST",
      headers: { "Content-Type": "application/json;charset=utf-8" },
      body: JSON.stringify(newProfileInfo),
    });

    if (res.ok) {
      profileInfo = await res.json();
      helpText.style.color = "green";

      // Inform user about data removal if preference was unchecked
      let message = "Changes saved successfully!";
      if (!emailPref && profileInfo.email) {
        message += " Your email address has been removed from our system.";
      }
      if (!textPref && profileInfo.phone_number) {
        message += " Your phone number has been removed from our system.";
      }

      helpText.innerHTML = message;
    } else {
      const contentType = res.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        const json = await res.json();
        helpText.style.color = "red";
        helpText.innerHTML = json.errors[0];
      } else {
        helpText.style.color = "red";
        helpText.innerHTML =
          "Server error occurred. Please refresh the page and try again.";
      }
    }
    initProfileForm(profileInfo, true);
  } catch (error) {
    console.error("Error during save:", error);
    helpText.style.color = "red";
    helpText.innerHTML = "An error occurred while saving. Please try again.";
  }
}

// ============================================================================
// VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validates email format
 * @param {string} email the email to validate
 * @return {boolean} whether the email is valid
 */
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validates phone number format (10 digits)
 * @param {string} phoneNumber the phone number to validate (digits only)
 * @return {boolean} whether the phone number is valid
 */
function validatePhoneNumber(phoneNumber) {
  return (
    phoneNumber && phoneNumber.length === 10 && /^\d{10}$/.test(phoneNumber)
  );
}

/**
 * Validates the entire form and updates UI accordingly
 * @return {boolean} whether the form is valid
 */
function validateForm() {
  const profForm = document.forms["profile-information-form"];
  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const emailInput = profForm.elements["email-address"];
  const phoneInput = profForm.elements["phone-number"];
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  const saveBtn = profForm.elements["prof-form-save-btn"];

  console.log("Validating form...");
  console.log("Email checkbox checked:", emailCheckbox.checked);
  console.log(
    "Email consent checked:",
    emailConsentCheckbox ? emailConsentCheckbox.checked : "N/A",
  );
  console.log("Text checkbox checked:", textCheckbox.checked);
  console.log(
    "Text consent checked:",
    textConsentCheckbox ? textConsentCheckbox.checked : "N/A",
  );

  let isValid = true;

  // Validate email if email preference is checked (preference-driven validation)
  if (emailCheckbox.checked) {
    const email = emailInput.value.trim();
    if (!email || !validateEmail(email)) {
      emailInput.classList.add("is-invalid");
      isValid = false;
    } else {
      emailInput.classList.remove("is-invalid");
    }
  } else {
    emailInput.classList.remove("is-invalid");
  }

  // Validate phone number if text preference is checked (preference-driven validation)
  if (textCheckbox.checked) {
    const phoneNumber = phoneInput.value.replace(/\D/g, "");
    if (!phoneNumber || !validatePhoneNumber(phoneNumber)) {
      phoneInput.classList.add("is-invalid");
      isValid = false;
    } else {
      phoneInput.classList.remove("is-invalid");
    }
  } else {
    phoneInput.classList.remove("is-invalid");
  }

  saveBtn.disabled = !isValid;
  return isValid;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Formats a given string into a phone number format.
 * @param {string} phoneNumber the string to format
 * @return {string} formatted phone number
 */
function maskPhoneNumber(phoneNumber = "") {
  const digits = phoneNumber
    .replace(/\D/g, "")
    .match(/(\d{0,3})(\d{0,3})(\d{0,4})/);

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
  return "";
}

// ============================================================================
// ACCORDION FUNCTIONS
// ============================================================================

/**
 * Sets up tab switching functionality for accordion content
 */
function setupAccordionTabs() {
  const tabs = document.querySelectorAll(".accordion-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      const tabId = this.getAttribute("data-tab");
      const accordionBody = this.closest(".accordion-body");

      // Remove active class from all tabs in this accordion
      accordionBody
        .querySelectorAll(".accordion-tab")
        .forEach((t) => t.classList.remove("active"));
      accordionBody
        .querySelectorAll(".accordion-tab-content")
        .forEach((c) => c.classList.remove("active"));

      // Add active class to clicked tab and content
      this.classList.add("active");
      const content = accordionBody.querySelector(`#${tabId}`);
      if (content) {
        content.classList.add("active");
      }
    });
  });
}

/**
 * Updates the accordion visibility based on consent states
 * @param {boolean} emailConsentChecked whether email consent is checked
 * @param {boolean} textConsentChecked whether text consent is checked
 */
function updateAccordionVisibility(emailConsentChecked, textConsentChecked) {
  const emailAccordion = document.getElementById("email-accordion");
  const textAccordion = document.getElementById("text-accordion");
  const emailExpandBtn = document.getElementById("email-expand-btn");
  const emailCollapseBtn = document.getElementById("email-collapse-btn");
  const textExpandBtn = document.getElementById("text-expand-btn");
  const textCollapseBtn = document.getElementById("text-collapse-btn");

  if (emailAccordion) {
    emailAccordion.classList.toggle("expanded", emailConsentChecked);
    // Update button states
    if (emailExpandBtn)
      emailExpandBtn.style.display = emailConsentChecked
        ? "none"
        : "inline-flex";
    if (emailCollapseBtn)
      emailCollapseBtn.style.display = emailConsentChecked
        ? "inline-flex"
        : "none";
  }

  if (textAccordion) {
    textAccordion.classList.toggle("expanded", textConsentChecked);
    // Update button states
    if (textExpandBtn)
      textExpandBtn.style.display = textConsentChecked ? "none" : "inline-flex";
    if (textCollapseBtn)
      textCollapseBtn.style.display = textConsentChecked
        ? "inline-flex"
        : "none";
  }
}

// ============================================================================
// LEASE MANAGEMENT FUNCTIONS
// ============================================================================

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
  const res = await authorizedFetch("/deleteAccount");
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
 * Displays the UI for a signed in user and initializes the lease forms.
 * @param {firebase.User} user
 */
async function handleSignedInUser(user) {
  // Show signed in view
  document.getElementById("user-signed-in").style.display = "block";
  document.getElementById("user-signed-out").style.display = "none";

  // Get user's profile information
  profileInfo = await getProfileInfo();
  console.log("Profile info from API:", profileInfo);
  // Store profile info globally for access by other functions
  window.userProfileInfo = profileInfo;
  initProfileForm(profileInfo);

  // Setup delete account button
  document
    .getElementById("confirm-account-deletion-btn")
    .addEventListener("click", deleteAccount);

  // Setup lease search functionality
  document
    .getElementById("lease-search-text-input")
    .addEventListener("input", searchLeasesOnDelay);
  document
    .getElementById("lease-search-btn")
    .addEventListener("click", searchLeases);
  document
    .getElementById("lease-clear-btn")
    .addEventListener("click", clearLeaseSearch);

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
    user ? handleSignedInUser(user) : handleSignedOutUser();
  });
})();
