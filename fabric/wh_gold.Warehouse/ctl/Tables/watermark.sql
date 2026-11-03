CREATE TABLE [ctl].[watermark] (
    [source_id]         VARCHAR (50)  NOT NULL,
    [watermark_value]   VARCHAR (50)  NOT NULL,
    [updated_at_utc]    DATETIME2 (6) NOT NULL,
    [updated_by_run_id] VARCHAR (64)  NULL
);


GO

ALTER TABLE [ctl].[watermark]
    ADD CONSTRAINT [pk_ctl_watermark] PRIMARY KEY NONCLUSTERED ([source_id] ASC) NOT ENFORCED;


GO