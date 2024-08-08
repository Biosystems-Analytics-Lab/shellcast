"use strict";
import { authorizedFetch } from "../common/common.js";
import {
  CAMERA_ICON,
  GROWING_UNIT_BOUNDS_PATH,
  HOME_ICON,
  HOWS_THE_BEACH_ICON,
  PARTNER_APP_POINTS_PATH,
  VISIT_BEACHES_ICON,
} from "./map_constants.js";

export const markerSvg =
  '<svg id="marker" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="30px" height="30px" viewBox="0 0 30 30" enable-background="new 0 0 30 30" xml:space="preserve">' +
  '<path fill="white" stroke="black" d="M22.906,10.438c0,4.367-6.281,14.312-7.906,17.031c-1.719-2.75-7.906-12.665-7.906-17.031S10.634,2.531,15,2.531S22.906,6.071,22.906,10.438z"/>' +
  '<circle fill="black" cx="15" cy="10.677" r="3.291"/></svg>';

export const colorPalette = {
  COLOR_NULL: "transparent",
  COLOR_VERY_LOW: "#4eb265",
  COLOR_LOW: "#fecc5c",
  COLOR_MODERATE: "#fd8d3c",
  COLOR_HIGH: "#e31a1c",
  COLOR_VERY_HIGH: "rgba(139, 0, 0, 0.7)",
};

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
  const res = await fetch("/growingUnitProbs");
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
  const res = await authorizedFetch("/leaseProbs");
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
        for (let [cmuName, data] of Object.entries(growingUnitData)) {
          if (feature.properties.cmu_name === cmuName) {
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

// ================== Styling ==================
export function getColor(value) {
  let color = colorPalette.COLOR_NULL;
  if (value === 1) color = colorPalette.COLOR_VERY_LOW;
  if (value === 2) color = colorPalette.COLOR_LOW;
  if (value === 3) color = colorPalette.COLOR_MODERATE;
  if (value === 4) color = colorPalette.COLOR_HIGH;
  if (value === 5) color = colorPalette.COLOR_VERY_HIGH;
  return color;
}

export function fillBoundaryColor(colorValue, featureName) {
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
  const featureName = feature.get("cmu_name");
  return fillBoundaryColor(value, featureName);
}

export let partnerAppLyrLegend = document.createElement("div");
partnerAppLyrLegend.innerHTML = `
<div id="partner-sites-legend">
  <div id="accordion" style="width: 20rem">
    <div class="card">
      <div class="card-header text-center" id="headingOne" style="padding: .1rem;">
        <h5 class="mb-0">
          <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true"
            aria-controls="collapseOne">
            Legend
          </button>
        </h5>
      </div>
      <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
        <div class="card-body">
          <h6>ShellCast</h6>
          <small>The legend for ShellCast is shown to the left. The forecast date can be changed by clicking 
          "Today", "Tomorrow" and "In 2 days".</small>
          <div style="line-height: 20px; vertical-align: middle; padding-top: 16px;">
            <input type="checkbox" id="partner-legend" role="button"
              style="width: 20px;height: 20px; vertical-align: middle;" checked>
            <label class="form-check-label" for="partner-legend"><span>
                <h6>&emsp13;Partner Sites</h6>
              </span></label>
          </div>      
          <table id="legend-table" class="partner-legend">
            <tr>
              <td class="legend-icon"><img src=${HOWS_THE_BEACH_ICON} alt="How's the Beach"></td>
              <td><small>How's the Beach Sites</small></td>
            </tr>
            <tr>
              <td class="legend-icon"><img src=${VISIT_BEACHES_ICON} alt="Visit Beachs"></td>
              <td><small>Beach Conditions Reporting System</small></td>
            </tr>
            <tr>
              <td class="legend-icon"><img src=${CAMERA_ICON} alt="WebCOOS"</td>
              <td><small>WebCOOS Camera Sites</small></td>
            </tr>
        </table>      
        </div>
      </div>
    </div>
  </div>
</div>`;

export function createHomeExtentButton() {
  const homeExtentButton = document.createElement("div");
  homeExtentButton.innerHTML = `<button id='home-ext-btn'><img id='home-ext-icon' src='${HOME_ICON}' alt='Home'/></button>`;
  homeExtentButton.style.marginTop = "60px";
  return homeExtentButton;
}
