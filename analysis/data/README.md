# README.md for data directory

last updated: 20210121<br/>
contact: Sheila Saia (ssaia at ncsu dot edu)

This README file describes the directory and file structure of the data directory for the ShellCast project. For all other ShellCast documentation go [here](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/tree/master/docs).

Letters in parentheses next to file names refer to how frequently the directory and file contents are updated. **NOTE:** No letter indicates the directory or file is static (i.e., not updated regularly).
(D) = daily
(Q) = quarterly
(Y) = yearly

# data directory structure

  1.0 spatial directory
    1.1 inputs directory
      1.1.1 ncdfm_data directory
        cmu_bounds directory
          files:
            cmu_bounds_10kmbuf_albers.shp (Y) -
            cmu_bounds_albers.shp (Y) -
            cmu_bounds_wgs84.geojson (Y) -
            README.md (Y) -
        cmu_bounds_raw directory (move up layer?)
          files:
            Conditional_Management_Units.shp (Y) -
            cmu_bounds_raw_albers.shp (Y) -
            cmu_bounds_raw_valid_albers.shp (Y) -
            README.md (Y) -
        sga_bounds directory
          files:
            
        sga_bounds_raw directory (move up layer?)
          files:

      1.1.2 state_bounds_data directory
        state_bounds directory (move in layer?)
          files:
        state_bounds_raw directory
          files:

    1.2 outputs directory
      1.2.1 ncdmf_data directory
        lease_bounds directory
          files:
        lease_bounds_ignored directory
          files:
        lease_bounds_raw directory
          files:
        lease_centroids directory
          files:

      1.2.2 ndfd_sco_data directory
        files:

  2.0 tabular directory
    2.1 inputs directory
      2.1.1 ncdmf_rainfall_thresholds directory
        files:

    2.2 outputs directory
      2.2.1 cronjob_data directory
        files:

      2.2.2 ndfd_sco_data directory
        cmu_calcs directory
          files:
        lease_calcs directory
          files:
        ndfd_sco_data_raw directory
          files:
        sga_calcs directory
          files:

      2.2.3 ndfd_sco_data_appended directory
        files:


      2.2.4 terminal_data directory
        files:
