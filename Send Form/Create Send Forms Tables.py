# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Create patients table
# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.default.send_forms_patients AS
# MAGIC WITH patient_data AS (
# MAGIC   SELECT
# MAGIC     ROW_NUMBER() OVER (ORDER BY RAND()) as patient_id,
# MAGIC     names.first_name || ', ' || names.last_name as patient_name,
# MAGIC     'ju'
# MAGIC       || LPAD(CAST(CAST(RAND() * 999999 AS INT) AS STRING), 6, '0')
# MAGIC       || SUBSTR('abcdefghijklmnopqrstuvwxyz', CAST(RAND() * 26 AS INT) + 1, 2) as mrn,
# MAGIC     DATE_ADD('1940-01-01', CAST(RAND() * 25000 AS INT)) as date_of_birth,
# MAGIC     providers.provider_name,
# MAGIC     locations.location_name,
# MAGIC     CASE
# MAGIC       WHEN RAND() > 0.7 THEN NULL
# MAGIC       ELSE DATE_ADD(CURRENT_DATE(), CAST(RAND() * 60 - 30 AS INT))
# MAGIC     END as next_appointment,
# MAGIC     appt_types.appointment_type
# MAGIC   FROM
# MAGIC     (
# MAGIC       SELECT
# MAGIC         explode(
# MAGIC           array(
# MAGIC             'Case', 'Forth', 'Miller', 'Palmer', 'Dwyer', 'Anderson', 'Brown', 'Davis', 'Garcia', 'Rodriguez',
# MAGIC             'Wilson', 'Martinez', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Harris', 'Clark',
# MAGIC             'Lewis', 'Walker', 'Hall', 'Allen', 'Young', 'King', 'Wright', 'Scott', 'Green', 'Baker'
# MAGIC           )
# MAGIC         ) as last_name,
# MAGIC         explode(
# MAGIC           array(
# MAGIC             'Justin', 'Sally', 'Sam', 'Eric', 'Barb', 'John', 'Mary', 'James', 'Patricia', 'Michael',
# MAGIC             'Jennifer', 'William', 'Linda', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas'
# MAGIC           )
# MAGIC         ) as first_name
# MAGIC     ) names
# MAGIC       CROSS JOIN (
# MAGIC         SELECT
# MAGIC           explode(array('Seth Fillmore, MD', 'Doctor Pink, MD', 'Dr. Johnson, MD', 'Dr. Smith, MD', 'Dr. Williams, MD')) as provider_name
# MAGIC       ) providers
# MAGIC       CROSS JOIN (
# MAGIC         SELECT
# MAGIC           explode(array('Fremont', 'San Francisco Medical Oncology', 'Downtown Clinic', 'Northside Hospital', 'Westside Center')) as location_name
# MAGIC       ) locations
# MAGIC       CROSS JOIN (
# MAGIC         SELECT
# MAGIC           explode(array('Alpha Shawn Test', 'Follow-up', 'Initial Consultation', 'Annual Physical', 'Specialist Visit')) as appointment_type
# MAGIC       ) appt_types
# MAGIC   LIMIT 100
# MAGIC )
# MAGIC SELECT
# MAGIC   patient_name,
# MAGIC   mrn,
# MAGIC   date_of_birth,
# MAGIC   CAST(DATEDIFF(CURRENT_DATE(), date_of_birth) / 365.25 AS INT) as age,
# MAGIC   provider_name,
# MAGIC   location_name,
# MAGIC   next_appointment,
# MAGIC   appointment_type
# MAGIC FROM patient_data
# MAGIC ORDER BY patient_name;

# COMMAND ----------

# DBTITLE 1,Create forms table
# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.default.send_forms_forms AS
# MAGIC WITH form_data AS (
# MAGIC   SELECT
# MAGIC     forms.form_name as packet_form_name,
# MAGIC     specialties.specialty,
# MAGIC     providers.provider_name,
# MAGIC     locations.location_name,
# MAGIC     appt_types.appointment_type,
# MAGIC     forms.last_update,
# MAGIC     forms.version
# MAGIC   FROM
# MAGIC     (
# MAGIC       SELECT 'Acknowledgement of Notice of Privacy Practices' as form_name, '2024-09-19' as last_update, 1 as version
# MAGIC       UNION ALL
# MAGIC       SELECT 'AO - Assignment of Benefits', '2025-03-18', 1
# MAGIC       UNION ALL
# MAGIC       SELECT 'AO - Financial Policy', '2025-03-18', 1
# MAGIC       UNION ALL
# MAGIC       SELECT 'AO - HIPAA Consent to Share Information', '2025-03-18', 1
# MAGIC       UNION ALL
# MAGIC       SELECT 'AOB Patient Info and Insurance', '2024-11-22', 1
# MAGIC     ) forms
# MAGIC       CROSS JOIN (
# MAGIC         SELECT explode(array('General Practice', 'Oncology', 'Cardiology', 'Pediatrics', 'All')) as specialty
# MAGIC       ) specialties
# MAGIC       CROSS JOIN (
# MAGIC         SELECT explode(array('Seth Fillmore, MD', 'Doctor Pink, MD', 'Dr. Johnson, MD', 'All')) as provider_name
# MAGIC       ) providers
# MAGIC       CROSS JOIN (
# MAGIC         SELECT explode(array('Fremont', 'San Francisco Medical Oncology', 'Downtown Clinic', 'All')) as location_name
# MAGIC       ) locations
# MAGIC       CROSS JOIN (
# MAGIC         SELECT explode(array('Alpha Shawn Test', 'Follow-up', 'Initial Consultation', 'All')) as appointment_type
# MAGIC       ) appt_types
# MAGIC )
# MAGIC SELECT DISTINCT
# MAGIC   packet_form_name,
# MAGIC   specialty,
# MAGIC   provider_name,
# MAGIC   location_name,
# MAGIC   appointment_type,
# MAGIC   last_update,
# MAGIC   version
# MAGIC FROM form_data
# MAGIC ORDER BY packet_form_name;