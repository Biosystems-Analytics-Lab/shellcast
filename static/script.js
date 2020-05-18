'use strict';

/** The HTML element that holds the map. */
const MAP_EL_ID = "map";
/** Options for the map. */
const MAP_OPTIONS = {
  center: {
    lat: 35.1013734,
    lng: -76.5595641
  },
  zoom: 8
};

let map;

/**
 * Initializes the main map.
 */
function initMap() {
  map = new google.maps.Map(document.getElementById(MAP_EL_ID), MAP_OPTIONS);
}
