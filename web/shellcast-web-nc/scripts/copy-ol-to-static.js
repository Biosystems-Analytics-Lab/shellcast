/**
 * Copies only the required OpenLayers files (ol.js and ol.css) from node_modules
 * into static/lib so that deployment does not include the full node_modules.
 * Run from shellcast-web-nc: npm run build
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OL = path.join(ROOT, "node_modules", "ol");
const OUT = path.join(ROOT, "static", "lib");

const files = [
  { src: path.join(OL, "ol.css"), dest: path.join(OUT, "ol.css") },
  { src: path.join(OL, "dist", "ol.js"), dest: path.join(OUT, "ol.js") },
];

if (!fs.existsSync(OL)) {
  console.error("OpenLayers not found. Run: npm install");
  process.exit(1);
}

fs.mkdirSync(OUT, { recursive: true });

for (const { src, dest } of files) {
  if (!fs.existsSync(src)) {
    console.error("Missing:", src);
    process.exit(1);
  }
  fs.copyFileSync(src, dest);
  console.log("Copied:", path.relative(ROOT, src), "->", path.relative(ROOT, dest));
}

console.log("Build complete. static/lib contains only required OpenLayers files.");
