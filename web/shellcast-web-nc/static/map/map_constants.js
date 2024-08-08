"use strict";

export const PARTNER_SITE_DOMAINS = {
  HB: "howsthebeach.org",
  WC: "webcoos.srv.axds.co",
  VB: "visitbeaches.org",
};

export const MAP_CENTER = [-76.315151, 35.007934];
export const INITIAL_ZOOM = 8;
export const CMU_LYR_NAME = "cmuLyr";
export const PARTNER_APP_LYR_NAME = "partnerAppLyr";
export const LEASE_PNT_LYR_NAME = "leasePntLyr";

// The path to the growing unit boundaries file.
export const GROWING_UNIT_BOUNDS_PATH = "static/cmu_bounds.geojson";
export const PARTNER_APP_POINTS_PATH = "static/partner_sites_nc.geojson";

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
