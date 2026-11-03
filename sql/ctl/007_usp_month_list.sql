-- sql/ctl/007_usp_month_list.sql
-- Task T021. Target: the warehouse wh_gold. Run 001 to 006 first.
--
-- ctl.usp_month_list returns one row per month from @first_month to @last_month, both
-- included, as YYYYMM text in a column called trip_month (the name fact.trip uses).
-- pl_backfill loops over it, one child run per month. Example: '202607' to '202609'
-- gives 202607, 202608, 202609.
--
-- Points to say about it:
--   * Same numbers list as ctl.usp_weather_windows: no recursive CTE in the Warehouse.
--   * Each argument has to be six digits that make a real month; the parameters are
--     wider than six characters on purpose, so a seven-character typo is refused
--     (50050) instead of being cut to six by the parameter and accepted.
--   * A first month after the last (50051) or a range over 1,000 months (50052) is refused.
--
-- CREATE OR ALTER must be the first statement of its batch, so this file has no
-- wrong-warehouse guard. Run it in a query tab opened from wh_gold.

CREATE OR ALTER PROCEDURE ctl.usp_month_list
    @first_month  varchar(10),
    @last_month   varchar(10)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @first_date date =
        CASE WHEN LEN(@first_month) = 6 THEN TRY_CONVERT(date, @first_month + '01', 112) END;
    DECLARE @last_date date =
        CASE WHEN LEN(@last_month) = 6 THEN TRY_CONVERT(date, @last_month + '01', 112) END;

    IF @first_date IS NULL OR @last_date IS NULL
        THROW 50050, N'@first_month and @last_month must each be a month written YYYYMM.', 1;
    IF @first_date > @last_date
        THROW 50051, N'@first_month is after @last_month.', 1;
    IF DATEDIFF(month, @first_date, @last_date) > 999
        THROW 50052, N'The range is longer than 1,000 months.', 1;

    WITH digits AS (
        SELECT d FROM (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) AS v(d)
    ),
    numbers AS (
        SELECT ones.d + 10 * tens.d + 100 * hundreds.d AS n
          FROM digits AS ones
         CROSS JOIN digits AS tens
         CROSS JOIN digits AS hundreds
    )
    SELECT LEFT(CONVERT(char(8), DATEADD(month, n, @first_date), 112), 6) AS trip_month
      FROM numbers
     WHERE n <= DATEDIFF(month, @first_date, @last_date)
     ORDER BY n;
END;
