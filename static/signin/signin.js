const FIREBASE_UI_CONFIG = {
  signInSuccessUrl: '/',
  callbacks: {
    // signInSuccessWithAuthResult: (authResult, redirectUrl) => {},
    signInFailure: (error) => {
      console.log('Failure during sign in');
      console.log(error);
    }
  },
  signInOptions: [
    firebase.auth.GoogleAuthProvider.PROVIDER_ID,
    // firebase.auth.FacebookAuthProvider.PROVIDER_ID,
    firebase.auth.TwitterAuthProvider.PROVIDER_ID
  ],
  credentialHelper: firebaseui.auth.CredentialHelper.NONE
};

const ui = new firebaseui.auth.AuthUI(firebase.auth());
ui.disableAutoSignIn();
ui.start('#firebaseui-container', FIREBASE_UI_CONFIG);
