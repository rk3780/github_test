# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS kpi_metrics (
# MAGIC   metric_name STRING,
# MAGIC   current_value DECIMAL(10,2),
# MAGIC   prior_value DECIMAL(10,2),
# MAGIC   change_pct DECIMAL(5,4),
# MAGIC   site STRING,
# MAGIC   payer STRING,
# MAGIC   metric_date DATE
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS regimen_margins (
# MAGIC   regimen STRING,
# MAGIC   margin DECIMAL(5,2),
# MAGIC   site STRING,
# MAGIC   payer STRING,
# MAGIC   margin_date DATE
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS payer_mix (
# MAGIC   payer_type STRING,
# MAGIC   percentage INT,
# MAGIC   site STRING,
# MAGIC   mix_date DATE
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS site_list (
# MAGIC   site_name STRING
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS payer_list (
# MAGIC   payer_name STRING
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO kpi_metrics VALUES
# MAGIC -- Main Campus + Commercial
# MAGIC ('Active Patients', 15200, 14800, 0.027, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 2100, 2000, 0.05, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 2.8, 3.1, -0.097, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 5.2, 5.5, -0.055, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- Main Campus + Medicare
# MAGIC ('Active Patients', 8900, 8500, 0.047, 'Main Campus', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 1650, 1600, 0.031, 'Main Campus', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 3.2, 3.4, -0.059, 'Main Campus', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 7.1, 6.9, 0.029, 'Main Campus', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- North Clinic + Commercial
# MAGIC ('Active Patients', 6800, 6200, 0.097, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 1950, 1850, 0.054, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 3.5, 3.8, -0.079, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 6.5, 6.3, 0.032, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- North Clinic + Medicare
# MAGIC ('Active Patients', 5400, 5100, 0.059, 'North Clinic', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 1580, 1520, 0.039, 'North Clinic', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 3.8, 4.1, -0.073, 'North Clinic', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 8.2, 8.0, 0.025, 'North Clinic', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- South Clinic + Commercial
# MAGIC ('Active Patients', 4200, 3900, 0.077, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 1820, 1750, 0.04, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 3.3, 3.5, -0.057, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 6.8, 6.5, 0.046, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- South Clinic + Medicaid
# MAGIC ('Active Patients', 3100, 2900, 0.069, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 1420, 1380, 0.029, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 4.1, 4.3, -0.047, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 9.5, 9.2, 0.033, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- East Medical Center + Commercial
# MAGIC ('Active Patients', 7600, 7200, 0.056, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 2050, 1980, 0.035, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 2.9, 3.2, -0.094, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 5.8, 5.6, 0.036, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- East Medical Center + Other
# MAGIC ('Active Patients', 2800, 2600, 0.077, 'East Medical Center', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Avg Revenue per Visit', 1680, 1620, 0.037, 'East Medical Center', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Report Run Time', 3.6, 3.9, -0.077, 'East Medical Center', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Denial Rate', 7.8, 7.5, 0.04, 'East Medical Center', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS);

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO regimen_margins VALUES
# MAGIC -- Main Campus
# MAGIC ('Regimen A', 32.5, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen B', 38.2, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen C', 42.1, 'Main Campus', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen D', 48.5, 'Main Campus', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen E', 45.3, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen F', 51.8, 'Main Campus', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen G', 58.2, 'Main Campus', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- North Clinic
# MAGIC ('Regimen A', 28.5, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen B', 32.1, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen C', 35.8, 'North Clinic', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen D', 41.2, 'North Clinic', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen E', 38.9, 'North Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen F', 45.3, 'North Clinic', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen G', 52.7, 'North Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- South Clinic
# MAGIC ('Regimen A', 25.8, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen B', 29.5, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen C', 31.2, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen D', 36.8, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen E', 34.1, 'South Clinic', 'Medicaid', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen F', 40.2, 'South Clinic', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen G', 47.9, 'South Clinic', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- East Medical Center
# MAGIC ('Regimen A', 30.2, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen B', 35.8, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen C', 39.5, 'East Medical Center', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen D', 44.8, 'East Medical Center', 'Medicare', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen E', 42.1, 'East Medical Center', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen F', 48.5, 'East Medical Center', 'Other', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Regimen G', 55.3, 'East Medical Center', 'Commercial', CURRENT_DATE() - INTERVAL 45 DAYS);

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO payer_mix VALUES
# MAGIC -- Main Campus
# MAGIC ('Commercial', 62, 'Main Campus', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Medicare', 28, 'Main Campus', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Other', 10, 'Main Campus', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- North Clinic
# MAGIC ('Commercial', 58, 'North Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Medicare', 31, 'North Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Other', 11, 'North Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- South Clinic
# MAGIC ('Commercial', 45, 'South Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Medicare', 25, 'South Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Medicaid', 22, 'South Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Other', 8, 'South Clinic', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC -- East Medical Center
# MAGIC ('Commercial', 65, 'East Medical Center', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Medicare', 23, 'East Medical Center', CURRENT_DATE() - INTERVAL 45 DAYS),
# MAGIC ('Other', 12, 'East Medical Center', CURRENT_DATE() - INTERVAL 45 DAYS);

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO site_list VALUES
# MAGIC ('All Sites'),
# MAGIC ('Main Campus'),
# MAGIC ('North Clinic'),
# MAGIC ('South Clinic'),
# MAGIC ('East Medical Center'),
# MAGIC ('West Facility');

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO payer_list VALUES
# MAGIC ('All Payers'),
# MAGIC ('Commercial'),
# MAGIC ('Medicare'),
# MAGIC ('Medicaid'),
# MAGIC ('Other');

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE EXTENDED kpi_metrics;