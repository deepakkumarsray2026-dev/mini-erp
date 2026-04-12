-- Mini-ERP PostgreSQL initialization
-- Creates all required schemas and enables extensions

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS hcm;
CREATE SCHEMA IF NOT EXISTS payroll;
CREATE SCHEMA IF NOT EXISTS ap;
CREATE SCHEMA IF NOT EXISTS expenses;
CREATE SCHEMA IF NOT EXISTS procurement;
CREATE SCHEMA IF NOT EXISTS gl;
CREATE SCHEMA IF NOT EXISTS mlops;

-- Grant privileges to the app user
GRANT ALL PRIVILEGES ON SCHEMA auth        TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA hcm         TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA payroll     TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA ap          TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA expenses    TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA procurement TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA gl          TO erp_user;
GRANT ALL PRIVILEGES ON SCHEMA mlops       TO erp_user;

GRANT ALL PRIVILEGES ON DATABASE mini_erp TO erp_user;

-- Default search_path
ALTER USER erp_user SET search_path TO public, auth, hcm, payroll, ap, expenses, procurement, gl, mlops;
