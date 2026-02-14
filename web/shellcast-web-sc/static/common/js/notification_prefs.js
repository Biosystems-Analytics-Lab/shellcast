"use strict";
/**
 * Common notification preferences form logic.
 * Used by NC, FL, SC. Initialize with initNotificationForm(deps).
 * @module notification_prefs
 */

// ============================================================================
// HELPERS (no deps)
// ============================================================================

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function validatePhoneNumber(phoneNumber) {
  return (
    phoneNumber && phoneNumber.length === 10 && /^\d{10}$/.test(phoneNumber)
  );
}

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
// INIT: build closure over deps
// ============================================================================

/**
 * Initializes the notification preferences form. Call once after DOM and profile data are ready.
 * @param {object} deps - Dependencies from the host app
 * @param {function} deps.authorizedFetch - (path, opts) => Promise<Response>
 * @param {function} deps.getProfileInfo - () => current profile object
 * @param {function} deps.setProfileInfo - (profile) => void
 * @param {function} deps.getSavedProfileData - () => saved form state for change detection
 * @param {function} deps.setSavedProfileData - (data) => void
 */
export function initNotificationForm(deps) {
  const {
    authorizedFetch,
    getProfileInfo,
    setProfileInfo,
    getSavedProfileData,
    setSavedProfileData,
  } = deps;

  function getCurrentFormValues() {
    const profForm = document.forms["profile-information-form"];
    const emailInput = profForm?.elements["email-address"];
    const phoneInput = profForm?.elements["phone-number"];
    const emailCheckbox = profForm?.elements["email-pref"];
    const textCheckbox = profForm?.elements["text-pref"];
    const emailConsentCheckbox = profForm?.elements["email-consent"];
    const textConsentCheckbox = profForm?.elements["text-consent"];
    const probRadios = profForm?.elements["notification-prob"];

    let selectedProb = 3;
    if (probRadios) {
      for (let radio of probRadios) {
        if (radio.checked) {
          selectedProb = Number(radio.value);
          break;
        }
      }
    }

    const phoneDigits = (phoneInput?.value || "").replace(/\D/g, "");

    return {
      email: (emailInput?.value || "").trim(),
      phone_number: phoneDigits,
      email_pref: Boolean(emailCheckbox?.checked),
      text_pref: Boolean(textCheckbox?.checked),
      email_consent: emailConsentCheckbox ? Boolean(emailConsentCheckbox.checked) : true,
      text_consent: Boolean(textConsentCheckbox?.checked),
      prob_pref: Number(selectedProb) || 3,
    };
  }

  function hasFormChanges() {
    const saved = getSavedProfileData();
    if (!saved || Object.keys(saved).length === 0) {
      return false;
    }

    const current = getCurrentFormValues();
    const s = {
      email: (saved.email || "").trim(),
      phone_number: String(saved.phone_number || "").replace(/\D/g, ""),
      email_pref: Boolean(saved.email_pref),
      text_pref: Boolean(saved.text_pref),
      email_consent: Boolean(saved.email_consent),
      text_consent: Boolean(saved.text_consent),
      prob_pref: Number(saved.prob_pref) || 3,
    };

    return (
      current.email !== s.email ||
      current.phone_number !== s.phone_number ||
      current.email_pref !== s.email_pref ||
      current.text_pref !== s.text_pref ||
      current.email_consent !== s.email_consent ||
      current.text_consent !== s.text_consent ||
      current.prob_pref !== s.prob_pref
    );
  }

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

  function updateEmailNotificationStatus() {
    const profForm = document.forms["profile-information-form"];
    const emailCheckbox = profForm?.elements["email-pref"];
    const emailInput = profForm?.elements["email-address"];
    const statusEmoji = document.getElementById("email-status-emoji");
    const statusMessage = document.getElementById("email-status-message");

    if (!statusEmoji || !statusMessage) return;

    const email = emailInput ? emailInput.value.trim() : "";
    const hasValidEmail =
      email &&
      email !== "you@example.com" &&
      !email.includes("example.com") &&
      validateEmail(email);
    const emailEnabled = emailCheckbox && emailCheckbox.checked;

    if (emailEnabled && hasValidEmail) {
      statusEmoji.textContent = "✅";
      statusMessage.textContent =
        "You will receive email notifications for lease closure alerts.";
    } else if (emailEnabled && !hasValidEmail) {
      statusEmoji.textContent = "⚠️";
      statusMessage.textContent =
        "Please enter a valid email address to receive email notifications.";
    } else {
      statusEmoji.textContent = "ℹ️";
      statusMessage.textContent = "Email notifications are currently disabled.";
    }
  }

  function updateTextNotificationStatus() {
    const profForm = document.forms["profile-information-form"];
    const textCheckbox = profForm?.elements["text-pref"];
    const textConsentCheckbox = profForm?.elements["text-consent"];
    const phoneInput = profForm?.elements["phone-number"];
    const statusEmoji = document.getElementById("text-status-emoji");
    const statusMessage = document.getElementById("text-status-message");

    if (!statusEmoji || !statusMessage) return;

    const phoneNumber = phoneInput ? phoneInput.value.replace(/\D/g, "") : "";
    const hasValidPhone = phoneNumber && phoneNumber.length === 10;
    const hasConsent = textConsentCheckbox && textConsentCheckbox.checked;
    const textEnabled = textCheckbox && textCheckbox.checked;

    if (textEnabled && hasValidPhone && hasConsent) {
      statusEmoji.textContent = "✅";
      statusMessage.textContent =
        "You will receive text notifications for lease closure alerts.";
    } else if (textEnabled && !hasConsent) {
      statusEmoji.textContent = "⚠️";
      statusMessage.textContent =
        "You must check the consent box above to receive text notifications.";
    } else if (textEnabled && !hasValidPhone) {
      statusEmoji.textContent = "⚠️";
      statusMessage.textContent =
        "Please enter a valid 10-digit phone number to receive text notifications.";
    } else {
      statusEmoji.textContent = "ℹ️";
      statusMessage.textContent = "Text notifications are currently disabled.";
    }
  }

  function updateAccordionVisibility(emailExpanded, textExpanded) {
    const emailAccordion = document.getElementById("email-accordion");
    const textAccordion = document.getElementById("text-accordion");
    const emailExpandBtn = document.getElementById("email-expand-btn");
    const emailCollapseBtn = document.getElementById("email-collapse-btn");
    const textExpandBtn = document.getElementById("text-expand-btn");
    const textCollapseBtn = document.getElementById("text-collapse-btn");

    if (emailAccordion) {
      emailAccordion.classList.toggle("expanded", emailExpanded);
      if (emailExpandBtn)
        emailExpandBtn.style.display = emailExpanded ? "none" : "inline-flex";
      if (emailCollapseBtn)
        emailCollapseBtn.style.display = emailExpanded ? "inline-flex" : "none";
    }

    if (textAccordion) {
      textAccordion.classList.toggle("expanded", textExpanded);
      if (textExpandBtn)
        textExpandBtn.style.display = textExpanded ? "none" : "inline-flex";
      if (textCollapseBtn)
        textCollapseBtn.style.display = textExpanded ? "inline-flex" : "none";
    }
  }

  function validateForm() {
    const profForm = document.forms["profile-information-form"];
    const emailCheckbox = profForm?.elements["email-pref"];
    const textCheckbox = profForm?.elements["text-pref"];
    const emailInput = profForm?.elements["email-address"];
    const phoneInput = profForm?.elements["phone-number"];
    const textConsentCheckbox = profForm?.elements["text-consent"];
    const saveBtn = profForm?.elements["prof-form-save-btn"];
    const cancelBtn = profForm?.elements["prof-form-cancel-btn"];

    let isValid = true;

    if (emailCheckbox?.checked) {
      const email = emailInput?.value?.trim() ?? "";
      if (!email || !validateEmail(email)) {
        emailInput?.classList.add("is-invalid");
        isValid = false;
      } else {
        emailInput?.classList.remove("is-invalid");
      }
    } else {
      emailInput?.classList.remove("is-invalid");
    }

    if (textCheckbox?.checked) {
      const phoneNumber = phoneInput?.value?.replace(/\D/g, "") ?? "";
      const hasTextConsent = textConsentCheckbox?.checked ?? false;
      if (!phoneNumber || !validatePhoneNumber(phoneNumber)) {
        phoneInput?.classList.add("is-invalid");
        isValid = false;
      } else {
        phoneInput?.classList.remove("is-invalid");
      }
      if (!hasTextConsent) isValid = false;
    } else {
      phoneInput?.classList.remove("is-invalid");
    }

    updateEmailNotificationStatus();
    updateTextNotificationStatus();

    const hasChanges = hasFormChanges();
    if (saveBtn) saveBtn.disabled = !hasChanges;
    if (cancelBtn) cancelBtn.disabled = !hasChanges;
    updateFormStatus(hasChanges);

    return isValid;
  }

  function setupAccordionTabs() {
    const tabs = document.querySelectorAll(".accordion-tab");
    tabs.forEach((tab) => {
      tab.addEventListener("click", function () {
        const tabId = this.getAttribute("data-tab");
        const accordionBody = this.closest(".accordion-body");

        accordionBody
          ?.querySelectorAll(".accordion-tab")
          ?.forEach((t) => t.classList.remove("active"));
        accordionBody
          ?.querySelectorAll(".accordion-tab-content")
          ?.forEach((c) => c.classList.remove("active"));

        this.classList.add("active");
        const content = accordionBody?.querySelector(`#${tabId}`);
        if (content) content.classList.add("active");

        const textNotificationStatus = document.getElementById(
          "text-notification-status",
        );
        if (textNotificationStatus) {
          if (tabId === "text-input") {
            textNotificationStatus.style.display = "block";
          } else if (tabId === "text-example") {
            textNotificationStatus.style.display = "none";
          }
        }
      });
    });
  }

  function setupExpandCollapseButtons() {
    const emailExpandBtn = document.getElementById("email-expand-btn");
    const emailCollapseBtn = document.getElementById("email-collapse-btn");
    const textExpandBtn = document.getElementById("text-expand-btn");
    const textCollapseBtn = document.getElementById("text-collapse-btn");

    const expandEmail = () => {
      document.getElementById("email-accordion")?.classList.add("expanded");
      if (emailExpandBtn) emailExpandBtn.style.display = "none";
      if (emailCollapseBtn) emailCollapseBtn.style.display = "inline-flex";
    };
    const collapseEmail = () => {
      document.getElementById("email-accordion")?.classList.remove("expanded");
      if (emailExpandBtn) emailExpandBtn.style.display = "inline-flex";
      if (emailCollapseBtn) emailCollapseBtn.style.display = "none";
    };
    const expandText = () => {
      document.getElementById("text-accordion")?.classList.add("expanded");
      if (textExpandBtn) textExpandBtn.style.display = "none";
      if (textCollapseBtn) textCollapseBtn.style.display = "inline-flex";
    };
    const collapseText = () => {
      document.getElementById("text-accordion")?.classList.remove("expanded");
      if (textExpandBtn) textExpandBtn.style.display = "inline-flex";
      if (textCollapseBtn) textCollapseBtn.style.display = "none";
    };

    emailExpandBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      expandEmail();
    });
    emailCollapseBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      collapseEmail();
    });
    textExpandBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      expandText();
    });
    textCollapseBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      collapseText();
    });
  }

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
    if (!profForm) return;

    const emailInput = profForm.elements["email-address"];
    const phoneNumberInput = profForm.elements["phone-number"];
    const noNotificationsCheckbox = profForm.elements["no-notifications"];
    const emailCheckbox = profForm.elements["email-pref"];
    const textCheckbox = profForm.elements["text-pref"];
    const probRadios = profForm.elements["notification-prob"];
    const cancelBtn = profForm.elements["prof-form-cancel-btn"];
    const saveBtn = profForm.elements["prof-form-save-btn"];

    if (!ignoreAddingEventListeners) {
      const phoneDigits = (profInfo.phone_number || "").replace(/\D/g, "");
      setSavedProfileData({
        email: (profInfo.email || "").trim(),
        phone_number: phoneDigits,
        email_pref: Boolean(profInfo.email_pref),
        text_pref: Boolean(profInfo.text_pref),
        email_consent: Boolean(profInfo.email_consent),
        text_consent: Boolean(profInfo.text_consent),
        prob_pref: Number(profInfo.prob_pref) || 3,
      });
    }

    emailInput.value = profInfo.email || "";
    phoneNumberInput.value = maskPhoneNumber(profInfo.phone_number || "");
    emailCheckbox.checked = profInfo.email_pref;
    textCheckbox.checked = profInfo.text_pref;
    noNotificationsCheckbox.checked =
      !profInfo.email_pref && !profInfo.text_pref;

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

    updateAccordionVisibility(profInfo.email_pref, true);

    for (let radio of probRadios || []) {
      const value = profInfo.prob_pref && profInfo.prob_pref.toString();
      radio.checked = radio.value === value;
      radio.disabled = noNotificationsCheckbox.checked;
    }

    if (!ignoreAddingEventListeners) {
      profForm.addEventListener("input", onProfileFormChange);
      profForm.addEventListener("change", onProfileFormChange);
      cancelBtn.addEventListener("click", cancelProfileFormChanges);
      saveBtn.addEventListener("click", saveProfileFormChanges);
      phoneNumberInput.addEventListener("input", (e) => {
        phoneNumberInput.value = maskPhoneNumber(e.target.value);
      });
      emailConsentCheckbox?.addEventListener("change", validateForm);
      textConsentCheckbox?.addEventListener("change", validateForm);
      setupAccordionTabs();
      setupExpandCollapseButtons();
    }

    updateEmailNotificationStatus();
    updateTextNotificationStatus();
    validateForm();
  }

  function onProfileFormChange(e) {
    const profForm = e.target.form;
    const noNotificationsCheckbox = profForm.elements["no-notifications"];
    const emailCheckbox = profForm.elements["email-pref"];
    const textCheckbox = profForm.elements["text-pref"];
    const emailConsentCheckbox = profForm.elements["email-consent"];
    const textConsentCheckbox = profForm.elements["text-consent"];
    const probRadios = profForm.elements["notification-prob"];

    const helpText = document.getElementById("profile-form-help-text");
    if (helpText) {
      helpText.innerHTML = "";
      helpText.style.color = "";
    }

    if (e.target === noNotificationsCheckbox) {
      if (noNotificationsCheckbox.checked) {
        emailCheckbox.checked = textCheckbox.checked = false;
        if (emailConsentCheckbox) emailConsentCheckbox.checked = false;
        if (textConsentCheckbox) textConsentCheckbox.checked = false;
      }
    } else if (e.target === emailCheckbox || e.target === textCheckbox) {
      if (
        e.target === emailCheckbox &&
        !emailCheckbox.checked &&
        emailConsentCheckbox
      ) {
        emailConsentCheckbox.checked = false;
      }
      if (
        e.target === textCheckbox &&
        !textCheckbox.checked &&
        textConsentCheckbox
      ) {
        textConsentCheckbox.checked = false;
      }
      if (emailCheckbox.checked || textCheckbox.checked) {
        noNotificationsCheckbox.checked = false;
      } else {
        noNotificationsCheckbox.checked = true;
      }
    }

    if (e.target === emailCheckbox && emailCheckbox.checked) {
      const emailInput = profForm.elements["email-address"];
      const currentEmail = emailInput.value.trim();
      const isPlaceholderOrEmpty =
        !currentEmail ||
        currentEmail === "you@example.com" ||
        currentEmail === "You@example.com" ||
        currentEmail.includes("example.com");
      const profileInfo = getProfileInfo();
      if (
        isPlaceholderOrEmpty &&
        profileInfo &&
        profileInfo.email
      ) {
        emailInput.value = profileInfo.email;
      }
    }

    if (e.target === noNotificationsCheckbox && noNotificationsCheckbox.checked) {
      updateAccordionVisibility(false, false);
    } else if (e.target === emailCheckbox && emailCheckbox.checked) {
      updateAccordionVisibility(true, textCheckbox.checked);
    } else if (e.target === textCheckbox && textCheckbox.checked) {
      updateAccordionVisibility(emailCheckbox.checked, true);
    }

    if (emailConsentCheckbox) {
      emailConsentCheckbox.disabled = !emailCheckbox.checked;
    }
    if (textConsentCheckbox) {
      textConsentCheckbox.disabled = !textCheckbox.checked;
    }

    for (let radio of probRadios || []) {
      radio.disabled = noNotificationsCheckbox.checked;
    }

    updateEmailNotificationStatus();
    validateForm();
  }

  function cancelProfileFormChanges() {
    initProfileForm(getProfileInfo(), true);
    validateForm();
  }

  async function saveProfileFormChanges() {
    const profForm = document.forms["profile-information-form"];
    const helpText = document.getElementById("profile-form-help-text");

    if (!profForm || !helpText) {
      console.error("Required form elements not found!");
      return;
    }

    if (!validateForm()) return;

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
      : true;
    const textConsentChecked = profForm.elements["text-consent"]
      ? profForm.elements["text-consent"].checked
      : false;
    const probRadios = profForm.elements["notification-prob"];

    let selectedProb;
    for (let radio of probRadios) {
      if (radio.checked) {
        selectedProb = Number(radio.value);
        break;
      }
    }

    const saved = getSavedProfileData();
    const emailToSend = emailPref
      ? (emailConsentChecked ? email : (saved?.email || email) || null)
      : null;
    const phoneToSend = textPref && phoneNumber ? phoneNumber : null;

    const newProfileInfo = {
      email: emailToSend,
      phone_number: phoneToSend,
      service_provider_id: null,
      email_pref: emailPref,
      text_pref: textPref,
      prob_pref: selectedProb,
      email_consent: emailConsentChecked,
      text_consent: textConsentChecked,
    };

    try {
      const res = await authorizedFetch("/user-info", {
        method: "POST",
        headers: { "Content-Type": "application/json;charset=utf-8" },
        body: JSON.stringify(newProfileInfo),
      });

      if (res.ok) {
        const profileInfo = await res.json();
        setProfileInfo(profileInfo);
        helpText.style.color = "green";

        const phoneDigits = (profileInfo.phone_number || "").replace(/\D/g, "");
        setSavedProfileData({
          email: (profileInfo.email || "").trim(),
          phone_number: phoneDigits,
          email_pref: Boolean(profileInfo.email_pref),
          text_pref: Boolean(profileInfo.text_pref),
          email_consent: Boolean(profileInfo.email_consent),
          text_consent: Boolean(profileInfo.text_consent),
          prob_pref: Number(profileInfo.prob_pref) || 3,
        });

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
      initProfileForm(getProfileInfo(), true);
    } catch (error) {
      console.error("Error during save:", error);
      helpText.style.color = "red";
      helpText.innerHTML = "An error occurred while saving. Please try again.";
    }
  }

  initProfileForm(getProfileInfo(), false);
}
