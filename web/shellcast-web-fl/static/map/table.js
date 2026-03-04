"use strict";
import { handleUndef } from "./utils.js"; //** The ID of the growing unit table element. */
//** The ID of the growing unit table element. */
const GROWING_UNIT_TABLE_ID = "growing-unit-table";
/** The ID of the lease table element. */
const LEASE_TABLE_ID = "lease-table";

export function setTableSearchBoxes() {
  // change placeholder text and title attribute for table search boxes
  const leaseTableSearchBox = document.querySelector("#lease-table-div input");
  leaseTableSearchBox.placeholder = "Search leases";
  leaseTableSearchBox.title = "Search leases table";
  const growingUnitTableSearchBox = document.querySelector("#growing-unit-table-div input");
  growingUnitTableSearchBox.placeholder = "Search growing units";
  growingUnitTableSearchBox.title = "Search growing units table";
}

/**
 * Fills the growing unit table with the growing unit records.
 */
export function initGrowingUnitTable(growingUnitData) {
  const rows = [];
  for (let [cmu, data] of Object.entries(growingUnitData)) {
    let prob_1d_perc =
      handleUndef(data.prob_1d_perc).length > 0
        ? `${handleUndef(data.prob_1d_perc)}`
        : "Out of Season";
    const rowData = {
      cmu_name: cmu,
      sh_name: `${data.sh_name}: ${data.sh_id}`,
      rainfall_desc: data.rainfall_desc,
      season: data.season,
      prob_1d_perc: prob_1d_perc,
    };
    rows.push(rowData);
  }
  $(`#${GROWING_UNIT_TABLE_ID}`).bootstrapTable("load", rows);
}

/**
 * Fills the lease table with lease records.
 */
export function initLeaseTable(cmusData) {
  const rows = [];
  for (let cmu of cmusData) {
    const rowData = {
      lease_id: cmu.lease_id,
      sh_name: `${cmu.sh_name}: ${cmu.sh_id}`,
      prob_1d_perc: `${handleUndef(cmu.prob_1d_perc)}`,
    };
    rows.push(rowData);
  }
  $(`#${LEASE_TABLE_ID}`).bootstrapTable("load", rows);
}
