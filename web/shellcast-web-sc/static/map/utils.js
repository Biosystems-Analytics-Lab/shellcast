"use strict";
import { authorizedFetch } from "../common/js/common.js";
import {
  COLOR_PALLET,
  GROWING_UNIT_BOUNDS_PATH,
  HOME_ICON,
  PARTNER_APP_POINTS_PATH,
} from "./map_constants.js";

/**
 * Returns a value of the risk factor.
 * @param {number} value the value with probability
 */
export function handleUndef(value) {
  let flag = "";
  if (value === 1) flag = "Very Low";
  if (value === 2) flag = "Low";
  if (value === 3) flag = "Moderate";
  if (value === 4) flag = "High";
  if (value === 5) flag = "Very High";
  return value || value === 0 ? flag : "-";
}

export function getDomainName(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname;
  } catch (e) {
    console.error("Invalid URL", e);
    return null;
  }
}

/**
 * @param {string} htmlStr the HTML string to create an element from
 * @return {Element} a DOM element created from the given string
 */
export let strToEl = function (htmlStr) {
  const template = document.createElement("template");
  template.innerHTML = htmlStr.trim();
  return template.content.firstChild;
};

// ================== API requests ==================
/**
 * Fetches the growing unit data from the server and returns it.
 */
export async function getGrowingUnitData() {
  const res = await fetch("/growing-unit-probs");
  if (res.ok) {
    return await res.json();
  }
  console.log("Problem retrieving growing unit data.");
  console.log(res);
  return null;
}

/**
 * Fetches the current user's lease data from the server and returns it.
 */
export async function getLeaseData() {
  const res = await authorizedFetch("/lease-probs");
  if (res.ok) {
    return await res.json();
  }
  console.log("Problem retrieving lease data.");
  console.log(res);
  return null;
}

// ================== Get GeoJSON ==================
/**
 * Add GeoJson CMU polygon feature to closure probabilities properties.
 * @param growingUnitData
 * @returns {Promise<any>}
 */
export async function getGeoJsonAddProbs(growingUnitData) {
  return fetch(GROWING_UNIT_BOUNDS_PATH)
    .then((response) => response.json())
    .then((response) => {
      response.features.forEach((feature) => {
        for (let [lease_id, data] of Object.entries(growingUnitData)) {
          if (feature.properties.lease_id === lease_id) {
            feature.properties.prob_1d_perc = data.prob_1d_perc;
            feature.properties.prob_2d_perc = data.prob_2d_perc;
            feature.properties.prob_3d_perc = data.prob_3d_perc;
          }
        }
      });
      return response;
    })
    .then((res) => {
      return res;
    });
}

export function createCmuGeoJsonSource(cmuGeoJson) {
  return new ol.source.Vector({
    features: new ol.format.GeoJSON().readFeatures(cmuGeoJson, {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    }),
  });
}

export async function getPartnerSitesSourceData() {
  return new ol.source.Vector({
    url: PARTNER_APP_POINTS_PATH,
    format: new ol.format.GeoJSON(),
  });
}

export async function createClusterSource(sourceData) {
  return new ol.source.Cluster({
    distance: 50,
    source: sourceData,
  });
}

export function createBaseLayer() {
  return new ol.layer.Tile({
    source: new ol.source.OSM({
      source: "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    }),
  });
}

export function createCmuLayer(cmuGeoJsonSource, htmlElement) {
  return new ol.layer.Vector({
    name: htmlElement,
    opacity: 0.7,
    source: cmuGeoJsonSource,
    extent: cmuGeoJsonSource.getExtent(),
    style: function (feature) {
      return getBoundaryStyle(feature, 1);
    },
  });
}

export function createSimplePopupLayer(containerEle) {
  return new ol.Overlay({
    element: containerEle,
    autoPan: {
      animation: {
        duration: 250,
      },
    },
  });
}

// ================== Styling ==================
export function getColor(value) {
  let color = COLOR_PALLET.COLOR_NULL;
  if (value === 1) color = COLOR_PALLET.COLOR_VERY_LOW;
  if (value === 2) color = COLOR_PALLET.COLOR_LOW;
  if (value === 3) color = COLOR_PALLET.COLOR_MODERATE;
  if (value === 4) color = COLOR_PALLET.COLOR_HIGH;
  if (value === 5) color = COLOR_PALLET.COLOR_VERY_HIGH;
  return color;
}

function fillBoundaryColor(colorValue, featureName) {
  return new ol.style.Style({
    fill: new ol.style.Fill({
      color: getColor(colorValue),
    }),
    stroke: new ol.style.Stroke({
      color: "rgba(255, 255, 255, 0.5)",
      width: 1,
    }),
    text: new ol.style.Text({
      text: featureName,
      font: "Arial",
      size: "12px",
      fill: new ol.style.Fill({
        color: "black",
      }),
      stroke: new ol.style.Stroke({
        color: "white",
        width: 3,
      }),
    }),
    textBaseline: "middle",
  });
}

export function getBoundaryStyle(feature, day) {
  const value = feature.get(`prob_${day}d_perc`);
  const featureName = feature.get("lease_id");
  return fillBoundaryColor(value, featureName);
}

/**
 * Create closure day button selector on map.
 * @returns {Element}
 */
export function createDaySelector() {
  const htmlStr = `
    <div class="btn-group btn-group-toggle btn-group-vertical day-selector" data-toggle="buttons">
      <label class="btn btn-outline-secondary active">
        <input type="radio" id="1day" checked> Today
      </label>
      <label class="btn btn-outline-secondary">
        <input type="radio" id="2day"> Tomorrow
      </label>
      <label class="btn btn-outline-secondary">
        <input type="radio" id="3day"> In 2 days
      </label>
    </div>
  `;
  const daySelector = strToEl(htmlStr);
  daySelector.style.backgroundColor = "white";
  daySelector.style.margin = "10px";
  daySelector.style.border = "1px solid black";
  return daySelector;
}

function createHomeExtentButton() {
  const homeExtentButton = document.createElement("div");
  homeExtentButton.innerHTML = `<button id='home-ext-btn'><img id='home-ext-icon' src='${HOME_ICON}' alt='Home'/></button>`;
  homeExtentButton.style.marginTop = "60px";
  return homeExtentButton;
}

export function addHomeExtentButton(map, extent, popupLyr) {
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

export function mapBoundingBox(map) {
  const extent = map.getView().calculateExtent(map.getSize());
  // Set the initial view to show all points of interest
  map.getView().fit(extent, {
    padding: [50, 50, 50, 50],
  });
  return extent;
}

export function addAllMapLayers(mapEl, lyrList, popupLyr, mapCenter, zoomLevel) {
  return new ol.Map({
    target: mapEl,
    layers: lyrList,
    overlays: [popupLyr],
    view: new ol.View({
      center: ol.proj.fromLonLat(mapCenter),
      zoom: zoomLevel,
    }),
  });
}
