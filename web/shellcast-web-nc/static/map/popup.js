"use strict";
import { handleUndef } from "./utils.js";

const container = document.getElementById("popup");

export function createShellCastPopupLayer() {
  return new ol.Overlay({
    element: container,
    autoPan: {
      animation: {
        duration: 250,
      },
    },
  });
}

export function generatePopUpContent(feature) {
  return `<div>Growing Unit: ${feature.get("cmu_name")}
                <br>Today: ${handleUndef(feature.get("prob_1d_perc"))}
                <br>Tomorrow: ${handleUndef(feature.get("prob_2d_perc"))}
                <br>In 2 days: ${handleUndef(feature.get("prob_3d_perc"))}
                </div>`;
}
