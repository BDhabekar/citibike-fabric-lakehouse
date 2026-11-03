CREATE   PROCEDURE ctl.usp_seed_config
    @weather_start date
AS
BEGIN
    SET NOCOUNT ON;

    IF @weather_start IS NULL
        THROW 50002, N'@weather_start is required, for example ''2026-04-01''.', 1;

    BEGIN TRY
        BEGIN TRAN;

        IF NOT EXISTS (SELECT 1 FROM ctl.source_config WHERE source_id = 'weather_archive')
            INSERT INTO ctl.source_config
                (source_id, source_kind, base_url_variable, relative_url, landing_folder, load_pattern, is_enabled, notes)
            VALUES
                ('weather_archive', 'rest_pipeline', 'weather_archive_url', NULL,
                 'Files/bronze/weather_archive', 'incremental', 1,
                 'Open-Meteo archive API, hourly values, pulled in month chunks from the watermark minus an overlap. The pipeline builds the query string.');

        IF NOT EXISTS (SELECT 1 FROM ctl.source_config WHERE source_id = 'weather_forecast')
            INSERT INTO ctl.source_config
                (source_id, source_kind, base_url_variable, relative_url, landing_folder, load_pattern, is_enabled, notes)
            VALUES
                ('weather_forecast', 'rest_notebook', 'weather_forecast_url', NULL,
                 'Files/bronze/weather_forecast', 'incremental', 1,
                 'Open-Meteo forecast API, fetched by nb_ingest_weather_forecast with past_days=3 and forecast_days=2. No watermark row: each run lands the whole rolling window.');

        IF NOT EXISTS (SELECT 1 FROM ctl.source_config WHERE source_id = 'gbfs_station_information')
            INSERT INTO ctl.source_config
                (source_id, source_kind, base_url_variable, relative_url, landing_folder, load_pattern, is_enabled, notes)
            VALUES
                ('gbfs_station_information', 'http_file', 'gbfs_base_url', 'station_information.json',
                 'Files/bronze/gbfs_station_information', 'snapshot', 1,
                 'GBFS station_information feed, one snapshot a day. relative_url is read against the gbfs_base_url variable.');

        IF NOT EXISTS (SELECT 1 FROM ctl.source_config WHERE source_id = 'gbfs_system_regions')
            INSERT INTO ctl.source_config
                (source_id, source_kind, base_url_variable, relative_url, landing_folder, load_pattern, is_enabled, notes)
            VALUES
                ('gbfs_system_regions', 'http_file', 'gbfs_base_url', 'system_regions.json',
                 'Files/bronze/gbfs_system_regions', 'snapshot', 1,
                 'GBFS system_regions feed, one snapshot a day. relative_url is read against the gbfs_base_url variable.');

        IF NOT EXISTS (SELECT 1 FROM ctl.source_config WHERE source_id = 'trips')
            INSERT INTO ctl.source_config
                (source_id, source_kind, base_url_variable, relative_url, landing_folder, load_pattern, is_enabled, notes)
            VALUES
                ('trips', 'http_file', 'trips_base_url', 'YYYYMM-citibike-tripdata.zip',
                 'Files/bronze/trips', 'monthly', 1,
                 'Citi Bike monthly trip zip. The pipeline replaces YYYYMM in relative_url. Staged as a zip, then unzipped into the month folder (ADR-027).');

        IF NOT EXISTS (SELECT 1 FROM ctl.watermark WHERE source_id = 'weather_archive')
            INSERT INTO ctl.watermark
                (source_id, watermark_value, updated_at_utc, updated_by_run_id)
            VALUES
                ('weather_archive', CONVERT(varchar(10), @weather_start, 23),
                 CAST(SYSUTCDATETIME() AS datetime2(6)), 'seed');

        COMMIT TRAN;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRAN;
        THROW;
    END CATCH;
END;

GO