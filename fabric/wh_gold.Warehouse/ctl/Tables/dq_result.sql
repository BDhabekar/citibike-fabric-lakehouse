CREATE TABLE [ctl].[dq_result] (
    [run_id]         VARCHAR (64)   NOT NULL,
    [layer]          VARCHAR (10)   NOT NULL,
    [table_name]     VARCHAR (100)  NOT NULL,
    [rule_name]      VARCHAR (100)  NOT NULL,
    [severity]       VARCHAR (10)   NOT NULL,
    [rows_checked]   BIGINT         NULL,
    [rows_failed]    BIGINT         NULL,
    [fail_pct]       DECIMAL (9, 4) NULL,
    [threshold_pct]  DECIMAL (9, 4) NULL,
    [passed]         BIT            NOT NULL,
    [checked_at_utc] DATETIME2 (6)  NOT NULL
);


GO