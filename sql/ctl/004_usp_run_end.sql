-- sql/ctl/004_usp_run_end.sql
-- Task T021. Target: the warehouse wh_gold. Run 001 to 003 first.
--
-- ctl.usp_run_end closes the row that ctl.usp_run_start opened for the same run_id and
-- step_name: it sets the final status, the end time, the error text, the raw JSON and
-- the three counts. The counts are read from the notebook exit contract in
-- docs/conventions.md section 6 ($.rows_read, $.rows_written, $.rows_rejected).
--
-- Points to say about it:
--   * It finds the newest row for that run_id and step_name that is still 'started'.
--     A manual run that reuses run_id 'manual' therefore closes only its own row, and a
--     step that crashed earlier cannot be closed by a later call by accident.
--   * No open row to close is an error (50023), not a silent no-op, so a missing
--     usp_run_start shows up in the pipeline instead of as a gap in the log.
--   * A succeeded step with details that are not valid JSON is refused (50021). A failed
--     step never is: this runs on the failure path, which must not fail over formatting,
--     so the text is moved into error_message and details_json stays empty.
--   * The counts come out as NULL when the JSON lacks them or holds a non-number.
--   * The notebook payload has to fit in 8,000 characters (the column size); a longer
--     one is cut by the parameter and then refused as invalid JSON. T022 keeps it short.
--   * A Warehouse UPDATE conflicts with any other UPDATE or DELETE running on the same
--     table at that moment, even on other rows (Microsoft Learn, Transactions in Fabric
--     Data Warehouse). Two pipelines closing steps in the same second can therefore
--     get error 24556 on one of them. The pipeline activity that calls this procedure
--     retries; the procedure does not retry inside itself.
--
-- CREATE OR ALTER must be the first statement of its batch, so this file has no
-- wrong-warehouse guard. Run it in a query tab opened from wh_gold.

CREATE OR ALTER PROCEDURE ctl.usp_run_end
    @run_id         varchar(64),
    @step_name      varchar(100),
    @status         varchar(20),
    @details_json   varchar(8000) = NULL,
    @error_message  varchar(4000) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @run_id IS NULL OR LEN(LTRIM(RTRIM(@run_id))) = 0
        THROW 50020, N'@run_id is required.', 1;
    IF @step_name IS NULL OR LEN(LTRIM(RTRIM(@step_name))) = 0
        THROW 50020, N'@step_name is required.', 1;
    IF @status IS NULL OR @status NOT IN ('succeeded', 'failed')
        THROW 50022, N'@status must be succeeded or failed.', 1;

    SET @details_json  = NULLIF(LTRIM(RTRIM(@details_json)), '');
    SET @error_message = NULLIF(LTRIM(RTRIM(@error_message)), '');

    IF @details_json IS NOT NULL AND ISJSON(@details_json) = 0
    BEGIN
        IF @status = 'succeeded'
            THROW 50021, N'@details_json is not valid JSON.', 1;

        SET @error_message = LEFT(
            CONCAT(COALESCE(@error_message, ''), ' | details: ', @details_json), 4000);
        SET @details_json = NULL;
    END;

    DECLARE @rows_read     bigint = TRY_CAST(JSON_VALUE(@details_json, '$.rows_read')     AS bigint);
    DECLARE @rows_written  bigint = TRY_CAST(JSON_VALUE(@details_json, '$.rows_written')  AS bigint);
    DECLARE @rows_rejected bigint = TRY_CAST(JSON_VALUE(@details_json, '$.rows_rejected') AS bigint);

    DECLARE @open_started_at datetime2(6) =
        (SELECT MAX(started_at_utc)
           FROM ctl.run_log
          WHERE run_id = @run_id AND step_name = @step_name AND status = 'started');

    IF @open_started_at IS NULL
        THROW 50023, N'No open started row for this run_id and step_name.', 1;

    UPDATE ctl.run_log
       SET status         = @status,
           rows_read      = @rows_read,
           rows_written   = @rows_written,
           rows_rejected  = @rows_rejected,
           ended_at_utc   = CAST(SYSUTCDATETIME() AS datetime2(6)),
           error_message  = @error_message,
           details_json   = @details_json
     WHERE run_id = @run_id
       AND step_name = @step_name
       AND status = 'started'
       AND started_at_utc = @open_started_at;
END;
