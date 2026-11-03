-- sql/ctl/001_ctl_tables.sql
-- Task T020. Target: the warehouse wh_gold. Builds schema ctl and its four tables
-- exactly as docs/data-contracts.md section 5 lists them.
--
-- Safe to run again. A table that already exists is left alone and never dropped,
-- because ctl.run_log and ctl.watermark hold run history that a re-run must not erase.
-- One batch with no GO lines, so it does not depend on how the query editor treats GO.
--
-- Choices the contract does not spell out (decided in T020):
--   * Primary keys only on source_config and watermark (one row per source_id), NOT ENFORCED.
--     run_log and dq_result are append-only logs and get no key.
--   * NOT NULL on the columns every writer must supply; everything else is nullable.
--   * No DEFAULT constraints: Fabric Warehouse does not support them.

IF DB_NAME() <> N'wh_gold'
    THROW 50001, N'Wrong item. Run this script in the warehouse wh_gold.', 1;

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'ctl')
    EXEC sp_executesql N'CREATE SCHEMA ctl';

-- One row per source. Pipelines read it to know what to fetch and where to land it.
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
               WHERE TABLE_SCHEMA = N'ctl' AND TABLE_NAME = N'source_config')
BEGIN
    CREATE TABLE ctl.source_config
    (
        source_id          varchar(50)  NOT NULL,
        source_kind        varchar(20)  NOT NULL,  -- rest_pipeline | rest_notebook | http_file | stream
        base_url_variable  varchar(100) NULL,      -- name of a variable in vl_citibike
        relative_url       varchar(400) NULL,
        landing_folder     varchar(200) NULL,
        load_pattern       varchar(20)  NOT NULL,  -- incremental | snapshot | monthly | stream
        is_enabled         bit          NOT NULL,
        notes              varchar(400) NULL
    );
    ALTER TABLE ctl.source_config
        ADD CONSTRAINT pk_ctl_source_config PRIMARY KEY NONCLUSTERED (source_id) NOT ENFORCED;
END;

-- One row per source: how far it has been loaded.
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
               WHERE TABLE_SCHEMA = N'ctl' AND TABLE_NAME = N'watermark')
BEGIN
    CREATE TABLE ctl.watermark
    (
        source_id           varchar(50)   NOT NULL,
        watermark_value     varchar(50)   NOT NULL,  -- ISO date or YYYYMM
        updated_at_utc      datetime2(6)  NOT NULL,
        updated_by_run_id   varchar(64)   NULL
    );
    ALTER TABLE ctl.watermark
        ADD CONSTRAINT pk_ctl_watermark PRIMARY KEY NONCLUSTERED (source_id) NOT ENFORCED;
END;

-- One row per pipeline step per run.
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
               WHERE TABLE_SCHEMA = N'ctl' AND TABLE_NAME = N'run_log')
BEGIN
    CREATE TABLE ctl.run_log
    (
        run_id           varchar(64)   NOT NULL,
        parent_run_id    varchar(64)   NULL,
        pipeline_name    varchar(100)  NOT NULL,
        step_name        varchar(100)  NOT NULL,
        environment      varchar(10)   NOT NULL,
        status           varchar(20)   NOT NULL,  -- started | succeeded | failed
        rows_read        bigint        NULL,
        rows_written     bigint        NULL,
        rows_rejected    bigint        NULL,
        started_at_utc   datetime2(6)  NOT NULL,
        ended_at_utc     datetime2(6)  NULL,
        error_message    varchar(4000) NULL,
        details_json     varchar(8000) NULL
    );
END;

-- One row per data-quality rule per run.
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES
               WHERE TABLE_SCHEMA = N'ctl' AND TABLE_NAME = N'dq_result')
BEGIN
    CREATE TABLE ctl.dq_result
    (
        run_id           varchar(64)   NOT NULL,
        layer            varchar(10)   NOT NULL,
        table_name       varchar(100)  NOT NULL,
        rule_name        varchar(100)  NOT NULL,
        severity         varchar(10)   NOT NULL,  -- error | warn
        rows_checked     bigint        NULL,
        rows_failed      bigint        NULL,
        fail_pct         decimal(9,4)  NULL,
        threshold_pct    decimal(9,4)  NULL,
        passed           bit           NOT NULL,
        checked_at_utc   datetime2(6)  NOT NULL
    );
END;
