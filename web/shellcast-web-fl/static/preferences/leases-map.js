const GROWING_UNIT_BOUNDS_PATH = "static/fl_leases_boundary.geojson";
const LEASE_MAP_STYLE = [
  {
    text: "Agricultural Use Zone",
    fill: "rgba(255, 0, 0, 0.1)",
    stroke: "red",
  },
  {
    text: "Individual Lease Site",
    fill: "rgba(0, 0, 255, 0.1)",
    stroke: "blue",
  },
];
const leasesFeatureSource = new ol.source.Vector({
  url: GROWING_UNIT_BOUNDS_PATH,
  format: new ol.format.GeoJSON(),
});

async function getLeasesBoundsGeoJSON() {
  const response = await fetch(GROWING_UNIT_BOUNDS_PATH);
  return response.json();
}

function getLeases(data) {
  let auzLeases = [];
  let indivLeases = [];

  for (let i = 0; i < data.features.length; i++) {
    let feature = data.features[i];
    if (feature.properties.src_merge == "AUZ") {
      if (!auzLeases.includes(feature.properties.PARCEL_NAM)) {
        auzLeases.push(feature.properties.PARCEL_NAM);
      }
    } else if (feature.properties.src_merge == "individual lease") {
      if (!indivLeases.includes(feature.properties.WATERBODY)) {
        indivLeases.push(feature.properties.WATERBODY);
      }
    }
  }
  return { auzLeases: auzLeases.sort(), indivLeases: indivLeases.sort() };
}

async function addDropDowns(leases) {
  // console.log(leases);
  const auzDropdownMenu = document.querySelector("#auzDropdownMenu");
  const indivDropdownMenu = document.querySelector("#indivDropdownMenu");
  leases.auzLeases.forEach((lease) => {
    let dropdownItem = document.createElement("a");
    dropdownItem.classList.add("dropdown-item");
    // dropdownItem.href = "#";
    dropdownItem.textContent = lease;
    auzDropdownMenu.appendChild(dropdownItem);
  });

  leases.indivLeases.forEach((lease) => {
    let dropdownItem = document.createElement("a");
    dropdownItem.classList.add("dropdown-item");
    // dropdownItem.href = "#";
    dropdownItem.textContent = lease;
    indivDropdownMenu.appendChild(dropdownItem);
  });
}

function zoomToAuzLease(map, clickedItem, leaseType) {
  const leasesFeatures = leasesFeatureSource.getFeatures();
  let extent = ol.extent.createEmpty();
  let field = "";
  if (leaseType === "AUZ") {
    field = "PARCEL_NAM";
  } else if (leaseType === "individual lease") {
    field = "WATERBODY";
  }

  for (let i = 0; i < leasesFeatures.length; i++) {
    let curExtent = leasesFeatures[i].getGeometry().getExtent();
    // console.log(curExtent);
    if (leasesFeatures[i].get("src_merge") === leaseType) {
      if (leasesFeatures[i].get(field) === clickedItem) {
        console.log(leasesFeatures[i].get(field));
        ol.extent.extend(extent, curExtent);
      }
    }
  }
  // console.log(extent);
  map.getView().fit(extent, { size: map.getSize(), padding: [50, 50, 50, 50] });
}

function setLeasesFeatureStyle(feature) {
  let fillColor;
  let strokeColor;
  if (feature.get("src_merge") === "AUZ") {
    // fillColor = "rgba(255, 0, 0, 0.1)";
    // strokeColor = "red";
    fillColor = LEASE_MAP_STYLE[0].fill;
    strokeColor = LEASE_MAP_STYLE[0].stroke;
  } else if (feature.get("src_merge") === "individual lease") {
    // fillColor = "rgba(0, 0, 255, 0.1)";
    // strokeColor = "blue";
    fillColor = LEASE_MAP_STYLE[1].fill;
    strokeColor = LEASE_MAP_STYLE[1].stroke;
  }
  return new ol.style.Style({
    fill: new ol.style.Fill({
      color: fillColor,
    }),
    stroke: new ol.style.Stroke({
      color: strokeColor,
      width: 1,
    }),
    text: new ol.style.Text({
      text: feature.get("lease_id"),
      font: "12px Calibri,sans-serif",
      fill: new ol.style.Fill({
        color: "#000",
      }),
      stroke: new ol.style.Stroke({
        color: "#fff",
        width: 3,
      }),
    }),
  });
}

async function createMap() {
  const map = new ol.Map({
    target: "leases-map",
    layers: [
      new ol.layer.Tile({
        source: new ol.source.OSM(),
      }),
      new ol.layer.Vector({
        source: leasesFeatureSource,
        style: setLeasesFeatureStyle,
      }),
    ],
    view: new ol.View({
      center: ol.proj.fromLonLat([-81.5158, 27.6648]),
      zoom: 7,
    }),
  });
  return map;
}

function createLegend() {
  const legend = document.createElement("div");
  legend.id = "lease-legend";
  const div = document.createElement("div");
  for (let item of LEASE_MAP_STYLE) {
    // Legend color
    let spanColor = document.createElement("span");
    spanColor.className = "legend-key";
    spanColor.style.backgroundColor = item.fill;
    spanColor.style.border = "1px solid " + item.stroke;
    // Legend text
    let text = document.createElement("p");
    text.className = "legend-text";
    text.textContent = item.text;
    div.appendChild(spanColor);
    div.appendChild(text);
  }
  legend.appendChild(div);
  return legend;
}

function addLegendControl(map, legend) {
  const legendPanel = new ol.control.Control({
    element: legend,
  });
  map.addControl(legendPanel);
}

function addEvents(map) {
  let auzDropdownMenu = document.getElementById("auzDropdownMenu");
  if (auzDropdownMenu) {
    auzDropdownMenu.addEventListener("click", function (event) {
      const clickedItem = event.target.textContent;
      // console.log(clickedItem);
      zoomToAuzLease(map, clickedItem, "AUZ");
    });
  } else {
    console.log("auzDropdownMenu is null");
  }

  let indivDropdownMenu = document.getElementById("indivDropdownMenu");
  if (indivDropdownMenu) {
    indivDropdownMenu.addEventListener("click", function (event) {
      const clickedItem = event.target.textContent;
      console.log(clickedItem);
      zoomToAuzLease(map, clickedItem, "individual lease");
    });
  } else {
    console.log("indivDropdownMenu is null");
  }
}

async function init() {
  const map = await createMap();
  const legend = createLegend();
  const leaseFeatures = await getLeasesBoundsGeoJSON();
  const leases = getLeases(leaseFeatures);
  await addDropDowns(leases);
  addEvents(map);
  addLegendControl(map, legend);
}

window.onload = function () {
  init();
};
