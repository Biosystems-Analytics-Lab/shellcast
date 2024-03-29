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
/** The ID of the growing unit table element. */
const GROWING_UNIT_TABLE_ID = 'growing-unit-table';
/** The ID of the lease table element. */
const LEASE_TABLE_ID = 'lease-table';
/** The path to the growing unit boundaries file. */
const GROWING_UNIT_BOUNDS_PATH = 'static/cmu_bounds.geojson';
/** The color used to fill in growing units without a closure probability. */
const COLOR_NULL = 'transparent';
// /** The color used to fill in growing units with a Very Low risk. */
const COLOR_VERY_LOW = '#4eb265';
// /** The color used to fill in growing units with a Low risk. */
const COLOR_LOW = '#fecc5c';
// /** The color used to fill in growing units with a Moderate risk. */
const COLOR_MODERATE = '#fd8d3c';
// /** The color used to fill in growing units with a High risk. */
const COLOR_HIGH = '#e31a1c';
// /** The color used to fill in growing units with a Very High risk. */
const COLOR_VERY_HIGH = '#8B0000';
/** The text and colors used for the legend. */
const LEGEND_SCALE = [
  { text: 'No data', color: COLOR_NULL},
  { text: 'Very Low', color: COLOR_VERY_LOW},
  { text: 'Low', color: COLOR_LOW},
  { text: 'Moderate', color: COLOR_MODERATE},
  { text: 'High', color: COLOR_HIGH},
  { text: 'Very High', color: COLOR_VERY_HIGH}
];

// a reference to the Google map object
let map;
// a reference to the Google map info window
let mapInfoWindow;

/**
 * Fetches the growing unit data from the server and returns it.
 */
async function getGrowingUnitData() {
  const res = await fetch('/growingUnitProbs');
  if (res.ok) {
    return await res.json();
  }
  console.log('Problem retrieving growing unit data.');
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
 * Fills the growing unit table with the growing unit records.
 */
function initGrowingUnitTable(growingUnitData) {
  const rows = [];
  for (let [cmuName, data] of Object.entries(growingUnitData)) {
    const rowData = {
      cmu_name: cmuName,
      prob_1d_perc: `${handleUndef(data.prob_1d_perc)}`,
      prob_2d_perc: `${handleUndef(data.prob_2d_perc)}`,
      prob_3d_perc: `${handleUndef(data.prob_3d_perc)}`
    };
    rows.push(rowData);
  }
  $(`#${GROWING_UNIT_TABLE_ID}`).bootstrapTable('load', rows);
}

/**
 * Fills the lease table with lease records.
 */
function initLeaseTable(leaseData) {
  const rows = [];
  for (let lease of leaseData) {
    const rowData = {
      ncdmf_lease_id: lease.ncdmf_lease_id,
      prob_1d_perc: `${handleUndef(lease.prob_1d_perc)}`,
      prob_2d_perc: `${handleUndef(lease.prob_2d_perc)}`,
      prob_3d_perc: `${handleUndef(lease.prob_3d_perc)}`
    };
    rows.push(rowData);
  }
  $(`#${LEASE_TABLE_ID}`).bootstrapTable('load', rows);
}

/**
 * Loads a GeoJSON file at the given URL into the given map object.
 * @param {google.maps.Map} map the map object to load the GeoJSON into
 * @param {string} url the URL of the GeoJSON to load
 */
async function loadGeoJson(map, url) {
  return new Promise((resolve) => {
    map.data.loadGeoJson(url, {idPropertyName: 'cmu_name'}, resolve);
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

  return loadGeoJson(map, GROWING_UNIT_BOUNDS_PATH);
}

function addGrowingUnitDataToMap(growingUnitData) {
  // set feature properties based on the growing unit data
  for (let [cmuName, data] of Object.entries(growingUnitData)) {
    const curFeature = map.data.getFeatureById(cmuName);
    curFeature.setProperty('prob_1d_perc', data.prob_1d_perc);
    curFeature.setProperty('prob_2d_perc', data.prob_2d_perc);
    curFeature.setProperty('prob_3d_perc', data.prob_3d_perc);
  }

  // set up an info window to appear when clicking on any growing unit
  map.data.addListener('click', (event) => {
    const pos = event.latLng;
    const cmuName = event.feature.getProperty('cmu_name');
    const prob_1d_perc = event.feature.getProperty('prob_1d_perc');
    const prob_2d_perc = event.feature.getProperty('prob_2d_perc');
    const prob_3d_perc = event.feature.getProperty('prob_3d_perc');
    mapInfoWindow.setPosition(pos);
    mapInfoWindow.setContent(`
      <div>Growing Unit: ${cmuName}
      <br>Today: ${handleUndef(prob_1d_perc)}
      <br>Tomorrow: ${handleUndef(prob_2d_perc)}
      <br>In 2 days: ${handleUndef(prob_3d_perc)}
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
      <br>Today: ${handleUndef(lease.prob_1d_perc)}
      <br>Tomorrow: ${handleUndef(lease.prob_2d_perc)}
      <br>In 2 days: ${handleUndef(lease.prob_3d_perc)}
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

/**
 * Returns a value of the risk factor.
 * @param {number} value the value with probability
 */
function handleUndef(value) {
  let flag = ""
  if(value === 1)
    flag = "Very Low"
  if(value === 2)
    flag = "Low"
  if(value === 3)
    flag = "Moderate"
  if(value === 4)
    flag = "High"
  if(value === 5)
    flag = "Very High"
  return (value || value === 0) ? flag : '-';
}

/**
 * Returns a function that styles features based on the probability for the given day.
 * @param {number} day the day to style with
 */
function styleFeatureBasedOnDay(day) {
  return (feature) => {
    // calculate the color of the growing unit (feature)
    const unitColor = getColor(feature.getProperty(`prob_${day}d_perc`));
    return {
      strokeColor: '#000',
      strokeWeight: 1,
      strokeOpacity: 0.5,
      fillColor: unitColor,
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
  if (value === 1) color = COLOR_VERY_LOW;
  if (value === 2) color = COLOR_LOW;
  if (value === 3) color = COLOR_MODERATE;
  if (value === 4) color = COLOR_HIGH;
  if (value === 5) color = COLOR_VERY_HIGH;
  return color;
}

(async () => {
  await initMap();

  // change placeholder text and title attribute for table search boxes
  const leaseTableSearchBox = document.querySelector('#lease-table-div input');
  leaseTableSearchBox.placeholder = 'Search leases';
  leaseTableSearchBox.title = 'Search leases table';
  const growingUnitTableSearchBox = document.querySelector('#growing-unit-table-div input');
  growingUnitTableSearchBox.placeholder = 'Search growing units';
  growingUnitTableSearchBox.title = 'Search growing units table';

  const growingUnitData = await getGrowingUnitData();
  initGrowingUnitTable(growingUnitData);
  addGrowingUnitDataToMap(growingUnitData);

  firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
      // hide disclaimer/privacy policy modal
      $(`#${DISCLAIMER_MODAL_ID}`).modal('hide');

      // show the leases table and explanation
      document.getElementById('lease-table-div').style.display = 'block';
      document.getElementById('lease-table-explanation').style.display = 'block';

      // hide the "Create Account" message
      document.getElementById('create-account-message').style.display = 'none';

      const leaseData = await getLeaseData();
      initLeaseTable(leaseData);
      addLeaseDataToMap(leaseData);
    } else {
      // show disclaimer/privacy policy modal
      $(`#${DISCLAIMER_MODAL_ID}`).modal('show');

      // hide the leases table and explanation
      document.getElementById('lease-table-div').style.display = 'none';
      document.getElementById('lease-table-explanation').style.display = 'none';

      // show the "Create Account" message
      document.getElementById('create-account-message').style.display = 'block';
    }
  });
})();
