'use strict';

/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = 'closure-map';
/** Options for the map. */
const MAP_OPTIONS = {
  center: {
    lat: 35.007934,
    lng: -76.315151
  },
  zoom: 9,
  restriction: {
    latLngBounds: {
      north: 38,
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
/** The ID of the lease table element. */
const LEASE_TABLE_ID = 'lease-table';
/** The path to the grow area bound file. */
const GROW_AREA_BOUNDS_PATH = 'static/growing_area_bounds.geojson';
/** The colors used to fill grow areas on the map. */
const COLOR_SCALE = ['#feda8b', '#fdb366', '#f67e4b', '#dd3d2d', '#a50026'];

// a reference to the Google map object
let map;
// a reference to the Google map info window
let mapInfoWindow;

/**
 * Fetches the growing area data from the server and returns it.
 */
async function getGrowAreaData() {
  const res = await fetch('/growAreaProbs');
  if (res.ok) {
    return await res.json();
  }
  console.log('Problem retrieving growing area data.');
  console.log(res);
  return null;
}

/**
 * Fetches the current user's lease data from the server and returns it.
 */
async function getLeaseData() {
  const res = await authorizedFetch('/leaseProbs');
  if (res.ok) {
    return await res.json();
  }
  console.log('Problem retrieving growing area data.');
  console.log(res);
  return null;
}

/**
 * Fills the grow area table with the grow area records.
 */
function initGrowAreaTable(growAreaData) {
  const rows = [];
  for (let [areaId, data] of Object.entries(growAreaData)) {
    const rowData = {
      grow_area: areaId,
      min_max_1d_prob: `${handleUndef(data.min_1d_prob)} / ${handleUndef(data.max_1d_prob)}`,
      min_max_2d_prob: `${handleUndef(data.min_2d_prob)} / ${handleUndef(data.max_2d_prob)}`,
      min_max_3d_prob: `${handleUndef(data.min_3d_prob)} / ${handleUndef(data.max_3d_prob)}`
    };
    rows.push(rowData);
  }
  $(`#${GROW_AREA_TABLE_ID}`).bootstrapTable('load', rows);
}

/**
 * Fills the lease table with lease records.
 */
function initLeaseTable(leaseData) {
  // const rows = [];
  // for (let lease of leaseData) {
  //   const rowData = {
  //     ncdmf_lease_id: areaId,
  //     prob_1d_perc: leaseData.prob_1d_perc,
  //   };
  //   rows.push(rowData);
  // }
  $(`#${LEASE_TABLE_ID}`).bootstrapTable('load', leaseData);
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
async function initMap() {
  const mapEl = document.getElementById(MAP_EL_ID);
  map = new google.maps.Map(mapEl, MAP_OPTIONS);
  // set the map's style
  map.data.setStyle(styleFeature);
  mapInfoWindow = new google.maps.InfoWindow();

  return loadGeoJson(map, GROW_AREA_BOUNDS_PATH);
}

function addGrowAreaDataToMap(growAreaData) {
  // set feature properties based on the grow area data
  for (let [areaId, data] of Object.entries(growAreaData)) {
    const curFeature = map.data.getFeatureById(areaId);
    curFeature.setProperty('min_1d_prob', data.min_1d_prob);
    curFeature.setProperty('max_1d_prob', data.max_1d_prob);
    curFeature.setProperty('min_2d_prob', data.min_2d_prob);
    curFeature.setProperty('max_2d_prob', data.max_2d_prob);
    curFeature.setProperty('min_3d_prob', data.min_3d_prob);
    curFeature.setProperty('max_3d_prob', data.max_3d_prob);
  }

  // set up an info window to appear when clicking on any grow area
  map.data.addListener('click', (event) => {
    const pos = event.latLng;
    const grow_area = event.feature.getProperty('grow_area');
    const min_1d_prob = event.feature.getProperty('min_1d_prob');
    const max_1d_prob = event.feature.getProperty('max_1d_prob');
    const min_2d_prob = event.feature.getProperty('min_2d_prob');
    const max_2d_prob = event.feature.getProperty('max_2d_prob');
    const min_3d_prob = event.feature.getProperty('min_3d_prob');
    const max_3d_prob = event.feature.getProperty('max_3d_prob');
    mapInfoWindow.setPosition(pos);
    mapInfoWindow.setContent(`
      <div>Area: ${grow_area}
      <br>1-day Min / Max %: ${handleUndef(min_1d_prob)} / ${handleUndef(max_1d_prob)}
      <br>2-day Min / Max %: ${handleUndef(min_2d_prob)} / ${handleUndef(max_2d_prob)}
      <br>3-day Min / Max %: ${handleUndef(min_3d_prob)} / ${handleUndef(max_3d_prob)}
      </div>
    `);
    mapInfoWindow.open(map);
  });
}

function addLeaseDataToMap(leaseData) {
  // create a marker for each lease
  for (let lease of leaseData) {
    const leaseInfoContent = (`
      <div>Lease ID: ${lease.ncdmf_lease_id}
      <br>1-day %: ${handleUndef(lease.prob_1d_perc)}
      <br>2-day %: ${handleUndef(lease.prob_2d_perc)}
      <br>3-day %: ${handleUndef(lease.prob_3d_perc)}
      </div>
    `);
    const marker = new google.maps.Marker({
      position: getLatLngFromArray(lease.geometry),
      map: map,
      title: lease.ncdmf_lease_id
      // icon: {
      //   path: "M182.9,551.7c0,0.1,0.2,0.3,0.2,0.3S358.3,283,358.3,194.6c0-130.1-88.8-186.7-175.4-186.9C96.3,7.9,7.5,64.5,7.5,194.6c0,88.4,175.3,357.4,175.3,357.4S182.9,551.7,182.9,551.7z M122.2,187.2c0-33.6,27.2-60.8,60.8-60.8c33.6,0,60.8,27.2,60.8,60.8S216.5,248,182.9,248C149.4,248,122.2,220.8,122.2,187.2z",
      //   strokeColor: "#FFF",
      //   strokeWeight: 1,
      //   fillColor: "#00AEEF",
      //   fillOpacity: 1,
      //   scale: .1
      // }
    });
    marker.addListener('click', () => {
      mapInfoWindow.setContent(leaseInfoContent);
      mapInfoWindow.open(map, marker);
    });
  }
}

function getLatLngFromArray(geometry) {
  return {
    lat: geometry[0],
    lng: geometry[1]
  };
}

function handleUndef(value) {
  return (value || value === 0) ? value : '-';
}

/**
 * Styles the given feature based on its 1-day closure probability.
 * @param {google.maps.data.Feature} feature the feature to style
 */
function styleFeature(feature) {
  // calculate the color of the growing area (feature)
  const areaColor = getColor(feature.getProperty('max_1d_prob'));

  return {
    strokeColor: '#000',
    strokeWeight: 1,
    strokeOpacity: 0.5,
    fillColor: areaColor,
    fillOpacity: 0.8
  };
}

/**
 * Returns a color from the color scale based on the given value.
 * @param {number} value the value to get a color for
 */
function getColor(value) {
  let color = COLOR_SCALE[0];
  if (value >= 20) color = COLOR_SCALE[1];
  if (value >= 40) color = COLOR_SCALE[2];
  if (value >= 60) color = COLOR_SCALE[3];
  if (value >= 80) color = COLOR_SCALE[4];
  return color;
}

(async () => {
  await initMap();

  const growAreaData = await getGrowAreaData();
  initGrowAreaTable(growAreaData);
  addGrowAreaDataToMap(growAreaData);

  firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
      const leaseData = await getLeaseData();
      initLeaseTable(leaseData);
      addLeaseDataToMap(leaseData);
    }
  });
})();
