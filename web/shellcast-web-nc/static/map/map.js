"use strict";
import { auth } from "../common/common.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";

import {
  clusterMemberStyle,
  createCmuGeoJsonSource,
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

const circleDistanceMultiplier = 1;
const circleFootSeparation = 28;
const circleStartAngle = Math.PI / 2;

const outerCircleFill = new ol.style.Fill({
  // color: "rgba(255, 153, 102, 0.3)",
  color: "rgba(221, 221, 221, 0.5)",
});
const innerCircleFill = new ol.style.Fill({
  // color: "rgba(255, 165, 0, 0.7)",
  color: "rgba(187, 187, 187, 0.7)",
});
const textFill = new ol.style.Fill({
  color: "#fff",
});
const textStroke = new ol.style.Stroke({
  color: "rgba(0, 0, 0, 0.6)",
  width: 3,
});
const innerCircle = new ol.style.Circle({
  radius: 14,
  fill: innerCircleFill,
});
const outerCircle = new ol.style.Circle({
  radius: 20,
  fill: outerCircleFill,
});

/** Options for the map. */
const mapCenter = [-76.315151, 35.007934];
const initialZoom = 8;
let clickFeature, clickResolution;
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

async function createClusterSource(sourceData) {
  return new ol.source.Cluster({
    distance: 50,
    source: sourceData,
  });
}

function generatePointsCircle(count, clusterCenter, resolution) {
  const circumference =
    circleDistanceMultiplier * circleFootSeparation * (2 + count);
  let legLength = circumference / (Math.PI * 2); //radius from circumference
  const angleStep = (Math.PI * 2) / count;
  const res = [];
  let angle;

  legLength = Math.max(legLength, 35) * resolution; // Minimum distance to get outside the cluster icon.

  for (let i = 0; i < count; ++i) {
    // Clockwise, like spiral.
    angle = circleStartAngle + i * angleStep;
    res.push([
      clusterCenter[0] + legLength * Math.cos(angle),
      clusterCenter[1] + legLength * Math.sin(angle),
    ]);
  }

  return res;
}

function clusterStyle(feature) {
  const size = feature.get("features").length;
  if (size > 1) {
    return [
      new ol.style.Style({
        image: outerCircle,
      }),
      new ol.style.Style({
        image: innerCircle,
        text: new ol.style.Text({
          text: size.toString(),
          fill: textFill,
          stroke: textStroke,
        }),
      }),
    ];
  }
  const originalFeature = feature.get("features")[0];
  return clusterMemberStyle(originalFeature);
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

async function createPartnerAppLayer(sourceData) {
  const clusterSource = await createClusterSource(sourceData);
  return new ol.layer.Vector({
    name: PARTNER_APP_LYR_NAME,
    source: clusterSource,
    style: clusterStyle,
  });
}

function createClusterCirclesLyr(sourceData) {
  return new ol.layer.Vector({
    source: sourceData,
    style: clusterCircleStyle,
  });
}

function partnerLegendCheckbox() {
  document
    .getElementById("partner-legend")
    .addEventListener("change", function () {
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
  partnerLyr.getSource().once("change", function () {
    map.getView().fit(partnerLyr.getSource().getExtent());
  });
}

function createBaseLayer() {
  return new ol.layer.Tile({
    source: new ol.source.OSM({
      source: "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    }),
  });
}

function createHomeExtentButton() {
  const homeExtentButton = document.createElement("div");
  homeExtentButton.id = "home-ext-btn";
  homeExtentButton.innerHTML =
    "<button style='border: none; background: none; outline: none;'><img src='./static/img/home.png' alt='Home button' style='width: 28px; height:28px;'/></button>";
  homeExtentButton.style.marginTop = "60px";
  return homeExtentButton;
}

function createPartnerSitesLegendButton() {
  const partnerSitesLegendButton = document.createElement("div");
  partnerSitesLegendButton.id = "partner-sites-legend-btn";
  partnerSitesLegendButton.innerHTML =
    "<button style='border: none; background: none; outline: none; float: right;'><img src='./static/img/map/legend.png' alt='Partner Sites button' style='width: 54px; height:54px;'/></button>";
  partnerSitesLegendButton.style.top = "10px";
  partnerSitesLegendButton.style.right = "10px";
  partnerSitesLegendButton.style.position = "absolute";
  partnerSitesLegendButton.style.zIndex = "-1";
  // partnerSitesLegendButton.onclick(() => {
  //   alert("Legend button clicked");
  // });
  return partnerSitesLegendButton;
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
  partnerLyr = await createPartnerAppLayer(partnerSitesSource);
  clusterCirclesLyr = createClusterCirclesLyr(partnerSitesSource);
  osmHumanitarianBaseLyr = createBaseLayer();
  setBoundingBoxMapExtent();

  popupLyr = createShellCastPopupLayer();

  map = new ol.Map({
    target: mapEl,
    layers: [osmHumanitarianBaseLyr, cmuLyr, partnerLyr, clusterCirclesLyr],
    overlays: [popupLyr],
    view: new ol.View({
      center: ol.proj.fromLonLat(mapCenter),
      zoom: initialZoom,
    }),
  }); // # Set map

  const homeExtentButton = createHomeExtentButton();
  homeExtentButton.onclick = () => {
    map.getView().fit(partnerLyr.getSource().getExtent(), {
      duration: 500,
      padding: [50, 50, 50, 50],
    });
  };
  const homeExtent = new ol.control.Control({
    element: homeExtentButton,
  });
  map.addControl(homeExtent);

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
  map.on("pointermove", function (evt) {
    var hit = evt.map.hasFeatureAtPixel(evt.pixel);
    this.getTargetElement().style.cursor = hit ? "pointer" : "";
  });

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
            view.fit(extent, { duration: 500, padding: [80, 80, 80, 80] });
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
        popupHtmlContent.innerHTML = popupContent(
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
          imgSize: [26, 26],
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
