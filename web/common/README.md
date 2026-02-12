# Shared notification preferences (canonical source)

This folder is **not** deployed to GAE. It is the single source for the notification preferences form used by NC, FL, and SC.

**Deployed copies** live inside each app:

- **CSS/JS:** `shellcast-web-nc/static/common/css/` and `static/common/js/` (and same under `shellcast-web-fl/`, `shellcast-web-sc/`)
- **Template:** `shellcast-web-*/templates/_notification_preferences.html`

When you change the form or its behavior:

1. Edit the files here (`css/notification_prefs.css`, `js/notification_prefs.js`, `templates/_notification_preferences.html`).
2. Copy the updated files into each app:

   ```bash
   # From repo root
   for app in shellcast-web-nc shellcast-web-fl shellcast-web-sc; do
     cp web/common/css/notification_prefs.css web/$app/static/common/css/
     cp web/common/js/notification_prefs.js web/$app/static/common/js/
     cp web/common/templates/_notification_preferences.html web/$app/templates/
   done
   ```

Then deploy each app as usual.
