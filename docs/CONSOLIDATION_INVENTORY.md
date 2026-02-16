# ShellCast Web Apps: Consolidation Inventory

This document inventories **routes**, **JavaScript functions**, **templates (HTML)**, and **CSS** across the three state apps (NC, FL, SC) to support a possible future consolidation into a single web service with state-based routing and shared vs state-specific logic.

**Conventions:**
- **Same** = Same path/name and same or equivalent role in all states where present.
- **FL/SC only** or **NC only** = Present in those states only.
- **Unique to X** = Logic or structure differs meaningfully in that state.

---

## 1. Routes (Python)

### 1.1 Page routes (`@pages.route`)

| Path | NC | FL | SC | Notes |
|------|----|----|-----|------|
| `/` | ✓ | ✓ | ✓ | **Same** – index |
| `/map` | ✓ | ✓ | ✓ | **Same** |
| `/about` | ✓ | ✓ | ✓ | **Same** |
| `/how-it-works` | ✓ | ✓ | ✓ | **Same** |
| `/notification-service` | ✓ | ✓ | ✓ | **Same** |
| `/faqs` | ✓ | ✓ | ✓ | **Same** |
| `/preferences` | ✓ | ✓ | ✓ | **Same** |
| `/signin` | ✓ | ✓ | ✓ | **Same** |
| `/feedback` | ✓ | ✓ | ✓ | **Same** |
| `/u/<token>` | — | ✓ | ✓ | **FL, SC only** – one-click unsubscribe; NC has no this route |

### 1.2 API routes (`@api.route`)

| Path | NC | FL | SC | Notes |
|------|----|----|-----|------|
| `/user-info` (GET/POST) | ✓ | ✓ | ✓ | **Same** |
| `/delete-account` | ✓ | ✓ | ✓ | **Same** |
| `/lease-probs` | ✓ | ✓ | ✓ | **Same** |
| `/growing-unit-probs` | ✓ | ✓ | ✓ | **Same** |
| `/leases` (GET/POST/DELETE) | ✓ | ✓ | ✓ | **Same** |
| `/search-leases` (POST) | ✓ | ✓ | ✓ | **Same** |
| `/api/bandwidth/callback` | ✓ | — | — | **NC only** – primary Bandwidth webhook; NC routes FL/SC callbacks |
| `/api/bandwidth/log-event` | ✓ | — | — | **NC only** – centralized SMS event logging |
| `/bandwidth/callback/internal` | — | ✓ | ✓ | **FL, SC only** – receive forwarded callbacks from NC |

### 1.3 Cron routes (`@cron.route`)

| Path | NC | FL | SC | Notes |
|------|----|----|-----|------|
| `/send-bandwidth-message` | ✓ | ✓ | ✓ | **Same** – FL/SC triggered by NC |
| `/test/send-sms` | ✓ | ✓ | ✓ | **Same** – dev/test |
| `/cron/smoke-test-sms` | ✓ | — | — | **NC only** |

---

## 2. JavaScript: Same vs state-specific

### 2.1 Files present by state

| File (under static/) | NC | FL | SC | Role |
|----------------------|----|----|-----|------|
| `common/common.js` | ✓ | ✓ | ✓ | Auth navbar, `authorizedFetch` |
| `common/js/notification_prefs.js` | ✓ | ✓ | ✓ | Notification preferences form |
| `preferences/preferences.js` | ✓ | ✓ | ✓ | Preferences page logic |
| `map/map.js` | ✓ | ✓ | ✓ | Main map init and layers |
| `map/utils.js` | ✓ | ✓ | ✓ | GeoJSON, styles, map helpers |
| `map/popup.js` | ✓ | ✓ | ✓ | Popup content builders |
| `map/table.js` | ✓ | ✓ | ✓ | Table search and init |
| `map/cluster.js` | ✓ | ✓ | ✓ | Cluster styling |
| `map/legends-dayselector.js` | ✓ | ✓ | ✓ | Legend and day selector UI |
| `map/map_constants.js` | ✓ | ✓ | ✓ | Map constants (paths, IDs, etc.) |
| `signin/signin.js` | ✓ | ✓ | ✓ | Sign-in page |
| `preferences/prefmap.js` | — | — | ✓ | **SC only** – preferences page map |
| `preferences/leases-map.js` | — | ✓ | — | **FL only** – FL lease boundaries / dropdowns |

### 2.2 Functions: same name, same role (candidates for shared code)

These exist in all three apps with the same purpose; only implementation details may differ.

**common.js**
- `handleNavbarSignedIn`, `handleNavbarSignedOut`, `authorizedFetch`

**notification_prefs.js**
- `validateEmail`, `validatePhoneNumber`, `maskPhoneNumber`, `initNotificationForm` (export)

**preferences.js**
- `getProfileInfo`, `buildLeaseInfoEls`, `createLeaseInfoEl`, `initLeaseInfoEl`
- `addLease`, `deleteLease`, `searchLeases`, `clearLeaseSearch`, `searchLeasesOnDelay`
- `deleteAccount`, `handleSignedInUser`, `handleSignedOutUser`

**map (map.js, utils.js, popup.js, table.js, cluster.js, legends-dayselector.js)**
- `createShellCastPopupLayer`, `popupContent`, `partnerAppLyrPopupContent`
- `setTableSearchBoxes`, `initGrowingUnitTable`, `initLeaseTable`
- `clusterMemberStyle`, `clusterStyle`, `generatePointsCircle`
- `handleUndef`, `getDomainName`, `getBoundaryStyle`, `createDaySelector`
- `createCmuGeoJsonSource`, `createCmuLayer` (signatures differ NC vs FL/SC)
- `createPartnerAppLayer`, `createClusterCirclesLyr`, `clusterCircleStyle`, `partnerLegendCheckbox`
- `setCmuPolyStyleByDay`, `addDaySelectorClickListener`, `addDaySelector` (duplicated in SC map.js and prefmap.js)
- `initMap`, `createLeasePointFeatures`, `addLeaseDataToMap`

### 2.3 Functions / files unique to a state

**NC only**
- **Map structure:** NC `map.js` uses `createCmuLayer(cmuGeoJsonSource)` (no layer name); no `createBaseLayer`/`createSimplePopupLayer` in utils – structure differs from FL/SC.
- **utils.js:** `getGrowingUnitData()`, `getLeaseData()` (fetch helpers); `strToEl`; NC-specific layer/GeoJSON wiring.
- **legends-dayselector.js:** NC exports only `createDaySelector()`; FL/SC also export `addShellCastLegendControl`, `addPartnerSitesLegendControl`.

**FL only**
- **preferences.js:** `getGeoJsonLeases()` – loads FL lease boundaries GeoJSON for preferences page.
- **leases-map.js (entire file):** `getLeasesBoundsGeoJSON`, `getLeases`, `addDropDowns`, `zoomToAuzLease`, `setLeasesFeatureStyle`, `createMap`, `createLegend`, `addLegendControl`, `addEvents`, `init` – FL-specific lease map and AUZ/Individual dropdowns.
- **map.js:** `_addDaySelector` (unused; name only).

**SC only**
- **prefmap.js (entire file):** `setCmuPolyStyleByDay`, `addDaySelectorClickListener`, `addDaySelector`, `prefInitMap` – preferences page map (duplicated day-selector logic from map.js).
- **map_constants.js:** All three have it; content is state-specific (paths, layer names).

### 2.4 Duplicated logic within a state (refactor candidates)

- **SC:** `setCmuPolyStyleByDay`, `addDaySelectorClickListener`, `addDaySelector` exist in both `map/map.js` and `preferences/prefmap.js` with the same behavior but different layer variables. Can be shared by passing the layer (e.g. into a factory or shared module).

---

## 3. Templates (HTML)

### 3.1 Present in all three (same name, state-specific content)

- `base.html`, `index.html`, `map.html`, `about.html`, `how-it-works.html`
- `faqs.html`, `notification-service.html`, `preferences.html`, `signin.html`, `feedback.html`
- `_notification_preferences.html` (partial)

### 3.2 FL and SC only

- `unsubscribed.html` – one-click unsubscribe success/failure (NC has no `/u/<token>` route).

---

## 4. CSS

### 4.1 Same path pattern across states (state-specific file content)

All three have parallel structure under `static/`:

- `common/common.css`
- `common/css/notification_prefs.css`
- `notification-service/notification-service.css`
- `preferences/preferences.css`
- `signin/signin.css`, `map/map.css`, `how-it-works/how-it-works.css`, `about/about.css`
- `lib/ol.css` (OpenLayers)

### 4.2 SC only

- `feedback/feedback.css` – SC has this; NC/FL may use different feedback styling or inline structure.

---

## 5. Consolidation-oriented summary

### 5.1 Good candidates to keep “same” in a single app

- **Routes:** All page routes except `/u/<token>` (add to NC if desired). All API routes can be unified with a state parameter or state-specific handlers.
- **JS:** `common.js`, `notification_prefs.js`, and the bulk of `preferences.js` (profile, leases, auth) are same-concept; map helpers in `utils.js`, `popup.js`, `table.js`, `cluster.js` can be shared with a small adapter layer for NC vs FL/SC.
- **Templates:** Same set of base templates with state passed as context (e.g. `state="NC"|"FL"|"SC"`) for copy, links, and branding.
- **CSS:** Same file layout; state can switch theme or override with state-specific partials.

### 5.2 State-specific pieces to keep behind one “state” switch

- **NC:** Bandwidth callback and log-event API; smoke-test cron; map layer/GeoJSON structure; no one-click unsubscribe unless added.
- **FL:** `leases-map.js`, `getGeoJsonLeases`, FL lease boundaries GeoJSON; one-click unsubscribe.
- **SC:** `prefmap.js` (preferences map); one-click unsubscribe; optional `feedback.css`.

### 5.3 Refactors that help before or during consolidation

1. **SC:** Extract shared day-selector logic from `map.js` and `prefmap.js` (single implementation, pass layer).
2. **NC:** Align `handleSignedInUser()` signature with FL/SC (no parameter) if desired.
3. **Naming:** Keep route names and JS function names consistent (already kebab-case routes; snake_case in Python).
4. **Templates:** Use a single `base.html` with `state` in context and optional state-specific blocks.

This inventory should be updated when adding or removing routes, JS modules, templates, or CSS so that consolidation stays easy to plan and execute.
