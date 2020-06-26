'use strict';

// Firebase configuration
const FIREBASE_CONFIG = {
  apiKey: 'AIzaSyBRh_l-CqS8dz8QcpdLk8QRpY_aoMLQBj8',
  authDomain: 'ncsu-shellcast.firebaseapp.com',
  databaseURL: 'https://ncsu-shellcast.firebaseio.com',
  projectId: 'ncsu-shellcast',
  storageBucket: 'ncsu-shellcast.appspot.com',
  messagingSenderId: '770417321789',
  appId: '1:770417321789:web:685ecb339be636f1140754'
};

/**
 * Displays the UI for a signed in user.
 * @param {!firebase.User} user
 */
function handleNavbarSignedIn(user) {
  // change the dropdown menu's text
  document.getElementById('account-dropdown').textContent = user.email;

  // remove the "Sign in" option from the dropdown menu
  document.getElementById('account-dropdown-sign-in').style.display = 'none';
  // add the "Manage notifications" and "Sign out" options to the dropdown menu
  document.getElementById('account-dropdown-notifications').style.display = 'block';
  document.getElementById('account-dropdown-sign-out').style.display = 'block';
};

/**
 * Displays the UI for a signed out user.
 */
function handleNavbarSignedOut() {
  // change the dropdown menu's text
  document.getElementById('account-dropdown').textContent = 'Account';

  // add the "Sign in" option to the dropdown menu
  document.getElementById('account-dropdown-sign-in').style.display = 'block';
  // remove the "Manage notifications" and "Sign out" options from the dropdown menu
  document.getElementById('account-dropdown-notifications').style.display = 'none';
  document.getElementById('account-dropdown-sign-out').style.display = 'none';
};

async function signOut() {
  await firebase.auth().signOut();
  location.reload();
}

(async () => {
  // initialize Firebase
  firebase.initializeApp(FIREBASE_CONFIG);
  
  // if the navigation bar exists
  if (document.getElementById('navigation-bar')) {
    // update elements based on auth state
    firebase.auth().onAuthStateChanged((user) => {
      user ? handleNavbarSignedIn(user) : handleNavbarSignedOut();
    });

    // init event listeners
    document.getElementById('account-dropdown-sign-out').addEventListener('click', signOut);

    // update sign-in url
    document.getElementById('account-dropdown-sign-in').href = `/signin?mode=select&signInSuccessUrl=${window.location.pathname}`;
  }
})();

async function authorizedFetch(url, options={}) {
  // request the token which may potentially be expired
  // (don't get an updated token just yet because you are unnecessarily refreshing tokens with sign-in service providers and this might drive you over your daily quotas)
  // TODO actually verify the statement above; it may no longer apply?!?!
  const userIdToken = await firebase.auth().currentUser.getIdToken(false);
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
    const userIdToken = await firebase.auth().currentUser.getIdToken(false);
    // add the auth token to the headers
    options.headers.Authorization = userIdToken;
    // resend the request
    request = fetch(url, options);
  }

  return request;
}
