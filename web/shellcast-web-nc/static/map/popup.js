"use strict";
import {getDomainName, partnerSiteDomains} from "./utils.js";

// Elements that make up the popup.
const popupContainer = document.getElementById("popup");
const popupHtmlContent = document.getElementById("popup-content");

function createShellCastPopupLayer() {
  return new ol.Overlay({
    element: popupContainer,
    autoPan: {
      animation: {
        duration: 250,
      },
    },
  });
}

function popupContent(title, siteName, iconUrl, text) {
  return `<div id="closable-card" class="card mb-3 popup-background" style="width:350px">
      <div class="card-header container-fluid">
        <div class="row">
          <div class="col-10 text-center" style="color: white;"><h6>${title}</h6></div>
          <div class="col-2 float-right">
            <button data-dismiss="alert" data-target="#closable-card" type="button" class="close" aria-label="Close">
              <span aria-hidden="true"" ><h6>&times;</h6></span>
            </button>
          </div>
        </div> 
      </div>
      <div class="card-body no-padding">
        <div class="row g-0 no-margin">
          <div class="col-md-4 popup-logo">
            <img src="${iconUrl}" class="img-fluid card-image" alt="...">
          </div>
          <div class="col-md-8 popup-content">
            <h5 class="card-title text-center">${siteName}</h5>
            <p class="card-text">${text}</p>
          </div>
        </div>
      </div>
    </div>`;
}

function partnerAppLyrPopupContent(feature) {
  const features = feature.get("features");
  if (features.length === 1) {
    let domainName = getDomainName(features[0].get("url"));
    let siteName = features[0].get("site_name");
    let url = features[0].get("url");
    let contentText = "";
    let title = "";
    let iconUrl = "";
    let hpUrl = "";
    if (domainName === partnerSiteDomains.HB) {
      title = "HOW'S THE BEACH?";
      iconUrl = "./static/img/map/howsthebeach-popup.png";
      hpUrl = "https://howsthebeach.org/";
      contentText = `<p class="small-font">Headed to the beach? Click <span><a href="${url}" target="_blank">here</a>
                      </span> to see if the water quality is healthy before heading in.
                      <br><span><a class="text-decoration-none" href="${hpUrl}" target="_blank">${hpUrl}</a></span></br>
                      </p>`;
    } else if (domainName === partnerSiteDomains.WC) {
      title = "Web Camera Observation Network";
      iconUrl = "./static/img/map/secoora-popup.png";
      hpUrl = "https://secoora.org/";
      contentText = `<p class="small-font">Click <span><a href="${url}" target="_blank">here</a></span> to view the 
                      Web Camera at this location. This will open the WebCOOS camera site in a new tab.
                      <br><span><a class="text-decoration-none" href="${hpUrl}" target="_blank">${hpUrl}</a></span>
                      </p>`;
    } else if (domainName === partnerSiteDomains.VB) {
      title = "Beach Conditions Reporting System";
      iconUrl = "./static/img/map/mote-popup.png";
      hpUrl = "https://visitbeaches.org/";
      contentText = `<p class="small-font">Click <span><a href="${url}" target="_blank">here</a></span> to view the 
                        Beach Condition Monitoring System at this location. This will open the Mote Marine Laboratory 
                        site in a new tab.
                        <br><span><a class="text-decoration-none" href="${hpUrl}" target="_blank">${hpUrl}</a></span>
                        </p>`;
    }
    popupHtmlContent.innerHTML = popupContent(
      title,
      siteName,
      iconUrl,
      contentText,
    );
  }
}

export {
  createShellCastPopupLayer,
  partnerAppLyrPopupContent,
  popupContent,
  popupHtmlContent,
};
