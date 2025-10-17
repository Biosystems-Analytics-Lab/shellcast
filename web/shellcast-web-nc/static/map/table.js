"use strict";
import { handleUndef } from "./utils.js";
//** The ID of the growing unit table element. */
const GROWING_UNIT_TABLE_ID = "growing-unit-table";
/** The ID of the lease table element. */
const LEASE_TABLE_ID = "lease-table";

export function setTableSearchBoxes() {
  // change placeholder text and title attribute for table search boxes
  const leaseTableSearchBox = document.querySelector("#lease-table-div input");
  leaseTableSearchBox.placeholder = "Search leases";
  leaseTableSearchBox.title = "Search leases table";
  const growingUnitTableSearchBox = document.querySelector(
    "#growing-unit-table-div input",
  );
  growingUnitTableSearchBox.placeholder = "Search growing units";
  growingUnitTableSearchBox.title = "Search growing units table";
}

/**
 * Fills the growing unit table with the growing unit records.
 */
export function initGrowingUnitTable(growingUnitData) {
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
export function initLeaseTable(leaseData) {
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
