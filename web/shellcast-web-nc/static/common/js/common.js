"use strict";
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  signOut,
} from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";

// Firebase configuration
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyA8f1ZWHYObRaLVFHc7KCqgT3FGhu_qO90",
  authDomain: "ncsu-shellcast.firebaseapp.com",
  databaseURL: "https://ncsu-shellcast.firebaseio.com",
  projectId: "ncsu-shellcast",
  storageBucket: "ncsu-shellcast.appspot.com",
  messagingSenderId: "770417321789",
  appId: "1:770417321789:web:685ecb339be636f1140754",
};

const app = initializeApp(FIREBASE_CONFIG);
const auth = getAuth(app);

/**
 * Displays the UI for a signed in user.
 * @param {!firebase.User} user
 */
function handleNavbarSignedIn(user) {
  // hide the "Sign In" link
  document.getElementById("account-sign-in").style.display = "none";

  // show the account dropdown menu
  document.getElementById("account-dropdown-div").style.display = "block";

  // change the dropdown menu's text
  document.getElementById("account-dropdown").textContent = user.email;
}

/**
 * Displays the UI for a signed out user.
 */
function handleNavbarSignedOut() {
  // show the "Sign In" link
  document.getElementById("account-sign-in").style.display = "block";

  // hide the account dropdown menu
  document.getElementById("account-dropdown-div").style.display = "none";

  // change the dropdown menu's text
  document.getElementById("account-dropdown").textContent = "Account";
}

async function authorizedFetch(url, options = {}) {
  // request the token which may potentially be expired
  // (don't get an updated token just yet because you are unnecessarily refreshing tokens with sign-in service
  // providers and this might drive you over your daily quotas)
  // TODO actually verify the statement above; it may no longer apply?!?!
  const userIdToken = await auth.currentUser.getIdToken(false);
  // add the auth token to the headers
  if (!options.headers) {
    options.headers = {};
  }
  options.headers.Authorization = userIdToken;
  // send the request
  let request = fetch(url, options);
  let result = await request;
  // if the response says that the token expired
  if (result.status === 401 /*&& json.message === 'Token expired'*/) {
    // get an updated token
    const userIdToken = await auth.currentUser.getIdToken(false);
    // add the auth token to the headers
    options.headers.Authorization = userIdToken;
    // resend the request
    request = fetch(url, options);
  }

  return request;
}

(async () => {
  // if the navigation bar exists
  if (document.getElementById("navigation-bar")) {
    // update elements based on auth state
    onAuthStateChanged(auth, (user) => {
      user ? handleNavbarSignedIn(user) : handleNavbarSignedOut();
    });

    // init event listeners
    document.getElementById("account-dropdown-sign-out").addEventListener("click", async () => {
      await signOut(auth);
      location.reload();
    });

    // update sign-in url
    document.getElementById("account-sign-in").href =
      `/signin?mode=select&signInSuccessUrl=${window.location.pathname}`;
  }
})();

export { authorizedFetch, auth };
