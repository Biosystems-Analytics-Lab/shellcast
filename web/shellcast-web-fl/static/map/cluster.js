"use strict";
/**
 * OpenLayers cluster styling except "clusterCircleStyle" since it is based on the layer extent.
 * Cluster layer is based on the OpenLayers example:
 * https://openlayers.org/en/latest/examples/clusters-dynamic.html
 */

import { PARTNER_SITE_DOMAINS } from "./map_constants.js";
import { getDomainName } from "./utils.js";

const circleDistanceMultiplier = 1;
const circleFootSeparation = 28;
const circleStartAngle = Math.PI / 2;

const outerCircleFill = new ol.style.Fill({
  // color: "rgba(255, 153, 102, 0.3)",
  color: "rgba(221, 221, 221, 0.5)",
});
const innerCircleFill = new ol.style.Fill({
  // color: "rgba(255, 165, 0, 0.7)",
  color: "rgba(187, 187, 187, 0.7)",
});
const textFill = new ol.style.Fill({
  color: "#fff",
});
const textStroke = new ol.style.Stroke({
  color: "rgba(0, 0, 0, 0.6)",
  width: 3,
});
const innerCircle = new ol.style.Circle({
  radius: 14,
  fill: innerCircleFill,
});
const outerCircle = new ol.style.Circle({
  radius: 20,
  fill: outerCircleFill,
});

export function clusterMemberStyle(feature) {
  const iconDir = "./static/img/map/";
  let domainName = getDomainName(feature.get("url"));
  // let property = feature.get("ID").substring(0, 2);
  let iconUrl;
  if (domainName === PARTNER_SITE_DOMAINS.HB) {
    iconUrl = iconDir + "hb.png";
  } else if (domainName === PARTNER_SITE_DOMAINS.WC) {
    iconUrl = iconDir + "camera.png";
  } else if (domainName === PARTNER_SITE_DOMAINS.VB) {
    iconUrl = iconDir + "vb.png";
  }
  return new ol.style.Style({
    image: new ol.style.Icon({
      src: iconUrl,
    }),
  });
}

export function clusterStyle(feature) {
  const size = feature.get("features").length;
  if (size > 1) {
    return [
      new ol.style.Style({
        image: outerCircle,
      }),
      new ol.style.Style({
        image: innerCircle,
        text: new ol.style.Text({
          text: size.toString(),
          fill: textFill,
          stroke: textStroke,
        }),
      }),
    ];
  }
  const originalFeature = feature.get("features")[0];
  return clusterMemberStyle(originalFeature);
}

export function generatePointsCircle(count, clusterCenter, resolution) {
  const circumference =
    circleDistanceMultiplier * circleFootSeparation * (2 + count);
  let legLength = circumference / (Math.PI * 2); //radius from circumference
  const angleStep = (Math.PI * 2) / count;
  const res = [];
  let angle;

  legLength = Math.max(legLength, 35) * resolution; // Minimum distance to get outside the cluster icon.

  for (let i = 0; i < count; ++i) {
    // Clockwise, like spiral.
    angle = circleStartAngle + i * angleStep;
    res.push([
      clusterCenter[0] + legLength * Math.cos(angle),
      clusterCenter[1] + legLength * Math.sin(angle),
    ]);
  }
  return res;
}
