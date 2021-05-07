# README.md for the data directory

last updated: 20210121<br/>
contact: Sheila Saia (ssaia at ncsu dot edu)

This README file describes the directory and file structure of the data directory for the ShellCast project. For all other ShellCast documentation go [here](/docs/).

Letters in parentheses next to file names refer to how frequently the directory and file contents are updated. **NOTE:** No letter indicates the directory or file is static (i.e., not updated regularly).

(D) = daily
(Q) = quarterly
(Y) = yearly
(NA) = not applicable

See the README file in each sub-directory for a full description of the containing files.

# data directory structure

  1.0 spatial directory
    1.1 inputs directory
      1.1.1 ncdfm_data directory
        cmu_bounds directory
          files:
            cmu_bounds_10kmbuf_albers.shp (Y)
            cmu_bounds_albers.shp (Y)
            cmu_bounds_wgs84.geojson (Y)
        cmu_bounds_raw directory
          files:
            Conditional_Management_Units.shp (Y)
            cmu_bounds_raw_albers.shp (Y)
            cmu_bounds_raw_valid_albers.shp (Y)
        sga_bounds directory
          files:
            sga_bounds_10kmbuf_albers.shp (Y)
            sga_bounds_albers.shp (Y)
            sga_bounds_class_albers.shp (Y)
            sga_bounds_simple_albers.shp (Y)
        sga_bounds_raw directory
          files:
            sga_bounds_raw_albers.shp (Y)
            sga_bounds_raw_valid_albers.shp (Y)
            SGA_Current_Classifications.shp (Y)

      1.1.2 state_bounds_data directory
        state_bounds directory
          files:
            nc_bounds_10kmbuf_albers.shp (Y)
            nc_bounds_albers.shp (Y)
            state_bounds_albers.shp (Y)
        state_bounds_raw directory
          files:
            State_Boundaries.shp (Y)

    1.2 outputs directory
      1.2.1 ncdmf_data directory
        lease_bounds directory
          files:
            lease_bounds_albers.shp (Q)
        lease_bounds_raw directory
          files:
            lease_bounds_raw.shp (Q)
        lease_centroids directory
          files:
            lease_centroids_albers.shp (Q)
            lease_centroids_mock_albers.shp (NA)

      1.2.2 ndfd_sco_data directory
        files:
          pop12_24hr_nc_albers.tif (D)
          pop12_48hr_nc_albers.tif (D)
          pop12_72hr_nc_albers.tif (D)
          qpf_24hr_nc_albers.tif (D)
          qpf_48hr_nc_albers.tif (D)
          qpf_72hr_nc_albers.tif (D)

  2.0 tabular directory
    2.1 inputs directory
      2.1.1 ncdmf_rainfall_thresholds directory
        files:
          cmu_sga_key.csv (Y)
          rainfall_thresholds_raw_tidy.csv (Y)
          sga_key.csv (Y)

    2.2 outputs directory
      2.2.1 cronjob_data directory
        files:
          shellcast_dailyanalysis_cronjob.err (D)
          shellcast_dailyanalysis_cronjob.out (D)

      2.2.2 ndfd_sco_data directory
        2.2.2.1 cmu_calcs directory
            files:
              ndfd_cmu_calcs.csv (D)
        2.2.2.2 lease_calcs directory
            files:
              ndfd_lease_calcs.csv (D)
        2.2.2.3 ndfd_sco_data_raw directory
            files:
              data_log.csv (D)
              pop12.csv (D)
              qpf.csv (D)
        2.2.2.4 sga_calcs directory
            files:
              none

      2.2.3 ndfd_sco_data_appended directory
        files:
          ndfd_cmu_calcs_appended.csv (D)

      2.2.4 terminal_data directory
        files:
          01_forecast_output_*.txt (D)
          02_convert_df_out_*.txt (D)
          03_analyze_out_*.txt (D)
          04_update_db_out*.txt (D)