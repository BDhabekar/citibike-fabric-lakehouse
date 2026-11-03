-- sql/ctl/006_usp_weather_windows.sql
-- Task T021. Target: the warehouse wh_gold. Run 001 to 005 first.
--
-- ctl.usp_weather_windows splits a date range into calendar-month chunks, one row per
-- chunk with start_date and end_date, for the weather pipeline's ForEach. The first
-- chunk starts on @from_date and the last ends on @to_date; the ones between are whole
-- months. Example: 2026-04-01 to 2026-07-15 gives
--   2026-04-01 / 2026-04-30,  2026-05-01 / 2026-05-31,
--   2026-06-01 / 2026-06-30,  2026-07-01 / 2026-07-15.
--
-- Points to say about it:
--   * The numbers 0 to 999 come from a cross join of three 0-to-9 lists, because the
--     Warehouse has no recursive CTEs (T-SQL surface area page). Month n is the first
--     month plus n months; only the months inside the range are kept.
--   * The dates come back as text (YYYY-MM-DD). The pipeline builds URLs from them, and
--     text has one exact spelling. How a date column would look in a Lookup activity's
--     output was not checked.
--   * Dates are returned in order. A reversed range (50041) or one longer than 1,000
--     months (50042) is refused.
--
-- CREATE OR ALTER must be the first statement of its batch, so this file has no
-- wrong-warehouse guard. Run it in a query tab opened from wh_gold.

CREATE OR ALTER PROCEDURE ctl.usp_weather_windows
    @from_date  date,
    @to_date    date
AS
BEGIN
    SET NOCOUNT ON;

    IF @from_date IS NULL OR @to_date IS NULL
        THROW 50040, N'@from_date and @to_date are required.', 1;
    IF @from_date > @to_date
        THROW 50041, N'@from_date is after @to_date.', 1;
    IF DATEDIFF(month, @from_date, @to_date) > 999
        THROW 50042, N'The range is longer than 1,000 months.', 1;

    DECLARE @first_month_start date = DATEFROMPARTS(YEAR(@from_date), MONTH(@from_date), 1);

    WITH digits AS (
        SELECT d FROM (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) AS v(d)
    ),
    numbers AS (
        SELECT ones.d + 10 * tens.d + 100 * hundreds.d AS n
          FROM digits AS ones
         CROSS JOIN digits AS tens
         CROSS JOIN digits AS hundreds
    ),
    months AS (
        SELECT n, DATEADD(month, n, @first_month_start) AS month_start
          FROM numbers
         WHERE n <= DATEDIFF(month, @from_date, @to_date)
    )
    SELECT CONVERT(varchar(10),
               CASE WHEN month_start < @from_date THEN @from_date ELSE month_start END, 23) AS start_date,
           CONVERT(varchar(10),
               CASE WHEN EOMONTH(month_start) > @to_date THEN @to_date ELSE EOMONTH(month_start) END, 23) AS end_date
      FROM months
     ORDER BY n;
END;
