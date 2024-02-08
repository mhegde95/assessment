# @author: Meghana Hegde

# SQL queries
CREATE_DATE_TABLE = """
CREATE TABLE IF NOT EXISTS date (
  date date PRIMARY KEY, day INT, day_of_week INT, 
  month INT, year INT, holiday BOOLEAN
);
"""
    
CREATE_WEATHER_TABLE = """                                 
CREATE TABLE IF NOT EXISTS weather (
  "date" DATE, 
  location_id VARCHAR, 
  temperature FLOAT, 
  pressure FLOAT, 
  humidity FLOAT, 
  cloudy BOOLEAN, 
  precipitation BOOLEAN, 
  PRIMARY KEY ("date", location_id), 
  FOREIGN KEY ("date") REFERENCES "date" ("date") ON DELETE CASCADE, 
  FOREIGN KEY (location_id) REFERENCES location (location_id) ON DELETE CASCADE
);
"""
    
CREATE_TRANSACTIONS_TABLE = """  
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id VARCHAR, 
  location_id VARCHAR, 
  "date" DATE, 
  profit float, 
  FOREIGN KEY ("date") REFERENCES "date" ("date") ON DELETE CASCADE, 
  FOREIGN KEY (location_id) REFERENCES location (location_id) ON DELETE CASCADE
);
"""

CREATE_LOCATION_TABLE = """
CREATE TABLE IF NOT EXISTS location (
  location_id VARCHAR PRIMARY KEY, elevation INT, 
  population INT
);
"""

# column headers
READ_QUERY_COLUMNS = ["location_id", "date", "temperature", "profit", "profit_stmt", "dod_profit", "roll_30d_profit"]


# Read Query:

# Transactions table is LEFT JOINed with weather table on columns: date and location_id.
# Sub query has been used to calculate the daily sum of profits aggregated by location, date. 
# Main query uses results from the subquery and calculates additional 2 columns namely rolling_30d_profit and dod_profit. This can also be achived with "SUM(SUM..." instead of explicit subquery, but it is not very debug friendly.
# LAG function is used to calculate the percent change in day-over-day profits (dod_profit) that compares the previous date data and computes the change.
# SQL window function "ROWS BETWEEN .." is used to calculate the rolling sum of for 30 days.

# P.S:
# we could have used cte_joins here that allows queries to scale for additional columns in the report. cte_joins can be used to join weather, location and date table to select the required columns which can be later joined with transactions table. However, i felts its unnecessary here (eg in the end)


READ_QUERY = """
SELECT 
  calculate_profit.location_id, 
  calculate_profit.date, 
  calculate_profit.temp as temperature, 
  calculate_profit.daily_sum_of_profit, 
  calculate_profit.income_statement, 
  ROUND(
    (
      (
        calculate_profit.daily_sum_of_profit - LAG(
          calculate_profit.daily_sum_of_profit
        ) OVER(
          ORDER BY 
            calculate_profit.location_id, 
            calculate_profit.date
        )
      ) / (
        LAG(
          calculate_profit.daily_sum_of_profit
        ) OVER(
          ORDER BY 
            calculate_profit.location_id, 
            calculate_profit.date
        )
      )
    ) * 100, 
    2
  ) As percent_change, 
  SUM(
    calculate_profit.daily_sum_of_profit
  ) OVER (
    PARTITION BY calculate_profit.location_id 
    ORDER BY 
      date ROWS BETWEEN 29 PRECEDING 
      AND CURRENT ROW
  ) As rolling_sum 
FROM 
  (
    SELECT 
      transactions.location_id, 
      transactions.date, 
      IFNULL(
        max(weather.temperature), 
        0
      ) temp, 
      SUM(transactions.profit) as daily_sum_of_profit, 
      CASE WHEN SUM(transactions.profit) > 0 THEN 'positive' WHEN SUM(transactions.profit) < 0 THEN 'negative' END as income_statement 
    FROM 
      transactions 
      LEFT JOIN weather ON transactions.location_id = weather.location_id 
      and transactions.'date' = weather.'date' 
    GROUP BY 
      transactions.location_id, 
      transactions.date
  ) AS calculate_profit 
ORDER BY 
  calculate_profit.location_id, 
  calculate_profit.date 
LIMIT 
  50;
"""

DROP_LOCATION_TABLE = """
DROP table IF EXISTS location;
"""

DROP_TRANSACTIONS_TABLE = """
DROP table IF EXISTS transactions;
"""

DROP_WEATHER_TABLE = """
DROP table IF EXISTS weather;
"""

DROP_DATE_TABLE = """
DROP table IF EXISTS date;
"""

# a query using cte_joins - however not used in this task.

'''
READ_QUERY_CTE = """
WITH cte_joins AS (
  SELECT 
    DISTINCT location.location_id, 
    'date'.'date', 
    'date'.day, 
    weather.temperature, 
    'date'.holiday 
  FROM 
    weather 
    INNER JOIN location ON weather.location_id = location.location_id 
    INNER JOIN 'date' ON 'date'.'date' = weather.'date'
    WHERE holiday = 0
) 
SELECT 
  location_id, 
  date, 
  temp as temperature, 
  daily_sum_of_profit, 
  income_statement, 
  ROUND(
    (
      (
        daily_sum_of_profit - LAG(daily_sum_of_profit) OVER(
          ORDER BY 
            location_id, 
            date
        )
      ) / (
        LAG(daily_sum_of_profit) OVER(
          ORDER BY 
            location_id, 
            date
        )
      )
    ) * 100, 
    2
  ) As percent_change, 
  SUM(daily_sum_of_profit) OVER (
    PARTITION BY location_id 
    ORDER BY 
      date ROWS BETWEEN 29 PRECEDING 
      AND CURRENT ROW
  ) As rolling_sum 
FROM 
  (
    SELECT 
      t.location_id, 
      t.date, 
      IFNULL(max(c.temperature) , 0)temp, 
      SUM(profit) as daily_sum_of_profit, 
      CASE WHEN SUM(profit) > 0 THEN 'positive' WHEN SUM(profit) < 0 THEN 'negative' END as income_statement 
    FROM 
      transactions t 
      LEFT JOIN cte_joins c ON t.location_id = c.location_id 
      and t.'date' = c.'date' 
    GROUP BY 
      t.location_id, 
      t.date
  ) AS V 
ORDER BY 
  v.location_id, 
  v.date
LIMIT
  50;
"""
'''
