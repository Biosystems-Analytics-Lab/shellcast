"use strict";
import {auth, authorizedFetch} from "../common/common.js";
import {onAuthStateChanged} from "https://www.gstatic.com/firebasejs/10.12.3/firebase-auth.js";

import {getGrowingUnitData, getLeaseData, getGeoJsonAddProbs, getBoundaryStyle, markerSvg, handleUndef} from './utils.js';
import {ShellCastLegend, createDaySelector} from './legends-dayselector.js';
import {initGrowingUnitTable, initLeaseTable, setTableSearchBoxes} from './table.js';
import {createShellCastPopupLayer, generatePopUpContent} from './popup.js';


const shellCastLegend = new ShellCastLegend();
/** The ID of the HTML element that holds the map. */
const MAP_EL_ID = "closure-map";
/** Options for the map. */
const mapCenter = [-76.315151, 35.007934];
// a reference to the Google map object
let map;
// CMU layer created from GeoJson
let cmuLyr;
// CMU closure probability popup overlay
let popupOverlay;
// Elements that make up the popup.
const content = document.getElementById("popup-content");


//================== Map functions ==================
function createCmuGeoJsonSource(cmuGeoJson) {
    return new ol.source.Vector({
        features: new ol.format.GeoJSON().readFeatures(cmuGeoJson, {
            dataProjection: "EPSG:4326",
            featureProjection: "EPSG:3857",
        }),
    });
}

function createCmuLayer(cmuGeoJsonSource) {
    return new ol.layer.Vector({
        title: "CMU",
        name: "cmu",
        opacity: 0.7,
        source: cmuGeoJsonSource,
        extent: cmuGeoJsonSource.getExtent(),
        style: function (feature) {
            return getBoundaryStyle(feature, 1)
        }
    });
}

/**
 * Set CMY polygon layer symbol style based on "prob_{day}d_perc" value.
 * @param day
 */
export function setCmuPolyStyleByDay(day) {
    cmuLyr.setStyle((feature) => {
        console.log(day);
        return getBoundaryStyle(feature, day);
    });
}


function setBoundingBoxMapExtent() {
    cmuLyr.getSource().once("change", function () {
        map.getView().fit(cmuLyr.getSource().getExtent());
    });
}

function createBaseLayer() {
    return new ol.layer.Tile({
        source: new ol.source.OSM({
            source: "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        }),
    });
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
    cmuLyr = createCmuLayer(cmuGeoJsonSource);
    setBoundingBoxMapExtent();
    const osmHumanitarian = createBaseLayer()
    popupOverlay = createShellCastPopupLayer()

    map = new ol.Map({
        target: mapEl,
        layers: [osmHumanitarian, cmuLyr],
        overlays: [popupOverlay],
        view: new ol.View({
            center: ol.proj.fromLonLat(mapCenter),
            zoom: 8,
        }),
    }); // # Set map

    const legendLeft = shellCastLegend.create();
    const legendPanel = new ol.control.Control({
        element: legendLeft,
    });
    map.addControl(legendPanel); // #8

    // ================== Add day selector panel ==================
    const daySelector = createDaySelector();

    // Add event listener to day selector buttons
    (function addDaySelectorEventListeners() {
        for (let i = 0; i < daySelector.childElementCount; i++) {
            const button = daySelector.children[i];
            button.addEventListener("click", () => setCmuPolyStyleByDay(i + 1));
        }
    })();

    // ================== Add day selector panel to map ==================
    let daySelectorPanel = new ol.control.Control({
        element: daySelector,
    });
    map.addControl(daySelectorPanel);

    // ================== Add popup event ==================
    map.on("singleclick", function (evt) {
        const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
            return feature;
        });
        if (feature && feature.get("type") != "Point") {
            console.log(feature);
            let coordinate = evt.coordinate; //default projection is EPSG:3857 you may want to use ol.proj.transform
            content.innerHTML = generatePopUpContent(feature);
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
    setTableSearchBoxes()
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
