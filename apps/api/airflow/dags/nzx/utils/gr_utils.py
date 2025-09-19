"""
GR Reports Utility Functions

Helper functions for processing NZX GR reports including:
- File validation
- Data quality checks
- Report type identification
- Schema validation

Author: SpotOn Data Team
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

class GRReportValidator:
    """Validator for GR report files and data"""
    
    # GR report filename patterns (case-insensitive match)
    GR_PATTERNS = {
        'GR-170': r'NZRM_E_\w{4}_ACCY(NHH|HHR)_\d{6}_\d{8}_\d{6}\.(abc|ABC)\.(gz|GZ)',
        'GR-130': r'NZRM_E_\w{4}_ESUPSUB_\d{6}_\d{8}_\d{6}\.(abc|ABC)\.(gz|GZ)',
        'GR-100': r'NZRM_E_\w{4}_ICPCOMP_\d{6}_\d{8}_\d{6}\.(abc|ABC)\.(gz|GZ)',
        'GR-150': r'NZRM_E_\w{4}_ICPCSUM_\d{6}_\d{8}_\d{6}\.(abc|ABC)\.(gz|GZ)',
        'GR-090': r'NZRM_E_\w{4}_ICPMISS_\d{6}_\d{8}_\d{6}\.(abc|ABC)\.(gz|GZ)',
        'GR-140': r'NZRM_E_\w{4}_ICPMSUM_\d{6}_\d{8}_\d{6}\.(abc|ABC)\.(gz|GZ)'
    }
    
    # Expected field counts for each GR report type
    EXPECTED_FIELDS = {
        'GR-170': 12,  # consumption_period through pct_variation_historical_vs_initial
        'GR-130': 10,  # consumption_period through sales_submission_ratio
        'GR-100': 11,  # consumption_period through percentage_difference
        'GR-150': 5,   # consumption_period through difference_registry_purchaser
        'GR-090': 8,   # consumption_period through icp_number
        'GR-140': 4    # consumption_period through number_of_discrepancies
    }
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate GR report filename and extract metadata
        
        Returns:
            (is_valid, gr_type, metadata_dict)
        """
        filename_upper = filename.upper()
        
        for gr_type, pattern in GRReportValidator.GR_PATTERNS.items():
            if re.match(pattern, filename_upper):
                metadata = GRReportValidator._extract_metadata(filename_upper, gr_type)
                return True, gr_type, metadata
        
        return False, None, None
    
    @staticmethod
    def _extract_metadata(filename: str, gr_type: str) -> Dict:
        """Extract metadata from GR report filename"""
        # Pattern: NZRM_E_ABCD_TYPE_YYYYMM_YYYYMMDD_HHMISS.abc.gz
        parts = filename.replace('.ABC.GZ', '').split('_')
        
        if len(parts) >= 7:
            return {
                'market': parts[0],  # NZRM
                'type': parts[1],    # E
                'participant': parts[2],  # ABCD
                'report_type': parts[3],  # ACCYNHH, ESUPSUB, etc.
                'period': parts[4],  # YYYYMM
                'date': parts[5],    # YYYYMMDD
                'time': parts[6],    # HHMISS
                'gr_type': gr_type
            }
        
        return {'gr_type': gr_type}
    
    @staticmethod
    def validate_record_count(records: List[Dict], gr_type: str) -> Tuple[bool, str]:
        """Validate record field counts for GR report type"""
        expected_count = GRReportValidator.EXPECTED_FIELDS.get(gr_type, 0)
        
        if expected_count == 0:
            return True, f"Unknown GR type {gr_type}, skipping field count validation"
        
        invalid_records = []
        for i, record in enumerate(records):
            raw_line = record.get('raw_line', '')
            field_count = len(raw_line.split(',')) if raw_line else 0
            
            if field_count < expected_count:
                invalid_records.append({
                    'line': i + 1,
                    'expected': expected_count,
                    'actual': field_count
                })
        
        if invalid_records:
            error_msg = f"Field count validation failed for {gr_type}:\n"
            for error in invalid_records[:5]:  # Show first 5 errors
                error_msg += f"  Line {error['line']}: expected {error['expected']}, got {error['actual']}\n"
            if len(invalid_records) > 5:
                error_msg += f"  ... and {len(invalid_records) - 5} more errors"
            return False, error_msg
        
        return True, f"All {len(records)} records passed field count validation"
    
    @staticmethod
    def validate_consumption_period(period: str) -> bool:
        """Validate consumption period format (MM/YYYY)"""
        if not period:
            return False
        
        pattern = r'^\d{2}/\d{4}$'
        if not re.match(pattern, period):
            return False
        
        try:
            month, year = period.split('/')
            month_int = int(month)
            year_int = int(year)
            
            return 1 <= month_int <= 12 and 2000 <= year_int <= 2100
        except:
            return False
    
    @staticmethod
    def validate_revision_cycle(cycle: int, gr_type: str) -> bool:
        """Validate revision cycle values for GR report type"""
        if cycle is None:
            return False
        
        # Most GR reports use: 0,1,3,7,14
        standard_cycles = [0, 1, 3, 7, 14]
        
        # GR-130 also includes 18, 24
        if gr_type == 'GR-130':
            standard_cycles.extend([18, 24])
        
        return cycle in standard_cycles

class GRDataQualityChecker:
    """Data quality checker for GR report data"""
    
    @staticmethod
    def check_data_quality(records: List[Dict], gr_type: str) -> Dict:
        """
        Perform comprehensive data quality checks
        
        Returns:
            {
                'total_records': int,
                'valid_records': int,
                'quality_score': float,
                'issues': [list of issues],
                'warnings': [list of warnings]
            }
        """
        total_records = len(records)
        if total_records == 0:
            return {
                'total_records': 0,
                'valid_records': 0,
                'quality_score': 0.0,
                'issues': ['No records found'],
                'warnings': []
            }
        
        issues = []
        warnings = []
        valid_count = 0
        
        # Check each record
        for i, record in enumerate(records):
            line_num = i + 1
            is_valid = True
            
            # Check consumption period
            period = record.get('consumption_period', '')
            if not GRReportValidator.validate_consumption_period(period):
                issues.append(f"Line {line_num}: Invalid consumption period '{period}'")
                is_valid = False
            
            # Check revision cycle
            cycle = record.get('revision_cycle')
            if not GRReportValidator.validate_revision_cycle(cycle, gr_type):
                issues.append(f"Line {line_num}: Invalid revision cycle '{cycle}' for {gr_type}")
                is_valid = False
            
            # Check participant code
            participant = record.get('participant_code', '')
            if not participant or len(participant) != 4:
                issues.append(f"Line {line_num}: Invalid participant code '{participant}'")
                is_valid = False
            
            # Type-specific checks
            if gr_type in ['GR-170', 'GR-100']:
                metering_type = record.get('metering_type', '')
                if metering_type not in ['HHR', 'NHH']:
                    issues.append(f"Line {line_num}: Invalid metering type '{metering_type}'")
                    is_valid = False
            
            if gr_type == 'GR-090':
                discrepancy_type = record.get('discrepancy_type', '')
                if discrepancy_type not in ['R', 'A']:
                    issues.append(f"Line {line_num}: Invalid discrepancy type '{discrepancy_type}'")
                    is_valid = False
                
                icp_number = record.get('icp_number', '')
                if not icp_number or len(icp_number) > 15:
                    issues.append(f"Line {line_num}: Invalid ICP number '{icp_number}'")
                    is_valid = False
            
            # Check for missing required fields
            required_fields = GRDataQualityChecker._get_required_fields(gr_type)
            for field in required_fields:
                if not record.get(field):
                    warnings.append(f"Line {line_num}: Missing {field}")
            
            if is_valid:
                valid_count += 1
        
        # Calculate quality score
        quality_score = (valid_count / total_records) * 100 if total_records > 0 else 0
        
        return {
            'total_records': total_records,
            'valid_records': valid_count,
            'quality_score': quality_score,
            'issues': issues,
            'warnings': warnings
        }
    
    @staticmethod
    def _get_required_fields(gr_type: str) -> List[str]:
        """Get required fields for each GR report type"""
        common_fields = ['consumption_period', 'revision_cycle', 'participant_code']
        
        type_specific = {
            'GR-170': ['balancing_area', 'poc', 'network_id', 'metering_type'],
            'GR-130': ['nsp', 'balancing_area', 'participant_identifier'],
            'GR-100': ['balancing_area', 'poc', 'network_id', 'metering_type'],
            'GR-150': ['metering_type'],
            'GR-090': ['balancing_area', 'poc', 'network_id', 'discrepancy_type', 'icp_number'],
            'GR-140': []
        }
        
        return common_fields + type_specific.get(gr_type, [])

class GRReportSummary:
    """Generate summary statistics for GR reports"""
    
    @staticmethod
    def generate_summary(records: List[Dict], gr_type: str, filename: str) -> Dict:
        """Generate comprehensive summary of GR report data"""
        if not records:
            return {
                'filename': filename,
                'gr_type': gr_type,
                'total_records': 0,
                'summary': 'No records processed'
            }
        
        summary = {
            'filename': filename,
            'gr_type': gr_type,
            'total_records': len(records),
            'periods': set(),
            'revision_cycles': set(),
            'participants': set(),
            'date_range': {'earliest': None, 'latest': None}
        }
        
        # Collect statistics
        for record in records:
            # Consumption periods
            period = record.get('consumption_period')
            if period:
                summary['periods'].add(period)
            
            # Revision cycles
            cycle = record.get('revision_cycle')
            if cycle is not None:
                summary['revision_cycles'].add(cycle)
            
            # Participants
            participant = record.get('participant_code')
            if participant:
                summary['participants'].add(participant)
        
        # Convert sets to sorted lists for JSON serialization
        summary['periods'] = sorted(list(summary['periods']))
        summary['revision_cycles'] = sorted(list(summary['revision_cycles']))
        summary['participants'] = sorted(list(summary['participants']))
        
        # Add type-specific summaries
        if gr_type in ['GR-170', 'GR-100']:
            metering_types = set()
            for record in records:
                mt = record.get('metering_type')
                if mt:
                    metering_types.add(mt)
            summary['metering_types'] = sorted(list(metering_types))
        
        if gr_type == 'GR-090':
            discrepancy_types = set()
            for record in records:
                dt = record.get('discrepancy_type')
                if dt:
                    discrepancy_types.add(dt)
            summary['discrepancy_types'] = sorted(list(discrepancy_types))
        
        return summary

def log_gr_processing_stats(filename: str, gr_type: str, records: List[Dict], 
                           quality_check: Dict, processing_time: float):
    """Log comprehensive processing statistics for GR reports"""
    
    logging.info(f"📊 GR Report Processing Summary for {filename}")
    logging.info(f"  📄 Report Type: {gr_type}")
    logging.info(f"  📝 Total Records: {len(records)}")
    logging.info(f"  ✅ Valid Records: {quality_check.get('valid_records', 0)}")
    logging.info(f"  📈 Quality Score: {quality_check.get('quality_score', 0):.1f}%")
    logging.info(f"  ⏱️ Processing Time: {processing_time:.2f}s")
    
    # Log issues if any
    issues = quality_check.get('issues', [])
    if issues:
        logging.warning(f"  ⚠️ Data Quality Issues ({len(issues)}):")
        for issue in issues[:3]:  # Show first 3 issues
            logging.warning(f"    - {issue}")
        if len(issues) > 3:
            logging.warning(f"    - ... and {len(issues) - 3} more issues")
    
    # Log warnings if any
    warnings = quality_check.get('warnings', [])
    if warnings:
        logging.info(f"  💡 Warnings ({len(warnings)}):")
        for warning in warnings[:3]:  # Show first 3 warnings
            logging.info(f"    - {warning}")
        if len(warnings) > 3:
            logging.info(f"    - ... and {len(warnings) - 3} more warnings")
    
    # Generate summary
    summary = GRReportSummary.generate_summary(records, gr_type, filename)
    
    if summary.get('periods'):
        logging.info(f"  📅 Periods: {', '.join(summary['periods'])}")
    
    if summary.get('revision_cycles'):
        logging.info(f"  🔄 Revision Cycles: {', '.join(map(str, summary['revision_cycles']))}")
    
    if summary.get('participants'):
        participant_count = len(summary['participants'])
        if participant_count <= 5:
            logging.info(f"  👥 Participants: {', '.join(summary['participants'])}")
        else:
            logging.info(f"  👥 Participants: {participant_count} unique participants")
    
    logging.info(f"✅ Completed processing {filename}") 