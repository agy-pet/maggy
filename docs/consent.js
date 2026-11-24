// Regional analytics consent banner (Google Consent Mode v2).
// Defaults in <head> set analytics_storage to 'denied' for EEA + UK + CH
// via Google's region parameter. This script shows the banner to visitors
// in those regions (detected locally via IANA timezone, with zero network
// calls) and lets any visitor update their choice via [data-consent-open].
(() => {
  "use strict";

  const STORAGE_KEY = "maggy.consent";

  // IANA timezones covering EEA (27 EU + IS, LI, NO), UK (GB), and Switzerland (CH).
  const CONSENT_TIMEZONES = new Set([
    "Arctic/Longyearbyen",
    "Asia/Nicosia",
    "Atlantic/Azores",
    "Atlantic/Canary",
    "Atlantic/Faroe",
    "Atlantic/Madeira",
    "Atlantic/Reykjavik",
    "CET",
    "EET",
    "Eire",
    "Europe/Amsterdam",
    "Europe/Andorra",
    "Europe/Athens",
    "Europe/Belfast",
    "Europe/Berlin",
    "Europe/Bratislava",
    "Europe/Brussels",
    "Europe/Bucharest",
    "Europe/Budapest",
    "Europe/Busingen",
    "Europe/Copenhagen",
    "Europe/Dublin",
    "Europe/Gibraltar",
    "Europe/Guernsey",
    "Europe/Helsinki",
    "Europe/Isle_of_Man",
    "Europe/Jersey",
    "Europe/Lisbon",
    "Europe/Ljubljana",
    "Europe/London",
    "Europe/Luxembourg",
    "Europe/Madrid",
    "Europe/Malta",
    "Europe/Mariehamn",
    "Europe/Monaco",
    "Europe/Nicosia",
    "Europe/Oslo",
    "Europe/Paris",
    "Europe/Prague",
    "Europe/Riga",
    "Europe/Rome",
    "Europe/San_Marino",
    "Europe/Sofia",
    "Europe/Stockholm",
    "Europe/Tallinn",
    "Europe/Vaduz",
    "Europe/Vatican",
    "Europe/Vienna",
    "Europe/Vilnius",
    "Europe/Warsaw",
    "Europe/Zagreb",
    "Europe/Zurich",
    "GB",
    "GB-Eire",
    "Iceland",
    "MET",
    "Poland",
    "Portugal",
    "WET",
  ]);

  function getSavedConsent() {
    try {
      const val = localStorage.getItem(STORAGE_KEY);
      return val === "granted" || val === "denied" ? val : null;
    } catch {
      return null;
    }
  }

  function saveConsent(choice) {
    try {
      localStorage.setItem(STORAGE_KEY, choice);
    } catch {
      // Storage unavailable (private mode / blocked storage); still update gtag for this session.
    }
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", {
        analytics_storage: choice,
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
      });
    }
  }

  function isConsentRegion() {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      return Boolean(tz && CONSENT_TIMEZONES.has(tz));
    } catch {
      return false;
    }
  }

  function init() {
    const banner = document.getElementById("consent-banner");
    if (!banner) return;

    const show = () => {
      banner.hidden = false;
    };
    const hide = () => {
      banner.hidden = true;
    };

    banner.querySelectorAll("[data-consent]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const choice = btn.dataset.consent === "granted" ? "granted" : "denied";
        saveConsent(choice);
        hide();
      });
    });

    const inRegion = isConsentRegion();
    const saved = getSavedConsent();

    document.querySelectorAll("[data-consent-open]").forEach((trigger) => {
      if (trigger.hidden && (inRegion || saved)) {
        trigger.hidden = false;
      }
      trigger.addEventListener("click", (e) => {
        e.preventDefault();
        show();
        const firstBtn = banner.querySelector("[data-consent]");
        if (firstBtn) firstBtn.focus();
      });
    });

    // Show automatically only in consent-requiring regions when no choice is saved
    // and Global Privacy Control isn't already opting the user out.
    if (!saved && !navigator.globalPrivacyControl && inRegion) {
      show();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
