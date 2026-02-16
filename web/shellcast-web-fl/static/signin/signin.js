"use strict";
import {
  GoogleAuthProvider,
  signInWithPopup,
} from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";
import { auth } from "../common/js/common.js";

document
  .getElementById("google-btn")
  .addEventListener("click", async (event) => {
    event.preventDefault();
    if (!auth.currentUser) {
      const provider = new GoogleAuthProvider();

      signInWithPopup(auth, provider)
        .then((result) => {
          if (result.user) {
            window.location.href = "/map";
          }
        })
        .catch((error) => {
          // TODO: handle error properly (e.g., display error message in modal)
          alert(error.message);
          // // Handle Errors here.
          // const errorCode = error.code;
          // const errorMessage = error.message;
          // const email = error.customData.email;
        });
    }
  });
