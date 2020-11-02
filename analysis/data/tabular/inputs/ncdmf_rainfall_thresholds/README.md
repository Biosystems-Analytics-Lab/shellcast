## README file for ncdmf_rainfall_thresholds directory ##

last updated: 20201101<br/>
contact: Sheila Saia (ssaia at ncsu dot edu)

**rainfall_thresholds_raw_tidy.csv** - This file represents tabular data comes from rainfall_thresholds_raw_20201026.csv which was shared with us by NCDFM staff. It was reformatted to break up the 'RAINFALL THRESHOLD' column into two separate columns: 'rainfall_threshold_in' a numerical column with the rainfall threshold depth in inches and (2) 'rainfall_threshold_class' a character column that describes whether the depth is defined by an everyday event (i.e., 'depth_defined') or emergency conditions (i.e., 'emergency'). Not that most emergency class values are 4 inches except for select ones. See email from NCDMF on 20200604. Also added a unit_id column for ShellCast viewing. In some cases I had to add a "_" between the letters and numbers of the cite name so these values matched the "Conditional_Management_Units.shp" file HA_CLASS values. Last, there were some repeat rows so I deleted those so there was only one mention of each CMU in the file.

**cmu_sga_key.csv** - This file represents tabular data comes from manually inspecting where the CMUs intersect (spatially) with the SGAs. I did this manually because these data do not have similar boundaries and sometimes the overlap is so small that it likely doesn't matter (since the boundaries are likely not too precise in open water). I also added a "google_description" column to point out major landmarks.

**sga_key.csv** - This file represents tabular data was compiled by looking at http://portal.ncdenr.org/web/mf/shellfish-closure-maps and recording the county name (county) and colloquial description (description) of each growing area.
