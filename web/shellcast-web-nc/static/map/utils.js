/** The path to the growing unit boundaries file. */
const GROWING_UNIT_BOUNDS_PATH = "static/cmu_bounds.geojson";

export const markerSvg =
    '<svg id="marker" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="30px" height="30px" viewBox="0 0 30 30" enable-background="new 0 0 30 30" xml:space="preserve">' +
    '<path fill="white" stroke="black" d="M22.906,10.438c0,4.367-6.281,14.312-7.906,17.031c-1.719-2.75-7.906-12.665-7.906-17.031S10.634,2.531,15,2.531S22.906,6.071,22.906,10.438z"/>' +
    '<circle fill="black" cx="15" cy="10.677" r="3.291"/></svg>';
export const colorPalette = {
    "COLOR_NULL": "transparent",
    "COLOR_VERY_LOW": "#4eb265",
    "COLOR_LOW": "#fecc5c",
    "COLOR_MODERATE": "#fd8d3c",
    "COLOR_HIGH": "#e31a1c",
    "COLOR_VERY_HIGH": "rgba(139, 0, 0, 0.7)"
}

/**
 * Returns a color from the color scale based on the given value.
 * @param {number} value the value to get a color for
 */
export function getColor(value) {
    let color = colorPalette.COLOR_NULL
    if (value === 1) color = colorPalette.COLOR_VERY_LOW;
    if (value === 2) color = colorPalette.COLOR_LOW;
    if (value === 3) color = colorPalette.COLOR_MODERATE;
    if (value === 4) color = colorPalette.COLOR_HIGH;
    if (value === 5) color = colorPalette.COLOR_VERY_HIGH;
    return color;
}

/**
 * Returns a value of the risk factor.
 * @param {number} value the value with probability
 */
export function handleUndef(value) {
    let flag = "";
    if (value === 1) flag = "Very Low";
    if (value === 2) flag = "Low";
    if (value === 3) flag = "Moderate";
    if (value === 4) flag = "High";
    if (value === 5) flag = "Very High";
    return value || value === 0 ? flag : "-";
}

/**
 * @param {string} htmlStr the HTML string to create an element from
 * @return {Element} a DOM element created from the given string
 */
export let strToEl = function (htmlStr) {
    const template = document.createElement("template");
    template.innerHTML = htmlStr.trim();
    return template.content.firstChild;
}


export function fillBoundaryColor(colorValue, featureName) {
    return new ol.style.Style({
        fill: new ol.style.Fill({
            color: getColor(colorValue),
        }),
        stroke: new ol.style.Stroke({
            color: "rgba(255, 255, 255, 0.5)",
            width: 1,
        }),
        text: new ol.style.Text({
            text: featureName,
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
}

// ================== API requests ==================
/**
 * Fetches the growing unit data from the server and returns it.
 */
export async function getGrowingUnitData() {
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
export async function getLeaseData() {
    const res = await authorizedFetch("/leaseProbs");
    if (res.ok) {
        return await res.json();
    }
    console.log("Problem retrieving lease data.");
    console.log(res);
    return null;
}

/**
 * Add GeoJson CMU polygon feature to closure probabilities properties.
 * @param growingUnitData
 * @returns {Promise<any>}
 */
export async function getGeoJsonAddProbs(growingUnitData) {
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

export function getBoundaryStyle(feature, day) {
    let value = feature.get(`prob_${day}d_perc`);
    let featureName = feature.get("cmu_name")
    return fillBoundaryColor(value, featureName);
}


