This document is intended to explain how to perform simple, manual updates to ShellCast.

## Setup
1. Download the Git repository to your machine.

## Uploading changes to GitHub
1. From the root of the repository, run `git pull` to make sure you have the most recent version of the repository.
2. Run `git add .` to stage all of the changes made in all files.
3. Run `git commit` which will open a text editor where you can write a commit message (describe what changes you've made).
4. Run `git push` to push the changes to GitHub.

## Uploading changes to Google App Engine
1. From the root of the repository, run `gcloud app deploy`.

## Updating web pages
Nearly all of the HTML used for the content of the web pages is contained in the templates/ directory as Jinja templates.  However, HTML that needed to be generated dynamically is not present in these files and is instead embedded in JavaScript files.  If you want to edit any of the following dynamic elements, look in the listed JS file to find the HTML otherwise look at the template for the page you want to edit.

Dynamic HTML element file locations
- The map legend, day selector, and lease and grow area info popups can be found in static/index/index.js.
- 

After you have found and made an edit:
1. [Upload the changes to GitHub](#uploading-changes-to-github).
2. [Upload the changes to Google App Engine](#uploading-changes-to-google-app-engine).

## Updating growing area boundaries
growing_area_bounds.geojson contains the NCDMF growing areas and their boundaries.  To modify the growing areas' boundaries, simply replace that file with an updated version while keeping the file name the same.

1. [Upload the changes to GitHub](#uploading-changes-to-github).
2. [Upload the changes to Google App Engine](#uploading-changes-to-google-app-engine).

## Turning off/on notifications
