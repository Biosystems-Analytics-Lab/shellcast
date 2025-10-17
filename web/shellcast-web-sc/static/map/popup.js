"use strict";
import {
  HB_POPUP,
  PARTNER_SITE_DOMAINS,
  VB_POPUP,
  WC_POPUP,
} from "./map_constants.js";
import { getDomainName } from "./utils.js";

// Elements that make up the popup.
const POPUP_CONTAINER_ELE = document.getElementById("popup");
export const POPUP_CONTENT_ELE = document.getElementById("popup-content");

export function createShellCastPopupLayer() {
  return new ol.Overlay({
    element: POPUP_CONTAINER_ELE,
    autoPan: {
      animation: {
        duration: 250,
      },
    },
  });
}

export function popupContent(title, siteName, iconUrl, text) {
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

export function partnerAppLyrPopupContent(feature) {
  const features = feature.get("features");
  if (features.length === 1) {
    console.log(features);
    let domainName = getDomainName(features[0].get("url"));
    let siteName = features[0].get("site_name");
    let url = features[0].get("url");
    let contentText = "";
    let title = "";
    let iconUrl = "";
    let hpUrl = "";
    if (domainName === PARTNER_SITE_DOMAINS.HB) {
      title = HB_POPUP.title;
      iconUrl = HB_POPUP.iconUrl;
      hpUrl = HB_POPUP.hpUrl;
      contentText = `<p class="small-font">Headed to the beach? Click <span><a href="${url}" target="_blank">here</a>
                      </span> to see if the water quality is healthy before heading in.
                      <br><span><a class="text-decoration-none" href="${hpUrl}" target="_blank">${hpUrl}</a></span></br>
                      </p>`;
    } else if (domainName === PARTNER_SITE_DOMAINS.WC) {
      title = WC_POPUP.title;
      iconUrl = WC_POPUP.iconUrl;
      hpUrl = WC_POPUP.hpUrl;
      contentText = `<p class="small-font">Click <span><a href="${url}" target="_blank">here</a></span> to view the
                      Web Camera at this location. This will open the WebCOOS camera site in a new tab.
                      <br><span><a class="text-decoration-none" href="${hpUrl}" target="_blank">${hpUrl}</a></span>
                      </p>`;
    } else if (domainName === PARTNER_SITE_DOMAINS.VB) {
      title = VB_POPUP.title;
      iconUrl = VB_POPUP.iconUrl;
      hpUrl = VB_POPUP.hpUrl;
      contentText = `<p class="small-font">Click <span><a href="${url}" target="_blank">here</a></span> to view the
                        Beach Condition Reporting System at this location. This will open the Mote Marine Laboratory
                        site in a new tab.
                        <br><span><a class="text-decoration-none" href="${hpUrl}" target="_blank">${hpUrl}</a></span>
                        </p>`;
    }
    POPUP_CONTENT_ELE.innerHTML = popupContent(
      title,
      siteName,
      iconUrl,
      contentText,
    );
  }
}
