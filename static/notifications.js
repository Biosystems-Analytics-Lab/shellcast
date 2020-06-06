'use strict';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBRh_l-CqS8dz8QcpdLk8QRpY_aoMLQBj8",
  authDomain: "ncsu-shellcast.firebaseapp.com",
  databaseURL: "https://ncsu-shellcast.firebaseio.com",
  projectId: "ncsu-shellcast",
  storageBucket: "ncsu-shellcast.appspot.com",
  messagingSenderId: "770417321789",
  appId: "1:770417321789:web:685ecb339be636f1140754"
};

const firebaseUIConfig = {
  callbacks: {
    signInSuccessWithAuthResult: async (authResult) => {
      if (authResult.user) {
        handleSignedInUser(authResult.user);
      }
      if (authResult.additionalUserInfo.isNewUser) {
        console.log('This is a new user, so send a request to the backend to add this user to the db.');
        console.log(authResult.user);
        const userIdToken = await authResult.user.getIdToken(true);
        console.log(userIdToken);
      } else {
        console.log('This isn\'t a new user, so we don\'t have to do anything.')
      }
      return false;
    },
    signInFailure: (error) => {
      console.log('Failure during sign in');
      console.log(error);
    }
  },
  signInOptions: [
    {
      provider: firebase.auth.EmailAuthProvider.PROVIDER_ID,
      requireDisplayName: false
    },
    firebase.auth.GoogleAuthProvider.PROVIDER_ID,
    firebase.auth.FacebookAuthProvider.PROVIDER_ID
  ],
  credentialHelper: firebaseui.auth.CredentialHelper.NONE
};

/**
 * Displays the UI for a signed in user.
 * @param {!firebase.User} user
 */
function handleSignedInUser(user) {
  document.getElementById('user-signed-in').style.display = 'block';
  document.getElementById('user-signed-out').style.display = 'none';

  // document.getElementById('name').textContent = user.displayName;
  // document.getElementById('email').textContent = user.email;
  // document.getElementById('phone').textContent = user.phoneNumber;
  // if (user.photoURL) {
  //   var photoURL = user.photoURL;
  //   // Append size to the photo URL for Google hosted images to avoid requesting
  //   // the image with its original resolution (using more bandwidth than needed)
  //   // when it is going to be presented in smaller size.
  //   if ((photoURL.indexOf('googleusercontent.com') != -1) ||
  //       (photoURL.indexOf('ggpht.com') != -1)) {
  //     photoURL = photoURL + '?sz=' +
  //         document.getElementById('photo').clientHeight;
  //   }
  //   document.getElementById('photo').src = photoURL;
  //   document.getElementById('photo').style.display = 'block';
  // } else {
  //   document.getElementById('photo').style.display = 'none';
  // }
};


/**
 * Displays the UI for a signed out user.
 */
function handleSignedOutUser() {
  document.getElementById('user-signed-in').style.display = 'none';
  document.getElementById('user-signed-out').style.display = 'block';
  ui.start('#firebaseui-container', firebaseUIConfig);
};

async function signOut() {
  return await firebase.auth().signOut();
}

function initEventListeners() {
  // attach event listeners
  document.getElementById('sign-out').addEventListener('click', signOut);
}

let ui;
(async () => {
  // initialize Firebase
  firebase.initializeApp(firebaseConfig);
  // initialize the FirebaseUI Widget using Firebase
  ui = new firebaseui.auth.AuthUI(firebase.auth());
  // Disable auto-sign in.
  ui.disableAutoSignIn();

  // Listen to change in auth state so it displays the correct UI for when
  // the user is signed in or not.
  firebase.auth().onAuthStateChanged((user) => {
    user ? handleSignedInUser(user) : handleSignedOutUser();
  });
})();

window.addEventListener('load', initEventListeners);
