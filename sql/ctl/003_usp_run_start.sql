-- sql/ctl/003_usp_run_start.sql
-- Task T021. Target: the warehouse wh_gold. Run 001 and 002 first.
--
-- ctl.usp_run_start opens one row in ctl.run_log for one pipeline step, with status
-- 'started'. Every pipeline calls it as its first step and every notebook step calls
-- it before the notebook runs; ctl.usp_run_end closes the row.
--
-- Points to say about it:
--   * One row per step per run. The row is found again by run_id + step_name.
--   * parent_run_id links a child pipeline's row to the pipeline that started it.
--     An empty string is stored as NULL, so "no parent" has one spelling.
--   * environment must be dev, test or prod (the values of env_name in vl_citibike),
--     so a typo is refused instead of making a fourth environment in the log.
--   * Nothing is typed here that belongs to an environment; the pipeline passes it all.
--   * Errors 50010 to 50013 are mine, so a message says which check refused the call.
--
-- CREATE OR ALTER must be the first statement of its batch, so this file has no
-- wrong-warehouse guard. Run it in a query tab opened from wh_gold.

CREATE OR ALTER PROCEDURE ctl.usp_run_start
    @run_id         varchar(64),
    @parent_run_id  varchar(64) = NULL,
    @pipeline_name  varchar(100),
    @step_name      varchar(100),
    @environment    varchar(10)
AS
BEGIN
    SET NOCOUNT ON;

    IF @run_id IS NULL OR LEN(LTRIM(RTRIM(@run_id))) = 0
        THROW 50010, N'@run_id is required.', 1;
    IF @pipeline_name IS NULL OR LEN(LTRIM(RTRIM(@pipeline_name))) = 0
        THROW 50011, N'@pipeline_name is required.', 1;
    IF @step_name IS NULL OR LEN(LTRIM(RTRIM(@step_name))) = 0
        THROW 50012, N'@step_name is required.', 1;
    IF @environment IS NULL OR @environment NOT IN ('dev', 'test', 'prod')
        THROW 50013, N'@environment must be dev, test or prod.', 1;

    INSERT INTO ctl.run_log
        (run_id, parent_run_id, pipeline_name, step_name, environment, status, started_at_utc)
    VALUES
        (@run_id, NULLIF(LTRIM(RTRIM(@parent_run_id)), ''), @pipeline_name, @step_name,
         @environment, 'started', CAST(SYSUTCDATETIME() AS datetime2(6)));
END;
