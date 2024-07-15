"use strict";
import { auth } from "../common/common.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";

import {
  createCmuGeoJsonSource,
  getBoundaryStyle,
  getGeoJsonAddProbs,
  getGrowingUnitData,
  getLeaseData,
  getPartnerAppStyle,
  getPartnerSitesSourceData,
  handleUndef,
  markerSvg,
  partnerAppLyrLegend,
} from "./utils.js";
import { createDaySelector, ShellCastLegend } from "./legends-dayselector.js";
import {
  initGrowingUnitTable,
  initLeaseTable,
  setTableSearchBoxes,
} from "./table.js";
import {
  createShellCastPopupLayer,
  partnerAppLyrPopupContent,
  popupContent,
  popupHtmlContent,
} from "./popup.js";

const shellCastLegend = new ShellCastLegend();
/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = "closure-map";
const DISCLAIMER_MODAL_ID = "disclaimer-privacy-modal";

const CMU_LYR_NAME = "cmuLyr";
const PARTNER_APP_LYR_NAME = "partnerAppLyr";
const LEASE_PNT_LYR_NAME = "leasePntLyr";

/** Options for the map. */
const mapCenter = [-76.315151, 35.007934];
// OSM humanitarian base layer
let osmHumanitarianBaseLyr;
// a reference to the Google map object
let map;
// CMU layer created from GeoJson
let cmuLyr;
// Partner app layer
let partnerLyr;
// CMU closure probability popup overlay
let popupLyr;

function createCmuLayer(cmuGeoJsonSource) {
  return new ol.layer.Vector({
    title: "CMU",
    name: CMU_LYR_NAME,
    opacity: 0.7,
    source: cmuGeoJsonSource,
    extent: cmuGeoJsonSource.getExtent(),
    style: function (feature) {
      return getBoundaryStyle(feature, 1);
    },
  });
}

function createPartnerAppLayer(sourceData) {
  return new ol.layer.Vector({
    name: PARTNER_APP_LYR_NAME,
    source: sourceData,
    style: (feature) => {
      return getPartnerAppStyle(feature);
    },
  });
}

function partnerLegendCheckbox() {
  document
    .getElementById("partner-legend")
    .addEventListener("change", function () {
      let ul = document.getElementById("partner-lyr-ul");
      let isVisible = partnerLyr.getVisible();
      if (this.checked) {
        if (!isVisible) {
          partnerLyr.setVisible(true);
          ul.style.display = "block";
        }
      } else {
        partnerLyr.setVisible(false);
        ul.style.display = "none";
      }
    });
}

/**
 * Set CMU polygon layer symbol style based on "prob_{day}d_perc" value.
 * @param day
 */
export function setCmuPolyStyleByDay(day) {
  cmuLyr.setStyle((feature) => {
    return getBoundaryStyle(feature, day);
  });
}

function setBoundingBoxMapExtent() {
  cmuLyr.getSource().once("change", function () {
    map.getView().fit(cmuLyr.getSource().getExtent());
  });
}

function createBaseLayer() {
  return new ol.layer.Tile({
    source: new ol.source.OSM({
      source: "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    }),
  });
}

/**
 * Create map.
 * @param growingUnitData
 * @returns {Promise<void>}
 */
async function initMap(growingUnitData) {
  const mapEl = document.getElementById(MAP_EL_ID);
  const cmuGeoJson = await getGeoJsonAddProbs(growingUnitData);
  // console.log(cmuGeoJson);
  const cmuGeoJsonSource = createCmuGeoJsonSource(cmuGeoJson);
  const partnerSitesSource = await getPartnerSitesSourceData();

  cmuLyr = createCmuLayer(cmuGeoJsonSource);
  partnerLyr = createPartnerAppLayer(partnerSitesSource);
  osmHumanitarianBaseLyr = createBaseLayer();
  setBoundingBoxMapExtent();

  popupLyr = createShellCastPopupLayer();

  map = new ol.Map({
    target: mapEl,
    layers: [osmHumanitarianBaseLyr, cmuLyr, partnerLyr],
    overlays: [popupLyr],
    view: new ol.View({
      center: ol.proj.fromLonLat(mapCenter),
      zoom: 8,
    }),
  }); // # Set map
  const legendLeft = shellCastLegend.create();
  const legendPanel = new ol.control.Control({
    element: legendLeft,
  });
  map.addControl(legendPanel); // #8

  // ================== Add day selector ==================
  const daySelector = createDaySelector();
  let daySelectorPanel = new ol.control.Control({
    element: daySelector,
  });
  map.addControl(daySelectorPanel);

  // ================== Add partner app legend ==================
  const partnerAppLegendControl = new ol.control.Control({
    element: partnerAppLyrLegend,
  });
  map.addControl(partnerAppLegendControl);
  partnerLegendCheckbox();

  // ================== Add popup event ==================
  map.on("singleclick", function (evt) {
    let coordinate = evt.coordinate;
    let lyrName;
    const feature = map.forEachFeatureAtPixel(
      evt.pixel,
      function (feature, layer) {
        if (layer) {
          lyrName = layer.get("name");
        }
        return feature;
      },
    );
    if (feature) {
      if (lyrName === PARTNER_APP_LYR_NAME) {
        partnerAppLyrPopupContent(feature);
      } else if (lyrName === CMU_LYR_NAME) {
        let title = "Growing Unit Closure Probability";
        let iconUrl = "static/img/map/shellcast-popup.png";
        let siteName = feature.get("cmu_name");
        let text = `<p>
                <b>Today:</b> ${handleUndef(feature.get("prob_1d_perc"))}
                <br><b>Tomorrow:</b> ${handleUndef(feature.get("prob_2d_perc"))}
                <br><b>In 2 days:</b> ${handleUndef(feature.get("prob_3d_perc"))}
                </p>`;
        popupHtmlContent.innerHTML = popupContent(
          title,
          siteName,
          iconUrl,
          text,
        );
      }
      popupLyr.setPosition(coordinate);
    } else {
      popupLyr.setPosition(undefined);
    }
  });
}

/**
 * Create point layer for user's registered lease locations.
 * @param leaseData
 * @returns {Promise<*>}
 */
async function createLeasePointFeatures(leaseData) {
  let features = leaseData.map((item) => {
    let longitude = item.longitude,
      latitude = item.latitude,
      iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([longitude, latitude])),
        lease_id: item.lease_id,
        prob_1d_perc: item.prob_1d_perc,
        prob_2d_perc: item.prob_2d_perc,
        prob_3d_perc: item.prob_3d_perc,
        type: "Point",
      }),
      iconStyle = new ol.style.Style(
        /** @type {olx.style.IconOptions} */ {
          image: new ol.style.Icon({
            anchor: [0.5, 1],
            anchorXUnits: "fraction",
            anchorYUnits: "fraction",
            // src: 'https://openlayers.org/en/latest/examples/data/icon.png'
            src: "data:image/svg+xml," + encodeURI(markerSvg),
            scale: 2,
            imgSize: [26, 26],
          }),
        },
      );

    iconFeature.setStyle(iconStyle);
    return iconFeature;
  });
  return features;
}

/**
 * Add users lease point layer to the map and add popup event listener.
 * @param pointFeatures
 */
function addLeaseDataToMap(pointFeatures) {
  let leasePntSource = new ol.source.Vector({
    features: pointFeatures, //add an array of features
  });

  let leasePntLyr = new ol.layer.Vector({
    source: leasePntSource,
  });
  map.addLayer(leasePntLyr);

  // Add mouseover event for popup
  map.on("pointermove", function (evt) {
    let coordinate = evt.coordinate;
    let lyrName;
    const feature = map.forEachFeatureAtPixel(
      evt.pixel,
      function (feature, layer) {
        if (layer) {
          lyrName = layer.get("name");
        }
        return feature;
      },
    );
    if (lyrName === LEASE_PNT_LYR_NAME) {
      let title = "Growing Unit Closure Probability";
      let iconUrl = "static/img/map/shellcast-popup.png";
      let siteName = feature.get("lease_id");
      let text = `<p>
                <b>Today:</b> ${handleUndef(feature.get("prob_1d_perc"))}
                <br><b>Tomorrow:</b> ${handleUndef(feature.get("prob_2d_perc"))}
                <br><b>In 2 days:</b> ${handleUndef(feature.get("prob_3d_perc"))}
                </p>`;
      popupHtmlContent.innerHTML = popupContent(title, siteName, iconUrl, text);
      popupLyr.setPosition(coordinate);
    } else {
      popupLyr.setPosition(undefined);
    }
  });
}

// Main
(async () => {
  const growingUnitData = await getGrowingUnitData();
  await initMap(growingUnitData);
  setTableSearchBoxes();
  initGrowingUnitTable(growingUnitData);

  onAuthStateChanged(auth, async (user) => {
    if (user) {
      // hide disclaimer/privacy policy modal
      $(`#${DISCLAIMER_MODAL_ID}`).modal("hide");

      // show the leases table and explanation
      document.getElementById("lease-table-div").style.display = "block";
      document.getElementById("lease-table-explanation").style.display =
        "block";

      // hide the "Create Account" message
      document.getElementById("create-account-message").style.display = "none";

      const leaseData = await getLeaseData();
      initLeaseTable(leaseData);
      createLeasePointFeatures(leaseData).then((features) => {
        addLeaseDataToMap(features);
      });
      // addLeaseDataToMap(leaseData);
    } else {
      // show disclaimer/privacy policy modal
      $(`#${DISCLAIMER_MODAL_ID}`).modal("show");

      // hide the lease table and explanation
      document.getElementById("lease-table-div").style.display = "none";
      document.getElementById("lease-table-explanation").style.display = "none";

      // show the "Create Account" message
      document.getElementById("create-account-message").style.display = "block";
    }
  });
})();
