'use strict';

/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = 'closure-map';
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
const GROW_AREA_TABLE_ID = 'area-table';
/** The path to the grow area bound file. */
const GROW_AREA_BOUNDS_PATH = 'static/growing_area_bounds.geojson';

/**
 * Fetches the growing area data from the server and returns it.
 */
async function getGrowAreaData() {
  let res = await fetch('/growAreaProbs');
  if (res.ok) {
    return await res.json();
  }
  console.log('Problem retrieving growing area data.');
  console.log(res);
  return null;
}

/**
 * Fills the table with the growing area data.
 */
function initGrowAreaTable(growAreaData) {
  const rows = [];
  for (let [areaId, data] of Object.entries(growAreaData)) {
    const rowData = {
      grow_area: areaId,
      min_max_1d_prob: `${data.min_1d_prob}/${data.max_1d_prob}`,
      min_max_2d_prob: `${data.min_2d_prob}/${data.max_2d_prob}`,
      min_max_3d_prob: `${data.min_3d_prob}/${data.max_3d_prob}`
    };
    rows.push(rowData);
  }
  $(`#${GROW_AREA_TABLE_ID}`).bootstrapTable('load', rows);
}

/**
 * Loads a GeoJSON file at the given URL into the given map object.
 * @param {google.maps.Map} map the map object to load the GeoJSON into
 * @param {string} url the URL of the GeoJSON to load
 */
async function loadGeoJson(map, url) {
  return new Promise((resolve) => {
    map.data.loadGeoJson(url, {idPropertyName: 'grow_area'}, resolve);
  });
}

/**
 * Initializes the map.
 */
async function initMap(growAreaData) {
  const mapEl = document.getElementById(MAP_EL_ID);
  const map = new google.maps.Map(mapEl, MAP_OPTIONS);
  await loadGeoJson(map, GROW_AREA_BOUNDS_PATH);

  // set feature properties based on the gowing area data
  for (let [areaId, data] of Object.entries(growAreaData)) {
    const curFeature = map.data.getFeatureById(areaId);
    curFeature.setProperty('min_1d_prob', data.min_1d_prob);
    curFeature.setProperty('max_1d_prob', data.max_1d_prob);
    curFeature.setProperty('min_2d_prob', data.min_2d_prob);
    curFeature.setProperty('max_2d_prob', data.max_2d_prob);
    curFeature.setProperty('min_3d_prob', data.min_3d_prob);
    curFeature.setProperty('max_3d_prob', data.max_3d_prob);
  }

  // set up info windows to appear when clicking on growing areas
  const infoWindow = new google.maps.InfoWindow();
  map.data.addListener('click', (event) => {
    const pos = event.latLng;
    const grow_area = event.feature.getProperty('grow_area');
    const min_1d_prob = event.feature.getProperty('min_1d_prob');
    const max_1d_prob = event.feature.getProperty('max_1d_prob');
    const min_2d_prob = event.feature.getProperty('min_2d_prob');
    const max_2d_prob = event.feature.getProperty('max_2d_prob');
    const min_3d_prob = event.feature.getProperty('min_3d_prob');
    const max_3d_prob = event.feature.getProperty('max_3d_prob');
    infoWindow.setPosition(pos);
    infoWindow.setContent(`
      <div>Area: ${grow_area}
      <br>3-day Min/Max %: ${min_3d_prob}/${max_3d_prob}
      <br>2-day Min/Max %: ${min_2d_prob}/${max_2d_prob}
      <br>1-day Min/Max %: ${min_1d_prob}/${max_1d_prob}
      </div>
    `);
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
  const RED = [255, 0, 0];
  const WHITE = [255, 255, 255];

  // calculate the closure probability as a floating point
  const prob1Day = feature.getProperty('min_1d_prob');
  let closureProbPerc = 0; // default the closure probability to 0
  if (prob1Day) {
    closureProbPerc = prob1Day / 100;
  }

  // calculate the color of the growing area (feature)
  const areaColor = [];
  for (var i = 0; i < 3; i++) {
    areaColor[i] = lerp(WHITE[i], RED[i], closureProbPerc);
  }

  return {
    strokeColor: '#000',
    strokeWeight: 1,
    strokeOpacity: 0.5,
    fillColor: `rgb(${areaColor[0]},${areaColor[1]},${areaColor[2]})`,
    fillOpacity: 0.8
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

(async () => {
  const growAreaData = await getGrowAreaData();
  initGrowAreaTable(growAreaData);

  // let leaseData = {};
  // firebase.auth().onAuthStateChanged((user) => {
  //   user ? loadLeaseProbs(user) : () => {};
  // });

  initMap(growAreaData);
})();
