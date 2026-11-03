-- sql/ctl/005_usp_watermark_set.sql
-- Task T021. Target: the warehouse wh_gold. Run 001 to 004 first.
--
-- ctl.usp_watermark_set moves a source's watermark to a new value and records which run
-- moved it. A pipeline calls it only after a load has succeeded, so a failed load leaves
-- the watermark where it was and the next run starts from the same point.
--
-- Points to say about it:
--   * Update-or-insert in one transaction: the first call for a source inserts its row,
--     later calls update it. ctl.watermark has one row per source (primary key on
--     source_id, NOT ENFORCED), so this procedure is what keeps it to one.
--   * The source has to exist in ctl.source_config (50030). A typo cannot create a
--     watermark for a source nobody loads.
--   * The value is an ISO date (YYYY-MM-DD) or a month (YYYYMM), as the contract says,
--     and has to be a real date or month (50031).
--   * It overwrites. It does not refuse a value older than the current one, because a
--     deliberate reload ("go back to April") is also a call to this procedure. The
--     pipelines pass the new high-water mark only.
--   * The Warehouse rule about conflicting UPDATEs applies here too (see 004); the
--     calling activity retries.
--
-- CREATE OR ALTER must be the first statement of its batch, so this file has no
-- wrong-warehouse guard. Run it in a query tab opened from wh_gold.

CREATE OR ALTER PROCEDURE ctl.usp_watermark_set
    @source_id  varchar(50),
    @value      varchar(50),
    @run_id     varchar(64)
AS
BEGIN
    SET NOCOUNT ON;

    IF @source_id IS NULL
       OR NOT EXISTS (SELECT 1 FROM ctl.source_config WHERE source_id = @source_id)
        THROW 50030, N'@source_id is not in ctl.source_config.', 1;

    IF @value IS NULL
       OR NOT (   (LEN(@value) = 10 AND TRY_CONVERT(date, @value, 23) IS NOT NULL)
               OR (LEN(@value) = 6  AND TRY_CONVERT(date, @value + '01', 112) IS NOT NULL))
        THROW 50031, N'@value must be an ISO date (YYYY-MM-DD) or a month (YYYYMM).', 1;

    IF @run_id IS NULL OR LEN(LTRIM(RTRIM(@run_id))) = 0
        THROW 50032, N'@run_id is required.', 1;

    BEGIN TRY
        BEGIN TRAN;

        UPDATE ctl.watermark
           SET watermark_value   = @value,
               updated_at_utc    = CAST(SYSUTCDATETIME() AS datetime2(6)),
               updated_by_run_id = @run_id
         WHERE source_id = @source_id;

        IF @@ROWCOUNT = 0
            INSERT INTO ctl.watermark
                (source_id, watermark_value, updated_at_utc, updated_by_run_id)
            VALUES
                (@source_id, @value, CAST(SYSUTCDATETIME() AS datetime2(6)), @run_id);

        COMMIT TRAN;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRAN;
        THROW;
    END CATCH;
END;
