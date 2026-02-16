"use strict";
import { auth } from "../common/js/common.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";

import {
  addAllMapLayers,
  addHomeExtentButton,
  createBaseLayer,
  createClusterSource,
  createCmuGeoJsonSource,
  createCmuLayer,
  createDaySelector,
  getBoundaryStyle,
  getGeoJsonAddProbs,
  getGrowingUnitData,
  getLeaseData,
  getPartnerSitesSourceData,
  handleUndef,
  mapBoundingBox,
} from "./utils.js";

import {
  initGrowingUnitTable,
  initLeaseTable,
  setTableSearchBoxes,
} from "./table.js";
import {
  createShellCastPopupLayer,
  partnerAppLyrPopupContent,
  POPUP_CONTENT_ELE,
  popupContent,
} from "./popup.js";
import {
  clusterMemberStyle,
  clusterStyle,
  generatePointsCircle,
} from "./cluster.js";
import {
  CMU_LYR_NAME,
  INITIAL_ZOOM,
  LEASE_PNT_LYR_NAME,
  MAP_CENTER,
  MARKER_SVG,
  PARTNER_APP_LYR_NAME,
} from "./map_constants.js";
import {
  addPartnerSitesLegendControl,
  addShellCastLegendControl,
} from "./legends-dayselector.js";

/** The ID of the HTML element that holds the map. */
const MAP_ELE_ID = "closure-map";
const DISCLAIMER_MODAL_ID = "disclaimer-privacy-modal";
const LEGEND_ELE_ID = "shellcast-legend";
const PARTNER_LEGEND_ELE_ID = "partner-sites-legend";
const PARTNER_LEGEND_CHECKBOX_ELE_ID = "partner-sites-legend-checkbox";
const PARTNER_LEGEND_CHECKBOX_ELE_TABLE = "partner-sites-legend-table";
// OSM humanitarian base layer
let osmHumanitarianBaseLyr;
let map;
let cmuLyr;
let partnerLyr;
let clusterCirclesLyr;
let popupLyr;
let boundingBoxExt;
// Cluster layer events
let clickFeature, clickResolution;

function clusterCircleStyle(cluster, resolution) {
  if (cluster !== clickFeature || resolution !== clickResolution) {
    return null;
  }
  const clusterMembers = cluster.get("features");
  return generatePointsCircle(
    clusterMembers.length,
    cluster.getGeometry().getCoordinates(),
    resolution,
  ).reduce((styles, coordinates, i) => {
    const point = new ol.geom.Point(coordinates);
    styles.push(
      clusterMemberStyle(
        new ol.Feature.Feature({
          ...clusterMembers[i].getProperties(),
          geometry: point,
        }),
      ),
    );
    return styles;
  }, []);
}

function createClusterCirclesLyr(sourceData) {
  return new ol.layer.Vector({
    source: sourceData,
    style: clusterCircleStyle,
  });
}

async function createPartnerAppLayer(sourceData) {
  const clusterSource = await createClusterSource(sourceData);
  return new ol.layer.Vector({
    name: PARTNER_APP_LYR_NAME,
    source: clusterSource,
    style: clusterStyle,
  });
}

/**
 * EVENT: Add a checkbox to show/hide the partner sites layer.
 */
function partnerLegendCheckbox() {
  document
    .getElementById(PARTNER_LEGEND_CHECKBOX_ELE_ID)
    .addEventListener("change", function () {
      let legendTb = document.getElementById(PARTNER_LEGEND_CHECKBOX_ELE_TABLE);
      let isVisible = partnerLyr.getVisible();
      if (this.checked) {
        if (!isVisible) {
          partnerLyr.setVisible(true);
          legendTb.style.display = "block";
        }
      } else {
        partnerLyr.setVisible(false);
        legendTb.style.display = "none";
        popupLyr.setPosition(undefined);
      }
    });
}

function setCmuPolyStyleByDay(day) {
  cmuLyr.setStyle((feature) => {
    return getBoundaryStyle(feature, day);
  });
}

function addDaySelectorClickListener(button, idx) {
  button.addEventListener("click", () => setCmuPolyStyleByDay(idx + 1));
}

function _addDaySelector() {
  let daySelector = createDaySelector();
  for (let i = 0; i < daySelector.childElementCount; i++) {
    const button = daySelector.children[i];
    addDaySelectorClickListener(button, i);
    // button.addEventListener("click", () => {
    //   setCmuPolyStyleByDay(i + 1);
    // });
  }
  return new ol.control.Control({ element: daySelector });
}

/**
 * Create map.
 * @param growingUnitData
 * @returns {Promise<void>}
 */
async function initMap(growingUnitData) {
  const mapEl = document.getElementById(MAP_ELE_ID);
  const cmuGeoJson = await getGeoJsonAddProbs(growingUnitData);
  console.log(growingUnitData);
  console.log(cmuGeoJson);
  const cmuGeoJsonSource = await createCmuGeoJsonSource(cmuGeoJson);
  const partnerSitesSource = await getPartnerSitesSourceData();

  // Create map layers
  cmuLyr = await createCmuLayer(cmuGeoJsonSource, CMU_LYR_NAME);
  partnerLyr = await createPartnerAppLayer(partnerSitesSource);
  clusterCirclesLyr = createClusterCirclesLyr(partnerSitesSource);
  osmHumanitarianBaseLyr = createBaseLayer();
  // setBoundingBoxMapExtent();
  popupLyr = createShellCastPopupLayer();

  // Add all layers to the map
  map = addAllMapLayers(
    mapEl,
    [osmHumanitarianBaseLyr, cmuLyr, partnerLyr, clusterCirclesLyr],
    popupLyr,
    MAP_CENTER,
    INITIAL_ZOOM,
  );

  // Add home extent button at the left
  boundingBoxExt = mapBoundingBox(map);
  addHomeExtentButton(map, boundingBoxExt, popupLyr);
  // Add ShellCast legend at the left
  let shellcastLegendControl = addShellCastLegendControl(LEGEND_ELE_ID);
  map.addControl(shellcastLegendControl);

  // Add Partner Sites legend at the right
  let partnerAppLegendControl = addPartnerSitesLegendControl(
    PARTNER_LEGEND_ELE_ID,
  );
  map.addControl(partnerAppLegendControl);
  // Add Partner Sites legend checkbox to turn on and off the layer
  partnerLegendCheckbox();

  setCmuPolyStyleByDay(1);
  // Add event listeners
  map.on("pointermove", function (evt) {
    let hit = evt.map.hasFeatureAtPixel(evt.pixel);
    this.getTargetElement().style.cursor = hit ? "pointer" : "";
  });

  // EVENT: Single click to show popup window for CMU and Partner Sites
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

        let clusterMembers = feature.get("features");
        if (clusterMembers.length > 1) {
          // Calculate the extent of the cluster members.
          const extent = new ol.extent.createEmpty();
          clusterMembers.forEach((feature) =>
            ol.extent.extend(extent, feature.getGeometry().getExtent()),
          );
          const view = map.getView();
          const resolution = map.getView().getResolution();
          if (
            view.getZoom() === view.getMaxZoom() ||
            (ol.extent.getWidth(extent) < resolution &&
              ol.extent.getHeight(extent) < resolution)
          ) {
            // Show an expanded view of the cluster members.
            clickFeature = clusterMembers[0];
            clickResolution = resolution;
            clusterCirclesLyr.setStyle(clusterCircleStyle);
          } else {
            // Zoom to the extent of the cluster members.
            view.fit(extent, { duration: 1000, padding: [80, 80, 80, 80] });
          }
        }
      } else if (lyrName === CMU_LYR_NAME) {
        let title = "Growing Unit Closure Probability";
        let iconUrl = "static/img/map/shellcast-popup.png";
        let siteName = `${feature.get("sh_name")}: ${feature.get("sh_id")}`;
        let text = `<p>
                <b>Today:</b> ${handleUndef(feature.get("prob_1d_perc"))}
                </p>`;
        POPUP_CONTENT_ELE.innerHTML = popupContent(
          title,
          siteName,
          iconUrl,
          text,
        );
      }
      popupLyr.setPosition(coordinate);
    } else {
      this.getTargetElement().style.cursor = "";
      popupLyr.setPosition(undefined);
    }
  });
}

// ================== Logged in users lease points ==================
/**
 * Create point layer for user's registered lease locations.
 * @param leaseData
 * @returns {Promise<*>}
 */
async function createLeasePointFeatures(leaseData) {
  return leaseData.map((item) => {
    let longitude = item.longitude,
      latitude = item.latitude,
      iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([longitude, latitude])),
        lease_id: item.lease_id,
        prob_1d_perc: item.prob_1d_perc,
        type: "Point",
      }),
      iconStyle = new ol.style.Style({
        image: new ol.style.Icon({
          anchor: [0.5, 1],
          anchorXUnits: "fraction",
          anchorYUnits: "fraction",
          // src: 'https://openlayers.org/en/latest/examples/data/icon.png'
          src: "data:image/svg+xml," + encodeURI(MARKER_SVG),
          scale: 2,
          size: [26, 26],
        }),
      });

    iconFeature.setStyle(iconStyle);
    return iconFeature;
  });
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
    name: LEASE_PNT_LYR_NAME,
    source: leasePntSource,
  });
  map.addLayer(leasePntLyr);

  // Add mouseover event for popup
  map.on("click", function (evt) {
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
                </p>`;
      POPUP_CONTENT_ELE.innerHTML = popupContent(
        title,
        siteName,
        iconUrl,
        text,
      );
      popupLyr.setPosition(coordinate);
    } else {
      popupLyr.setPosition(undefined);
    }
  });
}

// ================== End: Logged-in users lease points ==================

// ================== Main ==================
(async () => {
  const growingUnitData = await getGrowingUnitData();
  console.log(growingUnitData);
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
