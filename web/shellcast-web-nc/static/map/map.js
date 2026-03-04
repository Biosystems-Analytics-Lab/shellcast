"use strict";
import { auth } from "../common/js/common.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";

import {
  createClusterSource,
  createCmuGeoJsonSource,
  createHomeExtentButton,
  getBoundaryStyle,
  getGeoJsonAddProbs,
  getGrowingUnitData,
  getLeaseData,
  getPartnerSitesSourceData,
  handleUndef,
  markerSvg,
  partnerAppLyrLegend,
} from "./utils.js";
import { createDaySelector, ShellCastLegend } from "./legends-dayselector.js";
import { initGrowingUnitTable, initLeaseTable, setTableSearchBoxes } from "./table.js";
import {
  createShellCastPopupLayer,
  partnerAppLyrPopupContent,
  popupContent,
  popupHtmlContent,
} from "./popup.js";
import { clusterMemberStyle, clusterStyle, generatePointsCircle } from "./cluster.js";
import {
  CMU_LYR_NAME,
  INITIAL_ZOOM,
  LEASE_PNT_LYR_NAME,
  MAP_CENTER,
  PARTNER_APP_LYR_NAME,
} from "./map_constants.js";

const shellCastLegend = new ShellCastLegend();
/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = "closure-map";
const DISCLAIMER_MODAL_ID = "disclaimer-privacy-modal";

// OSM humanitarian base layer
let osmHumanitarianBaseLyr;
// a reference to the Google map object
let map;
// CMU layer created from GeoJson
let cmuLyr;
// Partner app layer
let partnerLyr;
let clusterCirclesLyr;
// CMU closure probability popup overlay
let popupLyr;
// Cluster layer events
let clickFeature, clickResolution;

function createCmuLayer(cmuGeoJsonSource) {
  return new ol.layer.Vector({
    name: CMU_LYR_NAME,
    opacity: 0.7,
    source: cmuGeoJsonSource,
    // extent: cmuGeoJsonSource.getExtent(),
    style: function (feature) {
      return getBoundaryStyle(feature, 1);
    },
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

function partnerLegendCheckbox() {
  document.getElementById("partner-legend").addEventListener("change", function () {
    let legendTb = document.getElementById("legend-table");
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

/**
 * Set CMU polygon layer symbol style based on "prob_{day}d_perc" value.
 * @param day
 */
export function setCmuPolyStyleByDay(day) {
  cmuLyr.setStyle((feature) => {
    return getBoundaryStyle(feature, day);
  });
}

function createBaseLayer() {
  return new ol.layer.Tile({
    source: new ol.source.OSM({
      source: "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    }),
  });
}

function addAllMapLayers(mapEl) {
  return new ol.Map({
    target: mapEl,
    layers: [osmHumanitarianBaseLyr, cmuLyr, partnerLyr, clusterCirclesLyr],
    overlays: [popupLyr],
    view: new ol.View({
      center: ol.proj.fromLonLat(MAP_CENTER),
      zoom: INITIAL_ZOOM,
    }),
  });
}

function mapBoundingBox() {
  // Calculate the initial extent that shows all points of interest
  const extent = map.getView().calculateExtent(map.getSize());
  // Set the initial view to show all points of interest
  map.getView().fit(extent, {
    padding: [50, 50, 50, 50],
  });
  return extent;
}

function addHomeExtentButton(map, extent) {
  const homeExtentButton = createHomeExtentButton();
  homeExtentButton.onclick = () => {
    map.getView().fit(extent, {
      duration: 1000,
      padding: [50, 50, 50, 50],
    });
    popupLyr.setPosition(undefined);
  };
  const homeExtent = new ol.control.Control({
    element: homeExtentButton,
  });
  map.addControl(homeExtent);
}

function addShellCastLegend(map) {
  const legendLeft = shellCastLegend.create();
  const legendPanel = new ol.control.Control({
    element: legendLeft,
  });
  map.addControl(legendPanel);
}

function addDaySelector(map) {
  const daySelector = createDaySelector();
  let daySelectorPanel = new ol.control.Control({
    element: daySelector,
  });
  map.addControl(daySelectorPanel);
}

function addPartnerSitesLegend(map) {
  const partnerAppLegendControl = new ol.control.Control({
    element: partnerAppLyrLegend,
  });
  map.addControl(partnerAppLegendControl);
  partnerLegendCheckbox();
}

/**
 * Create map.
 * @param growingUnitData
 * @returns {Promise<void>}
 */
async function initMap(growingUnitData) {
  const mapEl = document.getElementById(MAP_EL_ID);
  const cmuGeoJson = await getGeoJsonAddProbs(growingUnitData);
  const cmuGeoJsonSource = await createCmuGeoJsonSource(cmuGeoJson);
  const partnerSitesSource = await getPartnerSitesSourceData();
  // Create map layers
  cmuLyr = await createCmuLayer(cmuGeoJsonSource);
  partnerLyr = await createPartnerAppLayer(partnerSitesSource);

  clusterCirclesLyr = createClusterCirclesLyr(partnerSitesSource);
  osmHumanitarianBaseLyr = createBaseLayer();
  // setBoundingBoxMapExtent();
  popupLyr = createShellCastPopupLayer();

  // Add all layers to the map
  map = addAllMapLayers(mapEl);
  // Get "partnerLyr" initial bounding box extent. Once "partnerLyr" turned off, a layer extent is not available.
  const boundingBoxExt = mapBoundingBox();
  addHomeExtentButton(map, boundingBoxExt);
  addShellCastLegend(map);
  addDaySelector(map);
  addPartnerSitesLegend(map);

  // Add event listeners
  map.on("pointermove", function (evt) {
    let hit = evt.map.hasFeatureAtPixel(evt.pixel);
    this.getTargetElement().style.cursor = hit ? "pointer" : "";
  });

  map.on("singleclick", function (evt) {
    let coordinate = evt.coordinate;
    let lyrName;
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature, layer) {
      if (layer) {
        lyrName = layer.get("name");
      }
      return feature;
    });

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
            (ol.extent.getWidth(extent) < resolution && ol.extent.getHeight(extent) < resolution)
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
        let siteName = feature.get("cmu_name");
        let text = `<p>
                <b>Today:</b> ${handleUndef(feature.get("prob_1d_perc"))}
                <br><b>Tomorrow:</b> ${handleUndef(feature.get("prob_2d_perc"))}
                <br><b>In 2 days:</b> ${handleUndef(feature.get("prob_3d_perc"))}
                </p>`;
        popupHtmlContent.innerHTML = popupContent(title, siteName, iconUrl, text);
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
        prob_2d_perc: item.prob_2d_perc,
        prob_3d_perc: item.prob_3d_perc,
        type: "Point",
      }),
      iconStyle = new ol.style.Style({
        image: new ol.style.Icon({
          anchor: [0.5, 1],
          anchorXUnits: "fraction",
          anchorYUnits: "fraction",
          // src: 'https://openlayers.org/en/latest/examples/data/icon.png'
          src: "data:image/svg+xml," + encodeURI(markerSvg),
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
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature, layer) {
      if (layer) {
        lyrName = layer.get("name");
      }
      return feature;
    });
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

// ================== End: Logged-in users lease points ==================

// ================== Main ==================
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
      document.getElementById("lease-table-explanation").style.display = "block";

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
