CREATE TABLE [ctl].[run_log] (
    [run_id]         VARCHAR (64)   NOT NULL,
    [parent_run_id]  VARCHAR (64)   NULL,
    [pipeline_name]  VARCHAR (100)  NOT NULL,
    [step_name]      VARCHAR (100)  NOT NULL,
    [environment]    VARCHAR (10)   NOT NULL,
    [status]         VARCHAR (20)   NOT NULL,
    [rows_read]      BIGINT         NULL,
    [rows_written]   BIGINT         NULL,
    [rows_rejected]  BIGINT         NULL,
    [started_at_utc] DATETIME2 (6)  NOT NULL,
    [ended_at_utc]   DATETIME2 (6)  NULL,
    [error_message]  VARCHAR (4000) NULL,
    [details_json]   VARCHAR (8000) NULL
);


GO