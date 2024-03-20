"use strict";

/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = "closure-map";
/** Options for the map. */
const mapCenter = [-76.315151, 35.007934];
//** The ID of the growing unit table element. */
const GROWING_UNIT_TABLE_ID = "growing-unit-table";
/** The ID of the lease table element. */
const LEASE_TABLE_ID = "lease-table";
/** The path to the growing unit boundaries file. */
const GROWING_UNIT_BOUNDS_PATH = "static/cmu_bounds.geojson";
/** The color used to fill in growing units without a closure probability. */
const COLOR_NULL = "transparent";
// /** The color used to fill in growing units with a Very Low risk. */
const COLOR_VERY_LOW = "#4eb265";
// /** The color used to fill in growing units with a Low risk. */
const COLOR_LOW = "#fecc5c";
// /** The color used to fill in growing units with a Moderate risk. */
const COLOR_MODERATE = "#fd8d3c";
// /** The color used to fill in growing units with a High risk. */
const COLOR_HIGH = "#e31a1c";
// const COLOR_HIGH = 'rgba(227, 26, 28, 0.7)';

// /** The color used to fill in growing units with a Very High risk. */
// const COLOR_VERY_HIGH = '#8B0000';
const COLOR_VERY_HIGH = "rgba(139, 0, 0, 0.7)";

/** The text and colors used for the legend. */
const LEGEND_SCALE = [
  { text: "No data", color: COLOR_NULL },
  { text: "Very Low", color: COLOR_VERY_LOW },
  {
    text: "Low",
    color: COLOR_LOW,
  },
  { text: "Moderate", color: COLOR_MODERATE },
  { text: "High", color: COLOR_HIGH },
  {
    text: "Very High",
    color: COLOR_VERY_HIGH,
  },
];

// a reference to the Google map object
let map;
// a reference to the Google map info window
let mapInfoWindow;
// CMU layer created from GeoJson
let cmuLyr;
// CMU closure probability popup overlay
let popupOverlay;
// Lease place marker
let markerSvg =
  '<svg id="marker" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="30px" height="30px" viewBox="0 0 30 30" enable-background="new 0 0 30 30" xml:space="preserve">' +
  '<path fill="white" stroke="black" d="M22.906,10.438c0,4.367-6.281,14.312-7.906,17.031c-1.719-2.75-7.906-12.665-7.906-17.031S10.634,2.531,15,2.531S22.906,6.071,22.906,10.438z"/>' +
  '<circle fill="black" cx="15" cy="10.677" r="3.291"/></svg>';
// Elements that make up the popup.
const container = document.getElementById("popup");
const content = document.getElementById("popup-content");

/**
 * Returns a value of the risk factor.
 * @param {number} value the value with probability
 */
function handleUndef(value) {
  let flag = "";
  if (value === 1) flag = "Very Low";
  if (value === 2) flag = "Low";
  if (value === 3) flag = "Moderate";
  if (value === 4) flag = "High";
  if (value === 5) flag = "Very High";
  return value || value === 0 ? flag : "-";
}

/**
 * Returns a color from the color scale based on the given value.
 * @param {number} value the value to get a color for
 */
function getColor(value) {
  let color = "transparent";
  if (value === 1) color = COLOR_VERY_LOW;
  if (value === 2) color = COLOR_LOW;
  if (value === 3) color = COLOR_MODERATE;
  if (value === 4) color = COLOR_HIGH;
  if (value === 5) color = COLOR_VERY_HIGH;
  return color;
}

/**
 * Fetches the growing unit data from the server and returns it.
 */
async function getGrowingUnitData() {
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
async function getLeaseData() {
  const res = await authorizedFetch("/leaseProbs");
  if (res.ok) {
    return await res.json();
  }
  console.log("Problem retrieving lease data.");
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
      prob_3d_perc: `${handleUndef(data.prob_3d_perc)}`,
    };
    rows.push(rowData);
  }
  $(`#${GROWING_UNIT_TABLE_ID}`).bootstrapTable("load", rows);
}

/**
 * Fills the lease table with lease records.
 */
function initLeaseTable(leaseData) {
  const rows = [];
  for (let lease of leaseData) {
    const rowData = {
      lease_id: lease.lease_id,
      prob_1d_perc: `${handleUndef(lease.prob_1d_perc)}`,
      prob_2d_perc: `${handleUndef(lease.prob_2d_perc)}`,
      prob_3d_perc: `${handleUndef(lease.prob_3d_perc)}`,
    };
    rows.push(rowData);
  }
  $(`#${LEASE_TABLE_ID}`).bootstrapTable("load", rows);
}

/**
 * @param {string} htmlStr the HTML string to create an element from
 * @return {Element} a DOM element created from the given string
 */
function strToEl(htmlStr) {
  const template = document.createElement("template");
  template.innerHTML = htmlStr.trim();
  return template.content.firstChild;
}

/**
 * Create CMU closure probability legend on map
 * @returns {HTMLDivElement}
 */
function createLegend() {
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.style.border = "1px solid black";
  legend.style.display = "grid";
  legend.style.gridTemplateColumns = "auto 1rem";
  legend.style.marginLeft = "10px";
  legend.style.textAlign = "center";
  legend.style.lineHeight = "2rem";
  legend.style.fontSize = "1rem";
  // add text and colors to legend
  for (let step of LEGEND_SCALE) {
    const textDiv = strToEl(`<div>${step.text}</div>`);
    textDiv.style.paddingLeft = "3px";
    textDiv.style.paddingRight = "3px";
    textDiv.style.backgroundColor = "white";
    legend.appendChild(textDiv);
    const colorDiv = document.createElement("div");
    colorDiv.style.backgroundColor = step.color;
    colorDiv.style.borderLeft = "1px solid black";
    colorDiv.style.borderTop = "1px solid black";
    legend.appendChild(colorDiv);
  }
  return legend;
}

/**
 * Create closure day button selector on map.
 * @param map
 * @returns {Element}
 */
function createDaySelector(map) {
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
  for (let i = 0; i < daySelector.childElementCount; i++) {
    const button = daySelector.children[i];
    // button.addEventListener('click', () => map.data.setStyle(styleFeatureBasedOnDay(i + 1)));
    button.addEventListener("click", () => setCmuPolyStyleByDay(i + 1));
  }
  return daySelector;
}

/**
 * Add GeoJson CMU polygon feature to closure probabilities properties.
 * @param growingUnitData
 * @returns {Promise<any>}
 */
async function getGeoJsonAddProbs(growingUnitData) {
  let data = fetch(GROWING_UNIT_BOUNDS_PATH)
    .then((response) => response.json())
    .then((response) => {
      response.features.forEach((feature) => {
        for (let [cmuName, data] of Object.entries(growingUnitData)) {
          if (feature.properties.cmu_name == cmuName) {
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
  return data;
}

/**
 * Set CMY polygon layer symbol style based on "prob_{day}d_perc" value.
 * @param day
 */
function setCmuPolyStyleByDay(day) {
  cmuLyr.setStyle((feature) => {
    let fillColor;
    const value = feature.get(`prob_${day}d_perc`);
    fillColor = getColor(value);
    return new ol.style.Style({
      fill: new ol.style.Fill({
        color: fillColor,
      }),
      stroke: new ol.style.Stroke({
        color: "rgba(255, 255, 255, 0.5)",
        width: 1,
      }),
      text: new ol.style.Text({
        text: feature.get("cmu_name"),
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
  });
}

/**
 * Create map.
 * 1. Add closure probabilities to GeoJson CMU polygon features.
 * 2. Create GeoJson ol.sourceVector
 * 3. Create polygon layer from GeoJson source data.
 * 4. Set CMU polygon style for today's CMU closure probability.
 * 5. Set map view to CMU polygon extent.
 * 6. Set Esri satellite imagery tile layer.
 * 7. Set CMU closure probabilities popup layer.
 * 8. Set map.
 * 9. Set legend.
 * 10. Set CMU closure probability day selector.
 * @param growingUnitData
 * @returns {Promise<void>}
 */
async function initMap(growingUnitData) {
  const mapEl = document.getElementById(MAP_EL_ID);
  const cmuGeoJson = await getGeoJsonAddProbs(growingUnitData); // #1
  // console.log(cmuGeoJson);
  const cmuGeoJsonSource = new ol.source.Vector({
    features: new ol.format.GeoJSON().readFeatures(cmuGeoJson, {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    }),
  }); // #2

  cmuLyr = new ol.layer.Vector({
    title: "CMU",
    name: "cmu",
    opacity: 0.7,
    source: cmuGeoJsonSource,
  }); // #3

  setCmuPolyStyleByDay(1); // #4

  cmuLyr.getSource().once("change", function () {
    map.getView().fit(cmuLyr.getSource().getExtent());
  }); // #5

  // const worldImagery = new ol.layer.Tile({
  //     source: new ol.source.XYZ({
  //         attributions: ['Powered by Esri',
  //             'Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'],
  //         attributionsCollapsible: false,
  //         url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  //         // maxZoom: 8
  //     })
  // }); // #6

  // const osm = new ol.layer.Tile({
  //     source: new ol.source.OSM()
  // }); // #6

  const osmHumanitarian = new ol.layer.Tile({
    source: new ol.source.OSM({
      source: "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    }),
  }); // #6

  popupOverlay = new ol.Overlay({
    element: container,
    autoPan: {
      animation: {
        duration: 250,
      },
    },
  }); // #7

  map = new ol.Map({
    target: mapEl,
    layers: [osmHumanitarian, cmuLyr],
    overlays: [popupOverlay],
    view: new ol.View({
      center: ol.proj.fromLonLat(mapCenter),
      zoom: 8,
    }),
  }); // # Set map

  const legend = createLegend();
  let legendPanel = new ol.control.Control({
    element: legend,
  });
  map.addControl(legendPanel); // #8

  const daySelector = createDaySelector(map);
  let daySelectorPanel = new ol.control.Control({
    element: daySelector,
  });
  map.addControl(daySelectorPanel); // #9

  map.on("singleclick", function (evt) {
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
      return feature;
    });
    if (feature && feature.get("type") != "Point") {
      console.log(feature);
      let coordinate = evt.coordinate; //default projection is EPSG:3857 you may want to use ol.proj.transform
      const desc = `<div>Growing Unit: ${feature.get("cmu_name")}
                <br>Today: ${handleUndef(feature.get("prob_1d_perc"))}
                <br>Tomorrow: ${handleUndef(feature.get("prob_2d_perc"))}
                <br>In 2 days: ${handleUndef(feature.get("prob_3d_perc"))}
                </div>`;
      content.innerHTML = desc;
      popupOverlay.setPosition(coordinate);
    } else {
      popupOverlay.setPosition(undefined);
    }
  });
}

/**
 * Create point layer for user's registered lease locations.
 * @param leaseData
 * @returns {Promise<*>}
 */
async function createLeasePointFeatures(leaseData) {
  let features = leaseData.map((item) => {
    const leaseInfoContent = `
          <div>Lease ID: ${item.lease_id}
          <br>Today: ${handleUndef(item.prob_1d_perc)}
          <br>Tomorrow: ${handleUndef(item.prob_2d_perc)}
          <br>In 2 days: ${handleUndef(item.prob_3d_perc)}
          </div>
        `;
    let longitude = item.longitude,
      latitude = item.latitude,
      iconFeature = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([longitude, latitude])),
        desc: leaseInfoContent,
        type: "Point",
      }),
      iconStyle = new ol.style.Style(
        /** @type {olx.style.IconOptions} */ {
          image: new ol.style.Icon({
            anchor: [0.5, 1],
            anchorXUnits: "fraction",
            anchorYUnits: "fraction",
            // src: 'https://openlayers.org/en/latest/examples/data/icon.png'
            src: "data:image/svg+xml," + encodeURI(markerSvg),
            scale: 2,
            imgSize: [26, 26],
          }),
        },
      );

    iconFeature.setStyle(iconStyle);
    return iconFeature;
  });
  return features;
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
    source: leasePntSource,
  });
  map.addLayer(leasePntLyr);

  // Add mouseover event for popup
  map.on("pointermove", function (evt) {
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
      return feature;
    });
    if (feature && feature.get("type") == "Point") {
      let coordinate = evt.coordinate; //default projection is EPSG:3857 you may want to use ol.proj.transform
      content.innerHTML = feature.get("desc");
      popupOverlay.setPosition(coordinate);
    } else {
      popupOverlay.setPosition(undefined);
    }
  });
}

// Main
(async () => {
  const growingUnitData = await getGrowingUnitData();
  await initMap(growingUnitData);

  // change placeholder text and title attribute for table search boxes
  const leaseTableSearchBox = document.querySelector("#lease-table-div input");
  leaseTableSearchBox.placeholder = "Search leases";
  leaseTableSearchBox.title = "Search leases table";
  const growingUnitTableSearchBox = document.querySelector(
    "#growing-unit-table-div input",
  );
  growingUnitTableSearchBox.placeholder = "Search growing units";
  growingUnitTableSearchBox.title = "Search growing units table";
  initGrowingUnitTable(growingUnitData);

  firebase.auth().onAuthStateChanged(async (user) => {
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
      console.log(leaseData);
      initLeaseTable(leaseData);
      createLeasePointFeatures(leaseData).then((features) => {
        console.log(features);
        addLeaseDataToMap(features);
      });
      // addLeaseDataToMap(leaseData);
    } else {
      // show disclaimer/privacy policy modal
      $(`#${DISCLAIMER_MODAL_ID}`).modal("show");

      // hide the leases table and explanation
      document.getElementById("lease-table-div").style.display = "none";
      document.getElementById("lease-table-explanation").style.display = "none";

      // show the "Create Account" message
      document.getElementById("create-account-message").style.display = "block";
    }
  });
})();
