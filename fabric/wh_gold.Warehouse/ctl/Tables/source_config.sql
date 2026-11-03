CREATE TABLE [ctl].[source_config] (
    [source_id]         VARCHAR (50)  NOT NULL,
    [source_kind]       VARCHAR (20)  NOT NULL,
    [base_url_variable] VARCHAR (100) NULL,
    [relative_url]      VARCHAR (400) NULL,
    [landing_folder]    VARCHAR (200) NULL,
    [load_pattern]      VARCHAR (20)  NOT NULL,
    [is_enabled]        BIT           NOT NULL,
    [notes]             VARCHAR (400) NULL
);


GO

ALTER TABLE [ctl].[source_config]
    ADD CONSTRAINT [pk_ctl_source_config] PRIMARY KEY NONCLUSTERED ([source_id] ASC) NOT ENFORCED;


GO