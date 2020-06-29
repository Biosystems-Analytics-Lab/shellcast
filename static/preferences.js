'use strict';

/**
 * Displays the UI for a signed in user.
 * @param {!firebase.User} user
 */
function handleSignedInUser(user) {
  document.getElementById('user-signed-in').style.display = 'block';
  document.getElementById('user-signed-out').style.display = 'none';
};

/**
 * Displays the UI for a signed out user.
 */
function handleSignedOutUser() {
  document.getElementById('user-signed-in').style.display = 'none';
  document.getElementById('user-signed-out').style.display = 'block';
};

async function testBtn() {
  // request the token which may potentially be expired
  // (don't get an updated token just yet because you are unnecessarily refreshing tokens with sign-in service providers and this might drive you over your daily quotas)
  // TODO actually verify the statement above; it may no longer apply?!?!
  const userIdToken = await firebase.auth().currentUser.getIdToken(false);
  // send the request
  let result = await fetch('/userInfo', {
    headers: {
      'Authorization': userIdToken
    }
  });
  let json = await result.json();
  // if the response says that the token expired
  if (result.status === 401 /*&& json.message === 'Token expired'*/) {
    // get an updated token
    const userIdToken = await firebase.auth().currentUser.getIdToken(false);
    // resend the request
    result = await fetch('/userInfo', {
      headers: {
        'Authorization': userIdToken
      }
    });
    json = await result.json();
  }
  console.log(json);
}

(async () => {
  // change UI based on auth state
  firebase.auth().onAuthStateChanged((user) => {
    user ? handleSignedInUser(user) : handleSignedOutUser();
  });
})();
