'use strict';

/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = "closure-map";
/** Options for the map. */
const MAP_OPTIONS = {
  center: {
    lat: 35.2,
    lng: -77.2
  },
  zoom: 7,
  restriction: {
    latLngBounds: {
      north: 36.85,
      south: 33.67,
      east: -74,
      west: -79
    },
    strictBounds: false
  },
  clickableIcons: false,
  streetViewControl: false,
  mapTypeControl: true,
  mapTypeControlOptions: {
    style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
  },
  mapTypeId: 'hybrid' // 'roadmap', 'satellite', 'hybrid', 'terrain'
};
/** The ID of the grow area table element. */
const TABLE_ID = "area-table";

let areaDataPromise;
let areaData;
(async () => {
  areaDataPromise = getAreaData();
  areaData = await areaDataPromise;
  initTable();
  initMap();
})();

/**
 * Fetches the growing area data from the server and returns it.
 */
async function getAreaData() {
  let res = await fetch("/areaData");
  // if (res.ok) {
  //   return await res.json();
  // }
  // console.log("Problem retrieving growing area data.");
  // console.log(res);
  // return null;
  return {};
}

/**
 * Fills the table with the growing area data.
 */
function initTable() {
  const table = document.getElementById(TABLE_ID).getElementsByTagName("tbody")[0];
  for (let [areaId, data] of Object.entries(areaData)) {
    let row = table.insertRow();
    row.insertCell().appendChild(document.createTextNode(areaId));
    row.insertCell().appendChild(document.createTextNode(data.prob3Day));
    row.insertCell().appendChild(document.createTextNode(data.prob2Day));
    row.insertCell().appendChild(document.createTextNode(data.prob1Day));
  }
}

/**
 * Loads a GeoJSON file at the given URL into the given map object.
 * @param {google.maps.Map} map the map object to load the GeoJSON into
 * @param {string} url the URL of the GeoJSON to load
 */
async function loadGeoJson(map, url) {
  return new Promise((resolve) => {
    map.data.loadGeoJson(url, {idPropertyName: "grow_area"}, resolve);
  });
}

/**
 * Initializes the map.
 */
async function initMap() {
  const mapEl = document.getElementById(MAP_EL_ID);
  const map = new google.maps.Map(mapEl, MAP_OPTIONS);
  await loadGeoJson(map, "static/growing_area_bounds.geojson");
  // wait for the growing area data to become available
  await areaDataPromise;

  // set feature properties based on the gowing area data
  for (let [areaId, data] of Object.entries(areaData)) {
    const curFeature = map.data.getFeatureById(areaId);
    curFeature.setProperty("prob1Day", data.prob1Day);
    curFeature.setProperty("prob2Day", data.prob2Day);
    curFeature.setProperty("prob3Day", data.prob3Day);
  }

  // set up info windows to appear when clicking on growing areas
  const infoWindow = new google.maps.InfoWindow();
  map.data.addListener('click', function(event) {
    const pos = event.latLng;
    const areaId = event.feature.getProperty('grow_area');
    const prob1Day = event.feature.getProperty('prob1Day');
    const prob2Day = event.feature.getProperty('prob2Day');
    const prob3Day = event.feature.getProperty('prob3Day');
    infoWindow.setPosition(pos);
    infoWindow.setContent(`<div>Area: ${areaId}<br>1-day %: ${prob1Day}<br>2-day %: ${prob2Day}<br>3-day %: ${prob3Day}</div>`);
    infoWindow.open(map);
  });

  // set the map's style
  map.data.setStyle(styleFeature);
}

/**
 * Styles the given feature based on its 1-day closure probability.
 * @param {google.maps.data.Feature} feature the feature to style
 */
function styleFeature(feature) {
  const RED_HSL = [5, 69, 54]; // red in HSL
  // const GREEN_HSL = [151, 83, 34]; // green in HSL
  const GREEN_HSL = [151, 83, 34]; // green in HSL

  // calculate the closure probability as a floating point
  const prob1Day = feature.getProperty('prob1Day');
  let closureProbPerc = 0; // default the closure probability to 0
  if (prob1Day) {
    closureProbPerc = prob1Day / 100;
  }

  // calculate the color of the growing area (feature)
  const areaColor = [];
  for (var i = 0; i < 3; i++) {
    areaColor[i] = lerp(GREEN_HSL[i], RED_HSL[i], closureProbPerc);
  }

  return {
    strokeColor: '#000',
    strokeWeight: 1,
    strokeOpacity: 0.5,
    fillColor: 'hsl(360,100%,100%', // `hsl(${areaColor[0]},${areaColor[1]}%,${areaColor[2]}%)`,
    fillOpacity: 0.5
  };
}

/**
 * Performs a linear interpolation between the low and high values.
 * @param {number} lowVal the low value
 * @param {number} highVal the high value
 * @param {number} factor a floating point number between 0 and 1
 */
function lerp(lowVal, highVal, factor) {
  return (highVal - lowVal) * factor + lowVal;
}
