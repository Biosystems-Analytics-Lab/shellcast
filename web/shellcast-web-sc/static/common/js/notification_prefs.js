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
  return phoneNumber && phoneNumber.length === 10 && /^\d{10}$/.test(phoneNumber);
}

function maskPhoneNumber(phoneNumber = "") {
  const digits = phoneNumber.replace(/\D/g, "").match(/(\d{0,3})(\d{0,3})(\d{0,4})/);

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

/** Form and element name constants (single source of truth). */
const FORM_IDS = {
  form: "profile-information-form",
  email: "email-address",
  phone: "phone-number",
  emailPref: "email-pref",
  textPref: "text-pref",
  textConsent: "text-consent",
  probRadios: "notification-prob",
  saveBtn: "prof-form-save-btn",
  cancelBtn: "prof-form-cancel-btn",
  noNotifications: "no-notifications",
  resendVerifyBtn: "resend-text-verification",
};

/**
 * Returns current form and its elements, or null if form missing.
 * @returns {{ form: HTMLFormElement, elements: Record<string, Element> } | null}
 */
function getFormRefs() {
  const form = document.forms[FORM_IDS.form];
  if (!form) return null;
  return {
    form,
    elements: {
      email: form.elements[FORM_IDS.email],
      phone: form.elements[FORM_IDS.phone],
      emailPref: form.elements[FORM_IDS.emailPref],
      textPref: form.elements[FORM_IDS.textPref],
      textConsent: form.elements[FORM_IDS.textConsent],
      probRadios: form.elements[FORM_IDS.probRadios],
      saveBtn: form.elements[FORM_IDS.saveBtn],
      cancelBtn: form.elements[FORM_IDS.cancelBtn],
      noNotifications: form.elements[FORM_IDS.noNotifications],
      resendVerify: document.getElementById(FORM_IDS.resendVerifyBtn),
    },
  };
}

/**
 * Normalize profile data for comparison and storage (consistent trim, digits, booleans, prob).
 * @param {object} raw - Raw profile or form data
 * @returns {object} Normalized object with email, phone_number, email_pref, text_pref, text_consent, prob_pref
 */
function normalizeProfileData(raw) {
  if (!raw || typeof raw !== "object") {
    return {
      email: "",
      phone_number: "",
      email_pref: false,
      text_pref: false,
      text_consent: false,
      prob_pref: 3,
      phone_verified: false,
    };
  }
  const phoneDigits = String(raw.phone_number || "").replace(/\D/g, "");
  return {
    email: (raw.email || "").trim(),
    phone_number: phoneDigits,
    email_pref: Boolean(raw.email_pref),
    text_pref: Boolean(raw.text_pref),
    text_consent: Boolean(raw.text_consent),
    prob_pref: Number(raw.prob_pref) || 3,
    phone_verified: Boolean(raw.phone_verified),
  };
}

/**
 * Get selected value from notification-prob radio group, or 3.
 * @param {HTMLFormControlsCollection|undefined} probRadios
 * @returns {number}
 */
function getSelectedProb(probRadios) {
  if (!probRadios) return 3;
  for (let radio of probRadios) {
    if (radio.checked) return Number(radio.value) || 3;
  }
  return 3;
}

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
    const refs = getFormRefs();
    if (!refs) return normalizeProfileData({});
    const { elements } = refs;
    const phoneDigits = (elements.phone?.value || "").replace(/\D/g, "");
    return normalizeProfileData({
      email: elements.email?.value,
      phone_number: phoneDigits,
      email_pref: elements.emailPref?.checked,
      text_pref: elements.textPref?.checked,
      text_consent: elements.textConsent?.checked,
      prob_pref: getSelectedProb(elements.probRadios),
    });
  }

  function hasFormChanges() {
    const saved = getSavedProfileData();
    if (!saved || Object.keys(saved).length === 0) return false;
    const current = getCurrentFormValues();
    const s = normalizeProfileData(saved);
    return (
      current.email !== s.email ||
      current.phone_number !== s.phone_number ||
      current.email_pref !== s.email_pref ||
      current.text_pref !== s.text_pref ||
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
      const refs = getFormRefs();
      const elements = refs?.elements;
      const textPrefChecked = Boolean(elements?.textPref?.checked);
      const textConsentChecked = Boolean(elements?.textConsent?.checked);

      statusDiv.style.display = "block";
      if (textPrefChecked && !textConsentChecked) {
        // More specific guidance when text is enabled but consent is missing.
        statusEmoji.textContent = "⚠️";
        statusMessage.textContent =
          "You have changes, but must check the consent box above to receive text notifications, or turn text notifications off.";
      } else {
        statusEmoji.textContent = "✏️";
        statusMessage.textContent = "You have made changes. Click Submit to save.";
      }
    } else {
      statusDiv.style.display = "block";
      statusEmoji.textContent = "ℹ️";
      statusMessage.textContent = "You have no unsaved changes.";
    }
  }

  function updateVerificationButtonState() {
    const refs = getFormRefs();
    if (!refs) return;
    const { resendVerify } = refs.elements;
    if (!resendVerify) return;

    // If we've marked this button as rate-limited for today, keep it hidden/disabled.
    if (resendVerify.dataset.rateLimited === "true") {
      resendVerify.disabled = true;
      resendVerify.style.display = "none";
      return;
    }

    const savedRaw = getSavedProfileData();
    if (!savedRaw || Object.keys(savedRaw).length === 0) {
      resendVerify.disabled = true;
      resendVerify.style.display = "none";
      return;
    }
    const saved = normalizeProfileData(savedRaw);
    const current = getCurrentFormValues();
    const hasPhone = Boolean(current.phone_number);
    const textPrefOn = Boolean(current.text_pref);
    const textConsentOn = Boolean(current.text_consent);
    const isVerified = Boolean(saved.phone_verified);
    const shouldEnable = hasPhone && textPrefOn && textConsentOn && !isVerified;
    if (shouldEnable) {
      resendVerify.disabled = false;
      resendVerify.style.display = "inline-block";
    } else {
      resendVerify.disabled = true;
      resendVerify.style.display = "none";
    }
  }

  function updateEmailNotificationStatus() {
    const refs = getFormRefs();
    const statusEmoji = document.getElementById("email-status-emoji");
    const statusMessage = document.getElementById("email-status-message");
    if (!statusEmoji || !statusMessage || !refs) return;

    const { emailPref: emailCheckbox, email: emailInput } = refs.elements;
    const email = (emailInput?.value ?? "").trim();
    const hasValidEmail =
      email &&
      email !== "you@example.com" &&
      !email.includes("example.com") &&
      validateEmail(email);
    const emailEnabled = emailCheckbox?.checked;

    if (emailEnabled && hasValidEmail) {
      statusEmoji.textContent = "✅";
      statusMessage.textContent = "You will receive email notifications for lease closure alerts.";
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
    const refs = getFormRefs();
    const statusEmoji = document.getElementById("text-status-emoji");
    const statusMessage = document.getElementById("text-status-message");
    if (!statusEmoji || !statusMessage || !refs) return;

    const {
      textPref: textCheckbox,
      textConsent: textConsentCheckbox,
      phone: phoneInput,
    } = refs.elements;
    const phoneNumber = phoneInput?.value?.replace(/\D/g, "") ?? "";
    const hasValidPhone = phoneNumber.length === 10;
    const hasConsent = Boolean(textConsentCheckbox?.checked);
    const textEnabled = Boolean(textCheckbox?.checked);
    const savedRaw = getSavedProfileData();
    const saved = normalizeProfileData(savedRaw || {});
    const isVerified = Boolean(saved.phone_verified);

    if (textEnabled && hasValidPhone && hasConsent && isVerified) {
      statusEmoji.textContent = "✅";
      statusMessage.textContent =
        "Your phone number is verified. You will receive text notifications for lease closure alerts.";
    } else if (textEnabled && hasValidPhone && hasConsent && !isVerified) {
      statusEmoji.textContent = "⚠️";
      statusMessage.innerHTML =
        "Your phone number is not yet verified.<br />We will not send text notifications until verification succeeds. Use the button below to resend the verification text.";
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
      if (emailExpandBtn) emailExpandBtn.style.display = emailExpanded ? "none" : "inline-flex";
      if (emailCollapseBtn) emailCollapseBtn.style.display = emailExpanded ? "inline-flex" : "none";
    }

    if (textAccordion) {
      textAccordion.classList.toggle("expanded", textExpanded);
      if (textExpandBtn) textExpandBtn.style.display = textExpanded ? "none" : "inline-flex";
      if (textCollapseBtn) textCollapseBtn.style.display = textExpanded ? "inline-flex" : "none";
    }
  }

  function validateEmailSection(elements) {
    const email = (elements.email?.value ?? "").trim();
    const emailPrefChecked = Boolean(elements.emailPref?.checked);

    // Only require valid email when email_pref is checked.
    // When unchecked, email can be empty or filled; never block Submit for email.
    let emailBlocksSubmit = false;
    if (emailPrefChecked) {
      if (!email || !validateEmail(email)) {
        elements.email?.classList.add("is-invalid");
        emailBlocksSubmit = true;
      } else {
        elements.email?.classList.remove("is-invalid");
      }
    } else {
      elements.email?.classList.remove("is-invalid");
    }
    return emailBlocksSubmit;
  }

  function validateTextSection(elements) {
    // Only require valid phone (and consent) when text_pref is checked.
    let textBlocksSubmit = false;
    if (elements.textPref?.checked) {
      const phoneNumber = elements.phone?.value?.replace(/\D/g, "") ?? "";
      if (!phoneNumber || !validatePhoneNumber(phoneNumber)) {
        elements.phone?.classList.add("is-invalid");
        textBlocksSubmit = true;
      } else {
        elements.phone?.classList.remove("is-invalid");
      }
    } else {
      elements.phone?.classList.remove("is-invalid");
    }
    // Require text consent when text notifications are enabled
    if (elements.textPref?.checked && !elements.textConsent?.checked) textBlocksSubmit = true;
    return textBlocksSubmit;
  }

  function validateForm() {
    const refs = getFormRefs();
    if (!refs) return false;
    const { elements } = refs;

    const emailBlocksSubmit = validateEmailSection(elements);
    const textBlocksSubmit = validateTextSection(elements);

    updateEmailNotificationStatus();
    updateTextNotificationStatus();

    const hasChanges = hasFormChanges();
    const canSubmit = hasChanges && !emailBlocksSubmit && !textBlocksSubmit;
    if (elements.saveBtn) elements.saveBtn.disabled = !canSubmit;
    if (elements.cancelBtn) elements.cancelBtn.disabled = !hasChanges;
    updateFormStatus(hasChanges);

    return !emailBlocksSubmit && !textBlocksSubmit;
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

        const textNotificationStatus = document.getElementById("text-notification-status");
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
    const normalized = normalizeProfileData(profInfo);
    const refs = getFormRefs();
    if (!refs) return;

    const { form: profForm, elements } = refs;

    if (!ignoreAddingEventListeners) {
      setSavedProfileData(normalized);
    }

    elements.email.value = normalized.email;
    elements.phone.value = maskPhoneNumber(normalized.phone_number);
    elements.emailPref.checked = normalized.email_pref;
    elements.textPref.checked = normalized.text_pref;
    elements.noNotifications.checked = !normalized.email_pref && !normalized.text_pref;

    if (elements.textConsent) {
      elements.textConsent.checked = normalized.text_consent;
      elements.textConsent.disabled = !elements.textPref.checked;
    }

    updateAccordionVisibility(normalized.email_pref, true);

    const probValue = String(normalized.prob_pref);
    for (let radio of elements.probRadios || []) {
      radio.checked = radio.value === probValue;
      radio.disabled = elements.noNotifications.checked;
    }

    if (!ignoreAddingEventListeners) {
      profForm.addEventListener("input", onProfileFormChange);
      profForm.addEventListener("change", onProfileFormChange);
      elements.cancelBtn.addEventListener("click", cancelProfileFormChanges);
      elements.saveBtn.addEventListener("click", saveProfileFormChanges);
      elements.phone.addEventListener("input", (e) => {
        elements.phone.value = maskPhoneNumber(e.target.value);
      });
      elements.email.addEventListener("blur", () => {
        updateEmailNotificationStatus();
        validateForm();
      });
      elements.textConsent?.addEventListener("change", validateForm);
      if (elements.resendVerify) {
        elements.resendVerify.addEventListener("click", resendVerification);
      }
      setupAccordionTabs();
      setupExpandCollapseButtons();
    }

    updateEmailNotificationStatus();
    updateTextNotificationStatus();
    validateForm();
    updateVerificationButtonState();
  }

  function onProfileFormChange(e) {
    const form = e.target.form;
    if (!form) return;
    const emailInput = form.elements[FORM_IDS.email];
    // Don't touch DOM while typing in email (avoids bounce from helpText clear / validation UI)
    if (e.target === emailInput) return;

    const noNotificationsCheckbox = form.elements[FORM_IDS.noNotifications];
    const emailCheckbox = form.elements[FORM_IDS.emailPref];
    const textCheckbox = form.elements[FORM_IDS.textPref];
    const textConsentCheckbox = form.elements[FORM_IDS.textConsent];
    const probRadios = form.elements[FORM_IDS.probRadios];

    const helpText = document.getElementById("profile-form-help-text");
    if (helpText) {
      helpText.innerHTML = "";
      helpText.style.color = "";
    }

    if (e.target === noNotificationsCheckbox) {
      if (noNotificationsCheckbox.checked) {
        emailCheckbox.checked = textCheckbox.checked = false;
        if (textConsentCheckbox) textConsentCheckbox.checked = false;
      }
    } else if (e.target === emailCheckbox || e.target === textCheckbox) {
      if (e.target === textCheckbox && !textCheckbox.checked && textConsentCheckbox) {
        textConsentCheckbox.checked = false;
      }
      if (emailCheckbox.checked || textCheckbox.checked) {
        noNotificationsCheckbox.checked = false;
      } else {
        noNotificationsCheckbox.checked = true;
      }
    } else if (e.target === textConsentCheckbox && !textConsentCheckbox.checked) {
      // If the user unchecks consent while text notifications are on,
      // interpret that as turning off text notifications entirely.
      if (textCheckbox.checked) {
        textCheckbox.checked = false;
      }
      if (emailCheckbox.checked || textCheckbox.checked) {
        noNotificationsCheckbox.checked = false;
      } else {
        noNotificationsCheckbox.checked = true;
      }
    }

    if (e.target === emailCheckbox && emailCheckbox.checked) {
      const emailInput = form.elements[FORM_IDS.email];
      const currentEmail = emailInput.value.trim();
      const isPlaceholderOrEmpty =
        !currentEmail ||
        currentEmail === "you@example.com" ||
        currentEmail === "You@example.com" ||
        currentEmail.includes("example.com");
      const profileInfo = getProfileInfo();
      if (isPlaceholderOrEmpty && profileInfo && profileInfo.email) {
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

    if (textConsentCheckbox) {
      textConsentCheckbox.disabled = !textCheckbox.checked;
    }

    for (let radio of probRadios || []) {
      radio.disabled = noNotificationsCheckbox.checked;
    }

    updateEmailNotificationStatus();
    validateForm();
    updateVerificationButtonState();
  }

  function cancelProfileFormChanges() {
    initProfileForm(getProfileInfo(), true);
    validateForm();
  }

  async function resendVerification() {
    const resendVerify = document.getElementById(FORM_IDS.resendVerifyBtn);
    if (resendVerify) resendVerify.disabled = true;

    try {
      const current = getCurrentFormValues();
      const payload = {
        phone_number: current.phone_number || null,
        text_pref: current.text_pref,
        text_consent: current.text_consent,
      };
      const res = await authorizedFetch("/verify-phone/send", {
        method: "POST",
        headers: { "Content-Type": "application/json;charset=utf-8" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const savedRaw = getSavedProfileData();
        const saved = normalizeProfileData(savedRaw || {});
        saved.phone_verified = true;
        setSavedProfileData(saved);
        updateTextNotificationStatus();
        updateVerificationButtonState();
      } else {
        if (res.status === 429) {
          const errorMessage429 =
            "You have reached the maximum number of phone verification attempts for today. Please try again tomorrow.";
          if (resendVerify) {
            resendVerify.dataset.rateLimited = "true";
            resendVerify.disabled = true;
            resendVerify.style.display = "none";
          }
          const statusEmoji = document.getElementById("text-status-emoji");
          const statusMessage = document.getElementById("text-status-message");
          if (statusEmoji && statusMessage) {
            statusEmoji.textContent = "⚠️";
            statusMessage.textContent = errorMessage429;
          }
          // Do not change the main help text for 429; keep it focused on form changes.
        }
      }
    } catch (err) {
      console.error("Error sending verification SMS:", err);
      // Leave main form help text unchanged; errors are shown via console/text status.
    } finally {
      updateVerificationButtonState();
    }
  }

  async function saveProfileFormChanges() {
    const refs = getFormRefs();
    const helpText = document.getElementById("profile-form-help-text");
    if (!refs || !helpText) {
      console.error("Required form elements not found!");
      return;
    }

    if (!validateForm()) return;

    const current = getCurrentFormValues();
    const emailPref = refs.elements.emailPref.checked;
    const textPref = refs.elements.textPref.checked;
    const textConsentChecked = Boolean(refs.elements.textConsent?.checked);
    const selectedProb = getSelectedProb(refs.elements.probRadios);

    const savedRaw = getSavedProfileData();
    const saved = normalizeProfileData(savedRaw);
    const emailToSend = (current.email || "").trim() || "";
    // Do not clear phone number just because text_pref is off; only clear when the user
    // actually removes it. Always send the current digits (or null if empty).
    const phoneToSend = current.phone_number ? current.phone_number : null;

    const newProfileInfo = {
      email: emailToSend,
      phone_number: phoneToSend,
      service_provider_id: null,
      email_pref: emailPref,
      text_pref: textPref,
      prob_pref: selectedProb,
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
        setSavedProfileData(normalizeProfileData(profileInfo));

        // Detect whether we should send a verification SMS.
        // Two cases:
        // 1) User turns on text + consent with a phone number and has never been verified.
        // 2) User changes their phone number while text + consent are on (re-verify new number).
        const phoneChanged = current.phone_number !== saved.phone_number;
        const hasPhone = Boolean(current.phone_number);
        const shouldSendVerification =
          hasPhone && textPref && textConsentChecked && (!saved.phone_verified || phoneChanged);

        let message = "Changes saved successfully!";

        let verificationFailed = false;

        if (shouldSendVerification) {
          message +=
            " We will send a one-time text message to verify your phone number for alerts.";

          try {
            const payload = {
              phone_number: current.phone_number || null,
              text_pref: textPref,
              text_consent: textConsentChecked,
            };
            const verifyRes = await authorizedFetch("/verify-phone/send", {
              method: "POST",
              headers: { "Content-Type": "application/json;charset=utf-8" },
              body: JSON.stringify(payload),
            });
            if (verifyRes.ok) {
              const updatedProfile = await verifyRes.json().catch(() => null);
              if (updatedProfile && typeof updatedProfile === "object") {
                setSavedProfileData(normalizeProfileData(updatedProfile));
              } else {
                const savedNow = normalizeProfileData(getSavedProfileData() || {});
                savedNow.phone_verified = true;
                setSavedProfileData(savedNow);
              }
              updateTextNotificationStatus();
              updateVerificationButtonState();
            } else {
              verificationFailed = true;
              try {
                const json = await verifyRes.json();
                console.error("verify-phone/send failed:", json);
              } catch (e) {
                console.error("verify-phone/send failed with status", verifyRes.status);
              }
            }
          } catch (err) {
            console.error("Error sending verification SMS:", err);
            verificationFailed = true;
          }
        }

        if (verificationFailed) {
          message +=
            " However, we could not send a verification text right now. You can try again using the “Resend verification text” link below.";
        }

        helpText.innerHTML = message;
        updateVerificationButtonState();
      } else {
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const json = await res.json();
          helpText.style.color = "red";
          helpText.innerHTML = json.errors[0];
        } else {
          helpText.style.color = "red";
          helpText.innerHTML = "Server error occurred. Please refresh the page and try again.";
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
