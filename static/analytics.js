/* Consent-gated Google Analytics 4.
 * Nothing is requested from Google until the visitor clicks Accept.
 * The choice is stored in localStorage under "analytics_consent".
 * Every storage and cookie call is wrapped so the site works if they fail.
 */
(function () {
  "use strict";

  var id = document.body.getAttribute("data-ga-id");
  if (!id) return;

  var KEY = "analytics_consent";
  var banner = document.getElementById("consent-banner");

  function readChoice() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }

  function saveChoice(value) {
    try { window.localStorage.setItem(KEY, value); } catch (e) { /* ignore */ }
  }

  function showBanner() { if (banner) banner.hidden = false; }
  function hideBanner() { if (banner) banner.hidden = true; }

  function loadAnalytics() {
    window["ga-disable-" + id] = false;
    if (window.__gaLoaded) return;
    window.__gaLoaded = true;

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", id);

    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
    document.head.appendChild(script);
  }

  function clearAnalyticsCookies() {
    try {
      var host = window.location.hostname;
      var parts = host.split(".");
      var domains = [host, "." + host];
      if (parts.length > 2) domains.push("." + parts.slice(-2).join("."));
      document.cookie.split(";").forEach(function (entry) {
        var name = entry.split("=")[0].trim();
        if (name.indexOf("_ga") !== 0) return;
        domains.forEach(function (domain) {
          document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=" + domain;
        });
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
      });
    } catch (e) { /* ignore */ }
  }

  function accept() {
    saveChoice("granted");
    hideBanner();
    loadAnalytics();
  }

  function decline() {
    saveChoice("denied");
    hideBanner();
    window["ga-disable-" + id] = true;
    clearAnalyticsCookies();
  }

  var acceptButton = document.getElementById("consent-accept");
  var declineButton = document.getElementById("consent-decline");
  var reopenButton = document.getElementById("consent-reopen");
  if (acceptButton) acceptButton.addEventListener("click", accept);
  if (declineButton) declineButton.addEventListener("click", decline);
  if (reopenButton) reopenButton.addEventListener("click", showBanner);

  var choice = readChoice();
  if (choice === "granted") {
    loadAnalytics();
  } else if (choice === "denied") {
    window["ga-disable-" + id] = true;
  } else {
    showBanner();
  }
})();
