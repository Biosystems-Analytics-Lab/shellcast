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
  if (!profInfo || typeof profInfo !== "object") {
    profInfo = {
      email: "",
      phone_number: "",
      email_pref: false,
      text_pref: false,
      prob_pref: 3,
    };
  }

  const profForm = document.forms["profile-information-form"];
  const emailInput = profForm.elements["email-address"];
  const phoneNumberInput = profForm.elements["phone-number"];
  const noNotificationsCheckbox = profForm.elements["no-notifications"];
  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const probRadios = profForm.elements["notification-prob"];
  const cancelBtn = profForm.elements["prof-form-cancel-btn"];
  const saveBtn = profForm.elements["prof-form-save-btn"];

  // Store original saved data for comparison (only on first load, not after save)
  // Track: email_pref, email, email_consent, text_pref, text_consent, phone_number, prob_pref
  if (!ignoreAddingEventListeners) {
    const phoneDigits = (profInfo.phone_number || "").replace(/\D/g, "");
    const emailPref = Boolean(profInfo.email_pref);
    const textPref = Boolean(profInfo.text_pref);
    const emailConsent = Boolean(profInfo.email_consent);
    const textConsent = Boolean(profInfo.text_consent);
    savedProfileData = {
      email: (profInfo.email || "").trim(),
      phone_number: phoneDigits,
      email_pref: emailPref,
      text_pref: textPref,
      email_consent: emailConsent,
      text_consent: textConsent,
      prob_pref: Number(profInfo.prob_pref) || 3,
    };
  }

  // Set form values
  emailInput.value = profInfo.email || "";
  phoneNumberInput.value = maskPhoneNumber(profInfo.phone_number || "");
  emailCheckbox.checked = profInfo.email_pref;
  textCheckbox.checked = profInfo.text_pref;

  // Set "no notifications" based on email and text preferences
  // If neither email nor text is enabled, check "no notifications"
  noNotificationsCheckbox.checked = !profInfo.email_pref && !profInfo.text_pref;

  // Set consent from database only; never auto-check when user checks preference (user must consent explicitly)
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  if (emailConsentCheckbox) {
    emailConsentCheckbox.checked = Boolean(profInfo.email_consent);
    emailConsentCheckbox.disabled = !emailCheckbox.checked;
  }
  if (textConsentCheckbox) {
    textConsentCheckbox.checked = Boolean(profInfo.text_consent);
    textConsentCheckbox.disabled = !textCheckbox.checked;
  }

  // Initially expand accordions based on user preferences
  // Expand text accordion by default so users can see the settings
  updateAccordionVisibility(profInfo.email_pref, true);

  // Set probability preference
  for (let radio of probRadios) {
    const value = profInfo.prob_pref && profInfo.prob_pref.toString();
    radio.checked = radio.value === value;
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // Add event listeners
  if (!ignoreAddingEventListeners) {
    profForm.addEventListener("input", onProfileFormChange);
    profForm.addEventListener("change", onProfileFormChange);
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
    setupExpandCollapseButtons();
  }

  // Update text notification status on page load
  updateTextNotificationStatus();

  // Set Submit/Cancel button state based on changes (disabled when form matches saved data)
  validateForm();
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

  // Consent is never auto-checked; user must check it explicitly (common practice for SMS/email opt-in).
  // We do not change preference or clear fields when user unchecks consent; save uses effective opt-in.

  // Handle preference checkbox logic

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
    // If user unchecks preference, also uncheck consent (common practice: no channel = no consent)
    if (e.target === emailCheckbox && !emailCheckbox.checked && emailConsentCheckbox) {
      emailConsentCheckbox.checked = false;
    }
    if (e.target === textCheckbox && !textCheckbox.checked && textConsentCheckbox) {
      textConsentCheckbox.checked = false;
    }
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

  // Disable consent checkboxes unless the corresponding preference is checked (avoids consent-only state)
  if (emailConsentCheckbox) {
    emailConsentCheckbox.disabled = !emailCheckbox.checked;
  }
  if (textConsentCheckbox) {
    textConsentCheckbox.disabled = !textCheckbox.checked;
  }

  // Update probability radio button states
  for (let radio of probRadios) {
    radio.disabled = noNotificationsCheckbox.checked;
  }

  // Validate form and update button states (including cancel button based on changes)
  validateForm();
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
 * Resets the profile form to its original state.
 */
function cancelProfileFormChanges() {
  initProfileForm(profileInfo, true);
  // Update button states after reset
  validateForm();
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

  // Save phone when Text is checked and number is entered; consent is saved separately (SMS only sent when both pref and consent).
  // Email: keep saved email when pref on but consent off so we don't accidentally clear.
  const effectiveEmailPref = emailPref && emailConsentChecked;
  const emailToSend = emailPref
    ? (emailConsentChecked ? email : (savedProfileData.email || email) || null)
    : null;
  const phoneToSend = textPref && phoneNumber ? phoneNumber : null;

  const newProfileInfo = {
    email: emailToSend,
    phone_number: phoneToSend,
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

      // Update saved data to reflect the new saved state (use consent from response)
      const phoneDigits = (profileInfo.phone_number || "").replace(/\D/g, "");
      savedProfileData = {
        email: (profileInfo.email || "").trim(),
        phone_number: phoneDigits,
        email_pref: Boolean(profileInfo.email_pref),
        text_pref: Boolean(profileInfo.text_pref),
        email_consent: Boolean(profileInfo.email_consent),
        text_consent: Boolean(profileInfo.text_consent),
        prob_pref: Number(profileInfo.prob_pref) || 3,
      };

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
 * Gets the current form values for comparison
 * @return {object} current form values
 */
function getCurrentFormValues() {
  const profForm = document.forms["profile-information-form"];
  const emailInput = profForm.elements["email-address"];
  const phoneInput = profForm.elements["phone-number"];
  const emailCheckbox = profForm.elements["email-pref"];
  const textCheckbox = profForm.elements["text-pref"];
  const emailConsentCheckbox = profForm.elements["email-consent"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  const probRadios = profForm.elements["notification-prob"];

  // Get selected probability
  let selectedProb = 3;
  for (let radio of probRadios) {
    if (radio.checked) {
      selectedProb = Number(radio.value);
      break;
    }
  }

  const phoneDigits = (phoneInput?.value || "").replace(/\D/g, "");

  // Return raw form state for change detection (all 7 tracked fields)
  return {
    email: (emailInput?.value || "").trim(),
    phone_number: phoneDigits,
    email_pref: Boolean(emailCheckbox?.checked),
    text_pref: Boolean(textCheckbox?.checked),
    email_consent: Boolean(emailConsentCheckbox?.checked),
    text_consent: Boolean(textConsentCheckbox?.checked),
    prob_pref: Number(selectedProb) || 3,
  };
}

/**
 * Checks if the form has changes from the saved data
 * @return {boolean} true if there are changes
 */
function hasFormChanges() {
  if (!savedProfileData || Object.keys(savedProfileData).length === 0) {
    return false;
  }

  const current = getCurrentFormValues();
  const saved = {
    email: (savedProfileData.email || "").trim(),
    phone_number: String(savedProfileData.phone_number || "").replace(/\D/g, ""),
    email_pref: Boolean(savedProfileData.email_pref),
    text_pref: Boolean(savedProfileData.text_pref),
    email_consent: Boolean(savedProfileData.email_consent),
    text_consent: Boolean(savedProfileData.text_consent),
    prob_pref: Number(savedProfileData.prob_pref) || 3,
  };

  const emailChanged = current.email !== saved.email;
  const phoneChanged = current.phone_number !== saved.phone_number;
  const emailPrefChanged = current.email_pref !== saved.email_pref;
  const textPrefChanged = current.text_pref !== saved.text_pref;
  const emailConsentChanged = current.email_consent !== saved.email_consent;
  const textConsentChanged = current.text_consent !== saved.text_consent;
  const probPrefChanged = current.prob_pref !== saved.prob_pref;

  return (
    emailChanged ||
    phoneChanged ||
    emailPrefChanged ||
    textPrefChanged ||
    emailConsentChanged ||
    textConsentChanged ||
    probPrefChanged
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
  const cancelBtn = profForm.elements["prof-form-cancel-btn"];

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

  // Update text notification status message
  updateTextNotificationStatus();

  // Check if there are actual changes from saved data (email_pref, email, email_consent, text_pref, text_consent, phone_number, prob_pref)
  const hasChanges = hasFormChanges();

  // Enable submit when there are changes (validation still runs on Submit click)
  saveBtn.disabled = !hasChanges;

  // Enable cancel only if there are changes
  cancelBtn.disabled = !hasChanges;

  // Update form status at bottom: show "You have made changes" when any tracked variable changed
  updateFormStatus(hasChanges);

  return isValid;
}

/**
 * Updates the form status message at the bottom (emoji + text when user has made changes).
 * Tracked variables: email_pref, email, email_consent, text_pref, text_consent, phone_number, prob_pref.
 */
function updateFormStatus(hasChanges) {
  const statusDiv = document.getElementById("profile-form-status");
  const statusEmoji = document.getElementById("profile-form-status-emoji");
  const statusMessage = document.getElementById("profile-form-status-message");

  if (!statusDiv || !statusEmoji || !statusMessage) return;

  if (hasChanges) {
    statusDiv.style.display = "block";
    statusEmoji.textContent = "✏️";
    statusMessage.textContent = "You have made changes. Click Submit to save.";
  } else {
    statusDiv.style.display = "none";
  }
}

/**
 * Updates the text notification status message based on current form state
 */
function updateTextNotificationStatus() {
  const profForm = document.forms["profile-information-form"];
  const textCheckbox = profForm.elements["text-pref"];
  const textConsentCheckbox = profForm.elements["text-consent"];
  const phoneInput = profForm.elements["phone-number"];
  const statusEmoji = document.getElementById("text-status-emoji");
  const statusMessage = document.getElementById("text-status-message");

  if (!statusEmoji || !statusMessage) return;

  const phoneNumber = phoneInput ? phoneInput.value.replace(/\D/g, "") : "";
  const hasValidPhone = phoneNumber && phoneNumber.length === 10;
  const hasConsent = textConsentCheckbox && textConsentCheckbox.checked;
  const textEnabled = textCheckbox && textCheckbox.checked;

  // Determine status and message with emojis
  if (textEnabled && hasValidPhone && hasConsent) {
    // Will receive notifications
    statusEmoji.textContent = "✅";
    statusMessage.textContent =
      "You will receive text notifications for lease closure alerts.";
  } else if (textEnabled && !hasConsent) {
    // Text enabled but no consent
    statusEmoji.textContent = "⚠️";
    statusMessage.textContent =
      "You must check the consent box above to receive text notifications.";
  } else if (textEnabled && !hasValidPhone) {
    // Text enabled but no valid phone
    statusEmoji.textContent = "⚠️";
    statusMessage.textContent =
      "Please enter a valid 10-digit phone number to receive text notifications.";
  } else {
    // Text not enabled
    statusEmoji.textContent = "ℹ️";
    statusMessage.textContent = "Text notifications are currently disabled.";
  }
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

      // Show/hide text notification status based on active tab
      const textNotificationStatus = document.getElementById(
        "text-notification-status",
      );
      if (textNotificationStatus) {
        // Show status only when "Phone Number" tab (text-input) is active
        if (tabId === "text-input") {
          textNotificationStatus.style.display = "block";
        } else if (tabId === "text-example") {
          textNotificationStatus.style.display = "none";
        }
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
