"use strict";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";
import { auth, authorizedFetch } from "../common/common.js";

/* The number of milliseconds between when a user changes the lease search
   text and when an API request is sent for a lease search */
const LEASE_SEARCH_DELAY = 400;
/** The path to the growing unit boundaries file. */
const LEASES_BOUNDS_PATH = "static/fl_leases_boundary.geojson";

let profileInfo = {};
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

/**
 * Initializes the profile form with the given profile information.
 * @param {object} profInfo the profile information to initialize the form with
 * @param {boolean} ignoreAddingEventListeners whether or not to ignore adding
 *    event listeners as part of the form initialization. This is useful if the
 *    form has already been created, but you are resetting the values.
 */
function initProfileForm(profInfo, ignoreAddingEventListeners) {
  // setup profile information form
  const profForm = document.forms["profile-information-form"];
  const emailInput = profForm.elements["email-address"];
  const phoneNumberInput = profForm.elements["phone-number"];
  const noNotificationsCheckbox = profForm.elements["no-notifications"];
  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const textCheckboxLabel = textCheckbox.labels[0];
  const probRadios = profForm.elements["notification-prob"];
  const cancelBtn = profForm.elements["prof-form-cancel-btn"];
  const saveBtn = profForm.elements["prof-form-save-btn"];

  // set values for inputs
  emailInput.value = profInfo.email;
  phoneNumberInput.value = maskPhoneNumber(profInfo.phone_number);

  // Set default state: if no preferences are set, default to "no notifications"
  const hasEmailPref = profInfo.email_pref === true;
  const hasTextPref = profInfo.text_pref === true;

  // Default to "no notifications" if neither email nor text preferences are explicitly set
  noNotificationsCheckbox.checked = !hasEmailPref && !hasTextPref;
  emailCheckbox.checked = hasEmailPref;
  textCheckbox.checked = hasTextPref;

  // Set consent checkboxes based on preferences (for initial load)
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  if (emailConsentCheckbox) {
    // Enable email consent by default, or use existing preference if available
    emailConsentCheckbox.checked =
      profInfo.email_consent !== undefined
        ? profInfo.email_consent
        : hasEmailPref;
  }
  if (textConsentCheckbox) {
    textConsentCheckbox.checked =
      profInfo.text_consent !== undefined ? profInfo.text_consent : hasTextPref;
  }

  // Initially expand accordions if user has preferences enabled
  if (hasEmailPref || hasTextPref) {
    updateAccordionVisibility(hasEmailPref, hasTextPref);
  }
  // set values for radio buttons
  for (let radio of probRadios) {
    const value = profInfo.prob_pref && profInfo.prob_pref.toString();
    radio.checked = radio.value === value;
    // disable the radios if "No notifications" is checked
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // disable cancel and save buttons
  cancelBtn.disabled = true;
  saveBtn.disabled = true;

  // example notification text comes from the template; no dynamic override

  // add event listeners
  if (!ignoreAddingEventListeners) {
    profForm.addEventListener("input", onProfileFormChange);
    cancelBtn.addEventListener("click", cancelProfileFormChanges);
    saveBtn.addEventListener("click", saveProfileFormChanges);
    phoneNumberInput.addEventListener(
      "input",
      (e) => (phoneNumberInput.value = maskPhoneNumber(e.target.value))
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

    // Setup accordion functionality
    setupAccordionButtons();
    setupAccordionTabs();

    // Show initial notification status
    updateNotificationStatus();
  }
}

/**
 * Formats a given string into a phone number (pulls out all digits and formats them).
 * @param {string} phoneNumber the string to format
 */
function maskPhoneNumber(phoneNumber = "") {
  // get the digits from the input
  const digits = phoneNumber
    .replace(/\D/g, "")
    .match(/(\d{0,3})(\d{0,3})(\d{0,4})/);

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
  return "";
}

// ============================================================================
// ACCORDION FUNCTIONS
// ============================================================================

/**
 * Sets up accordion buttons for expand/collapse functionality
 */
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

/**
 * Sets up accordion tabs for switching between input and example views
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

// Removed generateExampleNotification; example text is static in HTML

/**
 * Enables the cancel and save buttons on the profile info form.
 * @param {object} e the change event
 */
function onProfileFormChange(e) {
  const profForm = e.target.form;
  const phoneNumberInput = profForm.elements["phone-number"];
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

  // Handle "no notifications" logic
  if (e.target === noNotificationsCheckbox) {
    // If "no notifications" is checked, uncheck email and text preferences
    if (noNotificationsCheckbox.checked) {
      emailCheckbox.checked = textCheckbox.checked = false;
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
      emailInput.value
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

  // Update notification status message
  updateNotificationStatus();
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
    ""
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
      // Reinitialize the form only on success so UI reflects saved state
      initProfileForm(profileInfo, true);
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
    emailConsentCheckbox ? emailConsentCheckbox.checked : "N/A"
  );
  console.log("Text checkbox checked:", textCheckbox.checked);
  console.log(
    "Text consent checked:",
    textConsentCheckbox ? textConsentCheckbox.checked : "N/A"
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
// NOTIFICATION STATUS FUNCTIONS
// ============================================================================

/**
 * Updates the notification status message to inform users whether they will receive notifications
 * based on their current form selections.
 */
function updateNotificationStatus() {
  const profForm = document.forms["profile-information-form"];
  const emailStatusText = document.getElementById("email-notification-status");
  const textStatusText = document.getElementById("text-notification-status");

  if (!profForm || !emailStatusText || !textStatusText) {
    return;
  }

  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  const emailInput = profForm.elements["email-address"];
  const phoneInput = profForm.elements["phone-number"];
  const noNotificationsCheckbox = profForm.elements["no-notifications"];

  // Check if "no notifications" is selected
  if (noNotificationsCheckbox && noNotificationsCheckbox.checked) {
    emailStatusText.innerHTML = "🚫 Email notifications disabled";
    emailStatusText.style.color = "orange";
    emailStatusText.style.textAlign = "left";
    textStatusText.innerHTML = "🚫 Text notifications disabled";
    textStatusText.style.color = "orange";
    textStatusText.style.textAlign = "left";
    return;
  }

  // Check email notification requirements
  let emailReady = false;
  if (emailCheckbox && emailCheckbox.checked) {
    if (emailConsentCheckbox && emailConsentCheckbox.checked) {
      const email = emailInput.value.trim();
      if (
        email &&
        email !== "you@example.com" &&
        !email.includes("example.com")
      ) {
        emailReady = true;
      }
    }
  }

  // Check text notification requirements
  let textReady = false;
  if (textCheckbox && textCheckbox.checked) {
    if (textConsentCheckbox && textConsentCheckbox.checked) {
      const phoneNumber = phoneInput.value.replace(/\D/g, "");
      if (phoneNumber && phoneNumber.length === 10) {
        textReady = true;
      }
    }
  }

  // Update email status
  if (emailReady) {
    emailStatusText.innerHTML = "✅ Email notifications enabled";
    emailStatusText.style.color = "green";
    emailStatusText.style.textAlign = "left";
  } else {
    // Check what's missing for email
    let emailMissingItems = [];

    if (emailCheckbox && emailCheckbox.checked) {
      if (!emailConsentCheckbox || !emailConsentCheckbox.checked) {
        emailMissingItems.push("check consent");
      }
      if (
        !emailInput.value.trim() ||
        emailInput.value.includes("example.com")
      ) {
        emailMissingItems.push("enter valid email");
      }
    }

    if (emailMissingItems.length > 0) {
      emailStatusText.innerHTML = `⚠️ To receive notifications: ${emailMissingItems.join(
        ", "
      )}`;
      emailStatusText.style.color = "orange";
      emailStatusText.style.textAlign = "left";
    } else {
      emailStatusText.innerHTML =
        "📧 You will not receive notifications - `Email` unchecked";
      emailStatusText.style.color = "blue";
      emailStatusText.style.textAlign = "left";
    }
  }

  // Update text status
  if (textReady) {
    textStatusText.innerHTML = "✅ Text notifications enabled";
    textStatusText.style.color = "green";
    textStatusText.style.textAlign = "left";
  } else {
    // Check what's missing for text
    let textMissingItems = [];

    if (textCheckbox && textCheckbox.checked) {
      if (!textConsentCheckbox || !textConsentCheckbox.checked) {
        textMissingItems.push("check consent");
      }
      if (
        !phoneInput.value.replace(/\D/g, "") ||
        phoneInput.value.replace(/\D/g, "").length !== 10
      ) {
        textMissingItems.push("enter valid phone");
      }
    }

    if (textMissingItems.length > 0) {
      textStatusText.innerHTML = `⚠️ To receive notifications: ${textMissingItems.join(
        ", "
      )}`;
      textStatusText.style.color = "orange";
      textStatusText.style.textAlign = "left";
    } else {
      textStatusText.innerHTML =
        "📱 You will not receive notifications - `Text` unchecked";
      textStatusText.style.color = "blue";
      textStatusText.style.textAlign = "left";
    }
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
  console.log("Profile info from API:", profileInfo);
  // Store profile info globally for access by other functions
  window.userProfileInfo = profileInfo;
  initProfileForm(profileInfo);

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
