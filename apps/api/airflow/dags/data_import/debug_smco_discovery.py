"""
Debug script for SMCO file discovery issues

This script helps diagnose why no HHR files are being found in the SMCO DAG.
Run this to check:
1. SFTP connection to SMCO
2. Files in DRR folder
3. Files in HERM folder
4. File classification logic

Usage:
python debug_smco_discovery.py
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add paths
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/data_import/utils")

def debug_smco_connection():
    """Debug SMCO SFTP connection"""
    print("🔍 DEBUG: Testing SMCO Connection")
    
    try:
        from connection_manager import ConnectionManager
        
        # SMCO connection config
        conn_config = {
            'protocol': os.getenv('SMARTCO_RES_PROTOCOL', 'SFTP'),
            'host': os.getenv('SMARTCO_RES_HOST'),
            'port': int(os.getenv('SMARTCO_RES_PORT', '22')),
            'user': os.getenv('SMARTCO_RES_USER'),
            'password': os.getenv('SMARTCO_RES_PASS'),
            'remote_paths': {
                'drr': '/SFTP/DailyRegisterRead',  # Daily Register Reads
                'hhr': '/SFTP/HERM/Bulk',          # Half-Hourly in HERM/Bulk folder
            },
            'remote_path': '/SFTP/DailyRegisterRead'   # Default to DRR folder
        }
        
        print(f"Host: {conn_config['host']}")
        print(f"Port: {conn_config['port']}")
        print(f"User: {conn_config['user']}")
        print(f"DRR Path: {conn_config['remote_paths']['drr']}")
        print(f"HHR Path: {conn_config['remote_paths']['hhr']}")
        
        if ConnectionManager.test_connection(conn_config):
            print("✅ SMCO connection successful")
            return conn_config
        else:
            print("❌ SMCO connection failed")
            return None
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return None

def debug_file_discovery(conn_config):
    """Debug file discovery in both folders"""
    print("\n🔍 DEBUG: Discovering Files")
    
    try:
        from utils.sftp_discovery import SFTPDiscovery
    except ImportError:
        try:
            from metering_etl import SFTPDiscovery
        except ImportError:
            print("❌ Could not import SFTPDiscovery")
            return
    
    # Check DRR folder
    print(f"\n📁 Checking DRR folder: {conn_config['remote_paths']['drr']}")
    drr_config = conn_config.copy()
    drr_config['remote_path'] = conn_config['remote_paths']['drr']
    
    try:
        with SFTPDiscovery(drr_config) as drr_discovery:
            drr_files = drr_discovery.discover_files()
            print(f"📊 Found {len(drr_files)} files in DRR folder")
            
            for i, f in enumerate(drr_files[:10]):  # Show first 10
                print(f"  {i+1}. {f['filename']} ({f.get('size', 0)} bytes)")
            
            if len(drr_files) > 10:
                print(f"  ... and {len(drr_files) - 10} more files")
                
    except Exception as e:
        print(f"❌ Error checking DRR folder: {e}")
    
    # Check HERM folder
    print(f"\n📁 Checking HERM folder: {conn_config['remote_paths']['hhr']}")
    herm_config = conn_config.copy()
    herm_config['remote_path'] = conn_config['remote_paths']['hhr']
    
    try:
        with SFTPDiscovery(herm_config) as herm_discovery:
            herm_files = herm_discovery.discover_files()
            print(f"📊 Found {len(herm_files)} files in HERM folder")
            
            for i, f in enumerate(herm_files[:10]):  # Show first 10
                print(f"  {i+1}. {f['filename']} ({f.get('size', 0)} bytes)")
                
                # Check file extension
                filename = f['filename'].lower()
                if filename.endswith('.csv'):
                    print(f"      ✅ CSV file - will be included")
                elif filename.endswith('.new'):
                    print(f"      ✅ NEW file - will be included")
                else:
                    print(f"      ❌ Other extension - will be filtered out")
            
            if len(herm_files) > 10:
                print(f"  ... and {len(herm_files) - 10} more files")
                
            # Check file extensions summary
            csv_files = [f for f in herm_files if f['filename'].lower().endswith('.csv')]
            new_files = [f for f in herm_files if f['filename'].lower().endswith('.new')]
            other_files = [f for f in herm_files if not f['filename'].lower().endswith(('.csv', '.new'))]
            
            print(f"\n📊 HERM File Extension Summary:")
            print(f"  CSV files: {len(csv_files)}")
            print(f"  NEW files: {len(new_files)}")
            print(f"  Other files: {len(other_files)}")
            
            if other_files:
                print(f"  Other file extensions:")
                extensions = set([f['filename'].split('.')[-1].lower() for f in other_files if '.' in f['filename']])
                for ext in sorted(extensions):
                    count = len([f for f in other_files if f['filename'].lower().endswith(f'.{ext}')])
                    print(f"    .{ext}: {count} files")
                
    except Exception as e:
        print(f"❌ Error checking HERM folder: {e}")

def debug_file_classification():
    """Debug file classification logic"""
    print("\n🔍 DEBUG: File Classification Logic")
    
    # Test classification examples
    test_files = [
        {'filename': 'test.csv', 'folder_type': 'drr', 'source_folder': 'DRR'},
        {'filename': 'test.new', 'folder_type': 'herm', 'source_folder': 'HERM'},
        {'filename': 'daily_data.csv', 'folder_type': 'drr', 'source_folder': 'DRR'},
        {'filename': 'interval_data.new', 'folder_type': 'herm', 'source_folder': 'HERM'},
        {'filename': 'unknown.txt', 'folder_type': 'unknown', 'source_folder': 'unknown'},
    ]
    
    for file_info in test_files:
        # Simulate classification logic from download_smco_files
        if file_info.get('folder_type') == 'drr' or file_info.get('source_folder') == 'DRR':
            file_type = 'daily'
            folder_desc = "DRR folder"
        elif file_info.get('folder_type') == 'herm' or file_info.get('source_folder') == 'HERM':
            file_type = 'interval'
            folder_desc = "HERM folder"
        else:
            # Fallback logic
            if 'daily' in file_info['filename'].lower() or 'drr' in file_info['filename'].lower():
                file_type = 'daily'
                folder_desc = "filename pattern (daily)"
            elif file_info['filename'].lower().endswith('.new'):
                file_type = 'interval'
                folder_desc = ".new extension"
            else:
                file_type = 'interval'
                folder_desc = "default fallback"
        
        print(f"  {file_info['filename']} → {file_type} ({folder_desc})")

def main():
    """Main debug function"""
    print("🔧 SMCO File Discovery Debug Tool")
    print("=" * 50)
    
    # Test connection
    conn_config = debug_smco_connection()
    if not conn_config:
        print("❌ Cannot proceed without connection")
        return
    
    # Test file discovery
    debug_file_discovery(conn_config)
    
    # Test classification logic
    debug_file_classification()
    
    print("\n✅ Debug complete!")
    print("\nNext steps to fix 'No HHR data to load' issue:")
    print("1. Check if HERM folder has files with .csv or .new extensions")
    print("2. Verify files are being classified as 'interval' type")
    print("3. Check if files are already processed (duplicate detection)")
    print("4. Look at earlier DAG task logs for file discovery results")

if __name__ == "__main__":
    main() 