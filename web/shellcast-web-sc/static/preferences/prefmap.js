"use strict";

import {
  addAllMapLayers,
  addHomeExtentButton,
  createBaseLayer,
  createCmuGeoJsonSource,
  createCmuLayer,
  createDaySelector,
  createSimplePopupLayer,
  getBoundaryStyle,
  getGeoJsonAddProbs,
  getGrowingUnitData,
  handleUndef,
  mapBoundingBox,
} from "../map/utils.js";
import { addShellCastLegendControl } from "../map/legends-dayselector.js";
import { INITIAL_ZOOM, MAP_CENTER } from "../map/map_constants.js";

const MAP_ELE_ID = "pref-map";
const PREF_LEGEND_ELE_ID = "pref-shellcast-legend";
const PREF_POPUP_CONTAINER_ELE = document.getElementById("pref-popup");
const PREF_POPUP_CONTENT_ELE = document.getElementById("pref-popup-content");
const closer = document.getElementById("pref-popup-closer");
let prefMap;
let prefCmuLyr;
let prefPopupLyr;
let osmHumanitarianBaseLyr;
let boundingBoxExt;

// ------ Day selector -----
/**
 * Set the style of the preference map polygons based on the day.
 * @param {number} day
 */
function setCmuPolyStyleByDay(day) {
  prefCmuLyr.setStyle((feature) => {
    return getBoundaryStyle(feature, day);
  });
}

/**
 * Add a click listener to the day selector button.
 * @param {object} button
 * @param {number} idx - index of a button object
 */
function addDaySelectorClickListener(button, idx) {
  button.addEventListener("click", () => setCmuPolyStyleByDay(idx + 1));
}

/**
 * Add a day selector to the preference map. When a day is selected, the polygons are styled based on the day.
 * @returns {ol.control.Control}
 */
function addDaySelector() {
  let daySelector = createDaySelector();
  for (let i = 0; i < daySelector.childElementCount; i++) {
    const button = daySelector.children[i];
    addDaySelectorClickListener(button, i);
  }
  return new ol.control.Control({ element: daySelector });
}

// ------ End Day selector -----

async function prefInitMap(growingUnitData) {
  const mapEl = document.getElementById(MAP_ELE_ID);
  const cmuGeoJson = await getGeoJsonAddProbs(growingUnitData);
  const cmuGeoJsonSource = await createCmuGeoJsonSource(cmuGeoJson);

  osmHumanitarianBaseLyr = createBaseLayer();
  prefPopupLyr = createSimplePopupLayer(PREF_POPUP_CONTAINER_ELE);
  prefCmuLyr = await createCmuLayer(cmuGeoJsonSource, "prefCmuLyr");

  prefMap = addAllMapLayers(
    mapEl,
    [osmHumanitarianBaseLyr, prefCmuLyr],
    prefPopupLyr,
    MAP_CENTER,
    INITIAL_ZOOM,
  );

  // Add home extent button
  boundingBoxExt = mapBoundingBox(prefMap);
  addHomeExtentButton(prefMap, boundingBoxExt, prefPopupLyr);

  // Add legend panel
  let legendPanel = addShellCastLegendControl(PREF_LEGEND_ELE_ID);
  prefMap.addControl(legendPanel);

  // Add Day Selector at the left
  let daySelectorControl = addDaySelector();
  prefMap.addControl(daySelectorControl);
  // Set initial style to show
  setCmuPolyStyleByDay(1);

  // Add popup
  prefMap.on("singleclick", function (evt) {
    const feature = prefMap.forEachFeatureAtPixel(
      evt.pixel,
      function (feature) {
        return feature;
      },
    );
    if (feature) {
      let coordinate = evt.coordinate; //default projection is EPSG:3857 you may want to use ol.proj.transform
      const desc = `<div>Lease ID: ${feature.get("lease_id")}
                <br>Today: ${handleUndef(feature.get("prob_1d_perc"))}
                <br>Tomorrow: ${handleUndef(feature.get("prob_2d_perc"))}
                <br>In 2 days: ${handleUndef(feature.get("prob_3d_perc"))}
                </div>`;
      PREF_POPUP_CONTENT_ELE.innerHTML = desc;
      prefPopupLyr.setPosition(coordinate);
    } else {
      prefPopupLyr.setPosition(undefined);
    }
  });
}

// Close popup when the close button is clicked
closer.onclick = function () {
  prefPopupLyr.setPosition(undefined);
  closer.blur();
  return false;
};

// Main
(async () => {
  const growingUnitData = await getGrowingUnitData();
  await prefInitMap(growingUnitData);
})();
