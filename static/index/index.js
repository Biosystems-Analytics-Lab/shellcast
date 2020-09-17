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
/** The color used to fill in grow areas without a closure probability. */
const COLOR_NULL = 'transparent';
/** The color used to fill in grow areas with a 0-40% closure probability. */
const COLOR_0_40 = '#4eb265';
/** The color used to fill in grow areas with a 40-60% closure probability. */
const COLOR_40_60 = '#fecc5c';
/** The color used to fill in grow areas with a 60-80% closure probability. */
const COLOR_60_80 = '#fd8d3c';
/** The color used to fill in grow areas with a 80-100% closure probability. */
const COLOR_80_100 = '#e31a1c';
/** The text and colors used for the legend. */
const LEGEND_SCALE = [
  { text: 'No data', color: COLOR_NULL},
  { text: '0 - 40%', color: COLOR_0_40},
  { text: '40 - 60%', color: COLOR_40_60},
  { text: '60 - 80%', color: COLOR_60_80},
  { text: '80 - 100%', color: COLOR_80_100}
];

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
  console.log('Problem retrieving lease data.');
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
 * @param {string} htmlStr the HTML string to create an element from
 * @return {Element} a DOM element created from the given string
 */
function strToEl(htmlStr) {
  const template = document.createElement('template');
  template.innerHTML = htmlStr.trim();
  return template.content.firstChild;
}

function createLegend() {
  const legend = document.createElement('div');
  legend.style.border = '1px solid black';
  legend.style.display = 'grid';
  legend.style.gridTemplateColumns = 'auto 1rem';
  legend.style.marginLeft = '10px';
  legend.style.textAlign = 'center';
  legend.style.lineHeight = '2rem';
  legend.style.fontSize = '1rem';
  // add text and colors to legend
  for (let step of LEGEND_SCALE) {
    const textDiv = strToEl(`<div>${step.text}</div>`);
    textDiv.style.paddingLeft = '3px';
    textDiv.style.paddingRight = '3px';
    textDiv.style.backgroundColor = 'white';
    legend.appendChild(textDiv);
    const colorDiv = document.createElement('div');
    colorDiv.style.backgroundColor = step.color;
    colorDiv.style.borderLeft = '1px solid black';
    colorDiv.style.borderTop = '1px solid black';
    legend.appendChild(colorDiv);
  }
  return legend;
}

function createDaySelector(map) {
  const htmlStr = `
    <div class="btn-group btn-group-toggle btn-group-vertical" data-toggle="buttons">
      <label class="btn btn-outline-secondary active">
        <input type="radio" id="1day" checked> 1-day
      </label>
      <label class="btn btn-outline-secondary">
        <input type="radio" id="2day"> 2-day
      </label>
      <label class="btn btn-outline-secondary">
        <input type="radio" id="3day"> 3-day
      </label>
    </div>
  `;
  const daySelector = strToEl(htmlStr);
  daySelector.style.backgroundColor = 'white';
  daySelector.style.margin = '10px';
  daySelector.style.border = '1px solid black';
  for (let i = 0; i < daySelector.childElementCount; i++) {
    const button = daySelector.children[i];
    button.addEventListener('click', () => map.data.setStyle(styleFeatureBasedOnDay(i + 1)));
  }
  return daySelector;
}

/**
 * Initializes the map.
 */
async function initMap() {
  const mapEl = document.getElementById(MAP_EL_ID);
  map = new google.maps.Map(mapEl, MAP_OPTIONS);
  // set the map's style
  map.data.setStyle(styleFeatureBasedOnDay(1));
  mapInfoWindow = new google.maps.InfoWindow();
  
  // add the legend to the map
  const legend = createLegend();
  map.controls[google.maps.ControlPosition.LEFT_TOP].push(legend);
  // add the day selector to the map
  const daySelector = createDaySelector(map);
  map.controls[google.maps.ControlPosition.LEFT_TOP].push(daySelector);

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
      title: lease.ncdmf_lease_id,
      icon: {
        url: '/static/img/custom_marker.png'
      }
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
 * Returns a function that styles features based on the max probability for the given day.
 * @param {number} day the day to style with
 */
function styleFeatureBasedOnDay(day) {
  return (feature) => {
    // calculate the color of the growing area (feature)
    const areaColor = getColor(feature.getProperty(`max_${day}d_prob`));
    return {
      strokeColor: '#000',
      strokeWeight: 1,
      strokeOpacity: 0.5,
      fillColor: areaColor,
      fillOpacity: 0.8
    };
  }
}

/**
 * Returns a color from the color scale based on the given value.
 * @param {number} value the value to get a color for
 */
function getColor(value) {
  let color = 'transparent';
  if (value >= 0) color = COLOR_0_40;
  if (value >= 40) color = COLOR_40_60;
  if (value >= 60) color = COLOR_60_80;
  if (value >= 80) color = COLOR_80_100;
  if (value === null) color = 'transparent';
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
