# File Processing Workflow Documentation

## Overview

This document outlines the file processing workflow for meter data ingestion in the utility retail platform. The system handles various file formats from different providers (Bluecurrent, SmartCo, IntelliHub, Influx) and processes them through a standardized pipeline.

## File Types and Formats

### Bluecurrent Mass Market
- **Daily Register Reads**
  - File Pattern: `RMNGCSXXXX{date}{time}IC.C24.csv.zip`
  - Format: CSV with ICP, Read Date, Meter Number, Register Channel, Midnight Read, Read Type
  - Processing: Daily at 00:30 NZST

- **Half Hourly Reads**
  - File Pattern: `AMS_E_XXXX_HERM_{targetdate}_{rundate}_{seq}.zip`
  - Format: CSV with ICP, AMS Number, Element, Register data
  - Processing: Every 30 minutes

### Bluecurrent C&I
- **Daily/Monthly Reads**
  - File Pattern: `TRUS_E_UNET_ICPHH_{reportmonth}_{rundate}_{uniqueid}.TXT`
  - Format: Fixed-width with header and detail records
  - Processing: Daily at 01:00 NZST

### SmartCo
- **Daily Register Reads**
  - File Pattern: `RMSMCOXXXX{date}{time}IC.C24.csv.zip`
  - Format: Similar to Bluecurrent Mass Market
  - Processing: Daily at 00:30 NZST

- **Half Hourly Reads**
  - File Pattern: `SMCO_E_XXXX_HERM_{targetdate}_{rundate}_{seq}.zip`
  - Format: Similar to Bluecurrent Mass Market
  - Processing: Every 30 minutes

### IntelliHub & Influx
- Similar patterns to above, with provider-specific prefixes

## Processing Pipeline

### 1. File Ingestion (Airflow DAG: `meter_data_ingestion`)
- **Task**: `check_sftp_sources`
  - Checks SFTP servers for new files
  - Validates file patterns and timestamps
  - Creates ImportLog entries

- **Task**: `download_files`
  - Downloads files to staging area
  - Calculates checksums
  - Updates ImportLog status

### 2. File Validation (Airflow DAG: `meter_data_validation`)
- **Task**: `validate_file_format`
  - Checks file structure against expected format
  - Validates headers and data types
  - Records validation errors

- **Task**: `validate_business_rules`
  - Applies business rules (e.g., date ranges, value ranges)
  - Checks for duplicates
  - Records business rule violations

### 3. Data Processing (Airflow DAG: `meter_data_processing`)
- **Task**: `extract_data`
  - Extracts data from files
  - Applies field mappings
  - Transforms data to standard format

- **Task**: `load_data`
  - Loads data into appropriate tables
  - Handles updates and inserts
  - Records processing statistics

### 4. Post-Processing (Airflow DAG: `meter_data_post_processing`)
- **Task**: `archive_files`
  - Moves processed files to archive
  - Updates ImportLog with archive location
  - Cleans up staging area

- **Task**: `send_notifications`
  - Sends success/failure notifications
  - Updates monitoring dashboards
  - Triggers downstream processes

## Directory Structure

```
/data/
├── imports/
│   ├── metering/
│   │   ├── bluecurrent-mm/
│   │   │   ├── dailyregisterreads/
│   │   │   │   ├── imported/
│   │   │   │   ├── error/
│   │   │   │   └── completed/
│   │   │   └── halfhourlyreads/
│   │   │       ├── imported/
│   │   │       ├── error/
│   │   │       └── completed/
│   │   ├── bluecurrent-ci/
│   │   ├── smartco/
│   │   ├── intellihub/
│   │   └── influx/
│   └── archive/
│       └── metering/
│           └── {year}/
│               └── {month}/
└── exports/
    └── metering/
        └── {provider}/
            └── {type}/
```

## Error Handling

1. **File Level Errors**
   - Invalid file format
   - Missing required fields
   - Corrupted files
   - Duplicate files

2. **Data Level Errors**
   - Invalid data types
   - Out of range values
   - Missing required values
   - Business rule violations

3. **Processing Errors**
   - Database connection issues
   - Transformation failures
   - Load failures

## Monitoring and Alerts

1. **Airflow Monitoring**
   - DAG run status
   - Task execution times
   - Error rates
   - Retry counts

2. **File Processing Monitoring**
   - Files processed per hour
   - Success/failure rates
   - Processing times
   - Error types and frequencies

3. **Data Quality Monitoring**
   - Record counts
   - Validation error rates
   - Data completeness
   - Processing latency

## Recovery Procedures

1. **Failed File Recovery**
   - Retry failed files
   - Manual intervention process
   - Error resolution workflow

2. **Data Recovery**
   - Point-in-time recovery
   - Data reconciliation
   - Audit trail verification

## Security Considerations

1. **File Security**
   - SFTP encryption
   - File access controls
   - Archive security

2. **Data Security**
   - Data encryption at rest
   - Access controls
   - Audit logging

## Maintenance Procedures

1. **Regular Maintenance**
   - Archive cleanup
   - Log rotation
   - Performance optimization

2. **Emergency Procedures**
   - System recovery
   - Data restoration
   - Service restoration 