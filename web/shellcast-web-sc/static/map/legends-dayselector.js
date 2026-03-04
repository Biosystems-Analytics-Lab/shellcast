"use strict";

import { strToEl } from "./utils.js";
import {
  CAMERA_ICON,
  HOWS_THE_BEACH_ICON,
  LEGEND_SCALE,
  VISIT_BEACHES_ICON,
} from "./map_constants.js";

/**
 * Create CMU closure probability legend on map
 * @returns {HTMLDivElement}
 */
export function addShellCastLegendControl(legendID) {
  const legend = document.createElement("div");
  legend.id = legendID;
  for (let step of LEGEND_SCALE) {
    const textDiv = strToEl(`<div id="shellcast-legend-txt">${step.text}</div>`);
    legend.appendChild(textDiv);
    const colorDiv = document.createElement("div");
    colorDiv.id = "shellcast-legend-color";
    colorDiv.style.backgroundColor = step.color;
    legend.appendChild(colorDiv);
  }
  return new ol.control.Control({ element: legend });
}

// export function addShellCastLegend(legendID) {
//   const shellCastLegend = new ShellCastLegend();
//   const legendLeft = shellCastLegend.create(legendID);
//   return new ol.control.Control({ element: legendLeft });
// }

export function addPartnerSitesLegendControl(partnerSitesLegendID) {
  const partnerSitesLegend = document.createElement("div");
  partnerSitesLegend.id = partnerSitesLegendID;
  partnerSitesLegend.innerHTML = `
    <div id="partner-sites-legend">
      <div id="accordion" style="width: 20rem">
        <div class="card">
          <div class="card-header text-center" id="headingOne" style="padding: .1rem;">
            <h5 class="mb-0">
              <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true"
                aria-controls="collapseOne">
                Legend
              </button>
            </h5>
          </div>
          <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
            <div class="card-body">
              <h6>ShellCast</h6>
              <small>The legend for ShellCast is shown to the left. The forecast date can be changed by clicking
              "Today", "Tomorrow" and "In 2 days".</small>
              <div style="line-height: 20px; vertical-align: middle; padding-top: 16px;">
                <input type="checkbox" id="partner-sites-legend-checkbox" role="button"
                  style="width: 20px;height: 20px; vertical-align: middle;" checked>
                <label class="form-check-label" for="partner-sites-legend-checkbox"><span>
                    <h6>&emsp13;Partner Sites</h6>
                  </span></label>
              </div>
              <table id="partner-sites-legend-table" class="partner-legend">
                <tr>
                  <td class="legend-icon"><img src=${HOWS_THE_BEACH_ICON} alt="How's the Beach"></td>
                  <td><small>How's the Beach Sites</small></td>
                </tr>
                <tr>
                  <td class="legend-icon"><img src=${VISIT_BEACHES_ICON} alt="Visit Beachs"></td>
                  <td><small>Beach Conditions Reporting System</small></td>
                </tr>
                <tr>
                  <td class="legend-icon"><img src=${CAMERA_ICON} alt="WebCOOS"</td>
                  <td><small>WebCOOS Camera Sites</small></td>
                </tr>
            </table>
            </div>
          </div>
        </div>
      </div>
    </div>`;
  return new ol.control.Control({ element: partnerSitesLegend });
}

// function addPartnerSitesLegend() {
//   const partnerSitesLegend = document.createElement("div");
//   partnerSitesLegend.id = legendID;
//   return new ol.control.Control({
//     element: partnerAppLyrLegend,
//   });
// }

// export let partnerAppLyrLegend = document.createElement("div");
// partnerAppLyrLegend.innerHTML = `
// <div id="partner-sites-legend">
//   <div id="accordion" style="width: 20rem">
//     <div class="card">
//       <div class="card-header text-center" id="headingOne" style="padding: .1rem;">
//         <h5 class="mb-0">
//           <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true"
//             aria-controls="collapseOne">
//             Legend
//           </button>
//         </h5>
//       </div>
//       <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
//         <div class="card-body">
//           <h6>ShellCast</h6>
//           <small>The legend for ShellCast is shown to the left. The forecast date can be changed by clicking
//           "Today", "Tomorrow" and "In 2 days".</small>
//           <div style="line-height: 20px; vertical-align: middle; padding-top: 16px;">
//             <input type="checkbox" id="partner-legend" role="button"
//               style="width: 20px;height: 20px; vertical-align: middle;" checked>
//             <label class="form-check-label" for="partner-legend"><span>
//                 <h6>&emsp13;Partner Sites</h6>
//               </span></label>
//           </div>
//           <table id="legend-table" class="partner-legend">
//             <tr>
//               <td class="legend-icon"><img src=${HOWS_THE_BEACH_ICON} alt="How's the Beach"></td>
//               <td><small>How's the Beach Sites</small></td>
//             </tr>
//             <tr>
//               <td class="legend-icon"><img src=${VISIT_BEACHES_ICON} alt="Visit Beachs"></td>
//               <td><small>Beach Conditions Reporting System</small></td>
//             </tr>
//             <tr>
//               <td class="legend-icon"><img src=${CAMERA_ICON} alt="WebCOOS"</td>
//               <td><small>WebCOOS Camera Sites</small></td>
//             </tr>
//         </table>
//         </div>
//       </div>
//     </div>
//   </div>
// </div>`;
