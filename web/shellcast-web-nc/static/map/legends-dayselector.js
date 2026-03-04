"use strict";

import { colorPalette, strToEl } from "./utils.js";
import { setCmuPolyStyleByDay } from "./map.js";

/** The text and colors used for the legend. */
const LEGEND_SCALE = [
  { text: "No data", color: colorPalette.COLOR_NULL },
  { text: "Very Low", color: colorPalette.COLOR_VERY_LOW },
  { text: "Low", color: colorPalette.COLOR_LOW },
  { text: "Moderate", color: colorPalette.COLOR_MODERATE },
  { text: "High", color: colorPalette.COLOR_HIGH },
  { text: "Very High", color: colorPalette.COLOR_VERY_HIGH },
];

/**
 * Create CMU closure probability legend on map
 * @returns {HTMLDivElement}
 */
class ShellCastLegend {
  constructor() {}

  create() {
    const legend = document.createElement("div");
    legend.id = "shellcast-legend";
    for (let step of LEGEND_SCALE) {
      const textDiv = strToEl(`<div id="shellcast-legend-txt">${step.text}</div>`);
      legend.appendChild(textDiv);
      const colorDiv = document.createElement("div");
      colorDiv.id = "shellcast-legend-color";
      colorDiv.style.backgroundColor = step.color;
      legend.appendChild(colorDiv);
    }
    return legend;
  }
}

/**
 * Create closure day button selector on map.
 * @returns {Element}
 */
export function createDaySelector() {
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
    button.addEventListener("click", () => {
      setCmuPolyStyleByDay(i + 1);
    });
  }
  return daySelector;
}

export { ShellCastLegend };
