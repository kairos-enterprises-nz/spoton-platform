# NZX GR Reports Import DAG

## Overview

The NZX GR Reports Import DAG (`gr_reports_nzx.py`) downloads and imports all GR (Generation Reconciliation) report files from the NZX SFTP server. It follows the same raw import philosophy as the switching files DAG.

## Supported GR Report Types

### GR-170 - Purchaser's Submission Accuracy
- **Files**: `NZRM_E_ABCD_ACCYNHH_YYYYMM_YYYYMMDD_HHMISS.abc.gz` (NHH)
- **Files**: `NZRM_E_ABCD_ACCYHHR_YYYYMM_YYYYMMDD_HHMISS.abc.gz` (HHR)
- **Fields**: Consumption Period, Revision Cycle, Balancing Area, POC, Network ID, Participant Code, Metering Type, Volumes, Percentages
- **Table**: `nzx_gr.gr_170_submission_accuracy`

### GR-130 - Report Electricity Supplied or Submitted Comparison
- **Files**: `NZRM_E_ABCD_ESUPSUB_YYYYMM_YYYYMMDD_HHMISS.abc.gz`
- **Fields**: Consumption Period, Revision Cycle, NSP, Grid NSP, Balancing Area, Participant, Consumption/Sales Data
- **Table**: `nzx_gr.gr_130_supply_submission`

### GR-100 - ICP Days Comparison
- **Files**: `NZRM_E_ABCD_ICPCOMP_YYYYMM_YYYYMMDD_HHMISS.abc.gz`
- **Fields**: Consumption Period, Revision Cycle, Balancing Area, POC, Network ID, Participant Code, Metering Type, ICP Days Data
- **Table**: `nzx_gr.gr_100_icp_days`

### GR-150 - ICP Days Comparison Summary
- **Files**: `NZRM_E_ABCD_ICPCSUM_YYYYMM_YYYYMMDD_HHMISS.abc.gz`
- **Fields**: Consumption Period, Revision Cycle, Participant Code, Metering Type, Difference
- **Table**: `nzx_gr.gr_150_icp_days_summary`

### GR-090 - Missing HHR ICPs
- **Files**: `NZRM_E_ABCD_ICPMISS_YYYYMM_YYYYMMDD_HHMISS.abc.gz`
- **Fields**: Consumption Period, Revision Cycle, Balancing Area, POC, Network ID, Participant Code, Discrepancy Type, ICP Number
- **Table**: `nzx_gr.gr_090_missing_icps`

### GR-140 - Missing HHR ICPs Summary
- **Files**: `NZRM_E_ABCD_ICPMSUM_YYYYMM_YYYYMMDD_HHMISS.abc.gz`
- **Fields**: Consumption Period, Revision Cycle, Participant Code, Number of Discrepancies
- **Table**: `nzx_gr.gr_140_missing_icps_summary`

## DAG Workflow

The DAG follows a 6-step linear workflow:

1. **Test NZX Connection** (`1_test_nzx_connection`)
   - Tests SFTP connection to NZX server
   - Validates credentials and connectivity

2. **Discover GR Files** (`2_discover_gr_files`)
   - Scans `/nzx/` directory for `.gz` files
   - Classifies files by GR report type
   - Filters for supported GR report patterns

3. **Download GR Files** (`3_download_gr_files`)
   - Downloads all discovered GR report files
   - Organizes by report type: `{GR_TYPE}/imported/`
   - Implements duplicate detection using file hashes

4. **Extract and Import** (`4_extract_and_import_gr_files`)
   - Extracts `.gz` files to temporary locations
   - Parses CSV content according to GR specifications
   - Imports raw data into appropriate database tables
   - Comprehensive error handling and logging

5. **Verify Import** (`5_verify_gr_import`)
   - Validates record counts across all tables
   - Generates import statistics and summaries
   - Checks data quality and completeness

6. **Cleanup Files** (`6_cleanup_gr_files`)
   - Archives successfully processed files
   - Moves failed files to error directories
   - Cleans up temporary extraction files

## Directory Structure

```
/data/imports/electricity/nzx_gr_reports/
├── GR-170/
│   ├── imported/     # Downloaded files awaiting processing
│   ├── extracted/    # Temporary extraction directory
│   ├── archive/      # Successfully processed files
│   └── error/        # Failed processing files
├── GR-130/
│   ├── imported/
│   ├── extracted/
│   ├── archive/
│   └── error/
└── ... (other GR types)
```

## Database Schema

All tables are created in the `nzx_gr` schema:

- `nzx_gr.gr_170_submission_accuracy`
- `nzx_gr.gr_130_supply_submission`
- `nzx_gr.gr_100_icp_days`
- `nzx_gr.gr_150_icp_days_summary`
- `nzx_gr.gr_090_missing_icps`
- `nzx_gr.gr_140_missing_icps_summary`
- `nzx_gr.import_log` (processing audit trail)

Each table includes:
- File metadata (name, hash, line number)
- GR-specific data fields
- Raw line preservation for debugging
- Created timestamp

## Configuration

### Environment Variables

The DAG uses these environment variables for NZX connection:

```bash
# NZX SFTP Configuration
NZX_PROTOCOL=SFTP
NZX_HOST=your-nzx-host
NZX_PORT=22
NZX_USER=your-username
NZX_PASS=your-password
# Optional: Use private key authentication
NZX_PRIVATE_KEY_PATH=/path/to/private/key
NZX_PRIVATE_KEY_PASSPHRASE=optional-passphrase

# TimescaleDB Configuration
TIMESCALE_DB_HOST=localhost
TIMESCALE_DB_PORT=5434
TIMESCALE_DB_NAME=spoton_timescale
TIMESCALE_DB_USER=postgres
TIMESCALE_DB_PASSWORD=your-password
```

### DAG Settings

- **Schedule**: Every 6 hours (`0 */6 * * *`)
- **Max Active Runs**: 1 (prevents concurrent execution)
- **Catchup**: Disabled
- **Timeout**: 45 minutes per task
- **Retries**: 1 with 5-minute delay

## Data Quality Features

### Validation
- Filename pattern validation
- Field count validation per GR type
- Consumption period format validation (MM/YYYY)
- Revision cycle validation (0,1,3,7,14 for most types)
- Participant code validation (4 characters)
- Type-specific field validation

### Quality Checks
- Missing required fields detection
- Invalid data format identification
- Quality score calculation
- Comprehensive issue reporting

### Monitoring
- Processing statistics logging
- Import audit trail
- Error tracking and reporting
- Performance metrics

## Utilities

### GR Utils Module (`utils/gr_utils.py`)

Provides helper classes and functions:

- **GRReportValidator**: File and data validation
- **GRDataQualityChecker**: Comprehensive quality analysis
- **GRReportSummary**: Statistical summaries
- **log_gr_processing_stats()**: Detailed logging

## Usage Examples

### Query GR-170 Data
```sql
-- Get submission accuracy for a specific period
SELECT * FROM nzx_gr.gr_170_submission_accuracy 
WHERE consumption_period = '01/2025' 
AND revision_cycle = 0;
```

### Check Import Status
```sql
-- Recent import activity
SELECT file_type, status, COUNT(*) as count
FROM nzx_gr.import_log 
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY file_type, status;
```

### Data Quality Summary
```sql
-- Records by GR type
SELECT 
    'GR-170' as report_type, COUNT(*) as records FROM nzx_gr.gr_170_submission_accuracy
UNION ALL
SELECT 
    'GR-130' as report_type, COUNT(*) as records FROM nzx_gr.gr_130_supply_submission
UNION ALL
SELECT 
    'GR-100' as report_type, COUNT(*) as records FROM nzx_gr.gr_100_icp_days;
```

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Verify NZX_HOST and credentials
   - Check network connectivity
   - Validate SFTP key permissions

2. **File Processing Errors**
   - Check file format and encoding
   - Verify gz file integrity
   - Review parsing logs for field mismatches

3. **Database Issues**
   - Ensure TimescaleDB connectivity
   - Check schema permissions
   - Monitor disk space for large imports

### Monitoring

- Check Airflow logs for detailed processing information
- Monitor `nzx_gr.import_log` table for import history
- Review data quality scores in processing logs
- Watch for file accumulation in error directories

## Integration

The GR Reports DAG integrates with:

- **Connection Manager**: Unified SFTP handling
- **TimescaleDB**: Time-series data storage
- **Airflow**: Orchestration and monitoring
- **Logging System**: Comprehensive audit trails

## Performance

- Parallel processing of multiple report types
- Efficient gz extraction and parsing
- Batch database operations
- Optimized indexing for common queries
- File-based duplicate prevention

## Security

- Encrypted SFTP connections
- Secure credential management
- File hash verification
- Audit trail maintenance
- Access control through database permissions 