"use strict";

export const PARTNER_SITE_DOMAINS = {
  HB: "howsthebeach.org",
  WC: "webcoos.srv.axds.co",
  VB: "visitbeaches.org",
};

export const MAP_CENTER = [-81.5158, 27.6648];
export const INITIAL_ZOOM = 7;
export const CMU_LYR_NAME = "cmuLyr";
export const PARTNER_APP_LYR_NAME = "partnerAppLyr";
export const LEASE_PNT_LYR_NAME = "leasePntLyr";

// The path to the growing unit boundaries file.
export const GROWING_UNIT_BOUNDS_PATH = "static/fl_cmus_boundary.geojson";
export const PARTNER_APP_POINTS_PATH = "static/partner_sites_fl.geojson";
// Icons
export const HOME_ICON = "./static/img/map/home.png";
export const HOWS_THE_BEACH_ICON = "./static/img/map/hb.png";
export const CAMERA_ICON = "./static/img/map/camera.png";
export const VISIT_BEACHES_ICON = "./static/img/map/vb.png";

// Popup contents
export const HB_POPUP = {
  title: "HOW'S THE BEACH?",
  iconUrl: "./static/img/map/howsthebeach-popup.png",
  hpUrl: "https://howsthebeach.org/",
};

export const WC_POPUP = {
  title: "Web Camera Observation Network",
  iconUrl: "./static/img/map/secoora-popup.png",
  hpUrl: "https://secoora.org/",
};

export const VB_POPUP = {
  title: "Beach Conditions Reporting System",
  iconUrl: "./static/img/map/mote-popup.png",
  hpUrl: "https://visitbeaches.org/",
};

export const COLOR_PALLET = {
  COLOR_NULL: "transparent",
  COLOR_VERY_LOW: "#4eb265",
  COLOR_LOW: "#fecc5c",
  COLOR_MODERATE: "#fd8d3c",
  COLOR_HIGH: "#e31a1c",
  COLOR_VERY_HIGH: "rgba(139, 0, 0, 0.7)",
};

/** The text and colors used for the legend. */
export const LEGEND_SCALE = [
  { text: "No data", color: COLOR_PALLET.COLOR_NULL },
  { text: "Very Low", color: COLOR_PALLET.COLOR_VERY_LOW },
  { text: "Low", color: COLOR_PALLET.COLOR_LOW },
  { text: "Moderate", color: COLOR_PALLET.COLOR_MODERATE },
  { text: "High", color: COLOR_PALLET.COLOR_HIGH },
  { text: "Very High", color: COLOR_PALLET.COLOR_VERY_HIGH },
];

export const MARKER_SVG =
  '<svg id="marker" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="30px" height="30px" viewBox="0 0 30 30" enable-background="new 0 0 30 30" xml:space="preserve">' +
  '<path fill="white" stroke="black" d="M22.906,10.438c0,4.367-6.281,14.312-7.906,17.031c-1.719-2.75-7.906-12.665-7.906-17.031S10.634,2.531,15,2.531S22.906,6.071,22.906,10.438z"/>' +
  '<circle fill="black" cx="15" cy="10.677" r="3.291"/></svg>';
