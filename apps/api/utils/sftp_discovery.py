"""
SFTP File Discovery Module

This module handles SFTP connections and file discovery for the canonical ingestion system.
It connects to provider SFTP servers, lists available files matching patterns, and downloads
them for processing.

Author: SpotOn Data Team
"""
import logging
import paramiko
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import gzip
import os
from dataclasses import dataclass

@dataclass
class SFTPFileInfo:
    """Information about a file on SFTP server"""
    filename: str
    remote_path: str
    size: int
    modified_time: datetime
    is_directory: bool = False

class SFTPFileDiscovery:
    """
    Handles SFTP connections and file discovery for metering data providers
    """
    
    def __init__(self, host: str, port: int, username: str, password: str = None, private_key_path: str = None, private_key_passphrase: str = None):
        """
        Initialize SFTP connection parameters
        
        Args:
            host: SFTP server hostname
            port: SFTP server port
            username: SFTP username
            password: SFTP password (if using password auth)
            private_key_path: Path to private key file (if using key auth)
            private_key_passphrase: Passphrase for private key (if encrypted)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.private_key_passphrase = private_key_passphrase
        self.client = None
        self.sftp = None
        
    def __enter__(self):
        """Context manager entry"""
        if not self.connect():
            raise RuntimeError("Failed to establish SFTP connection")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        
    def connect(self) -> bool:
        """
        Establish SFTP connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Determine authentication method
            if self.private_key_path and os.path.exists(self.private_key_path):
                # Use private key authentication - try different key types
                private_key = None
                key_types = [
                    ('Ed25519', paramiko.Ed25519Key),
                    ('RSA', paramiko.RSAKey),
                    ('ECDSA', paramiko.ECDSAKey),
                    ('DSS', paramiko.DSSKey)
                ]
                
                for key_type_name, key_class in key_types:
                    try:
                        private_key = key_class.from_private_key_file(
                            self.private_key_path, 
                            password=self.private_key_passphrase
                        )
                        logging.info(f"Using {key_type_name} private key for authentication")
                        break
                    except Exception as e:
                        logging.debug(f"Failed to load {key_type_name} key: {e}")
                        continue
                
                if not private_key:
                    raise ValueError(f"Could not load private key from {self.private_key_path}")
                
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=30
                )
                logging.info(f"✅ Connected to {self.host}:{self.port} using private key")
            elif self.password:
                # Use password authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
                logging.info(f"✅ Connected to {self.host}:{self.port} using password")
            else:
                raise ValueError("No authentication method provided (password or private_key_path)")
                
            # Open SFTP channel
            self.sftp = self.client.open_sftp()
            logging.info("✅ SFTP channel opened successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ SFTP connection failed: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Close SFTP connection"""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
            if self.client:
                self.client.close()
                self.client = None
            logging.info("🔌 SFTP connection closed")
        except Exception as e:
            logging.warning(f"⚠️ Error closing SFTP connection: {e}")
    
    def test_connection(self) -> bool:
        """
        Test SFTP connection without keeping it open
        
        Returns:
            bool: True if connection test successful
        """
        try:
            if self.connect():
                self.disconnect()
                return True
            return False
        except Exception as e:
            logging.error(f"❌ SFTP connection test failed: {e}")
            return False
    
    def list_files(self, remote_path: str, pattern: str = None, max_age_days: int = 30) -> List[SFTPFileInfo]:
        """
        List files in remote directory matching pattern
        
        Args:
            remote_path: Remote directory path
            pattern: Regex pattern to match filenames
            max_age_days: Maximum age in days for files to consider
            
        Returns:
            List of SFTPFileInfo objects
        """
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
            
        try:
            logging.info(f"📂 Listing files in {remote_path}")
            
            # List directory contents
            file_attrs = self.sftp.listdir_attr(remote_path)
            
            files = []
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            for attr in file_attrs:
                # Skip directories
                if attr.st_mode and (attr.st_mode & 0o040000):  # S_IFDIR
                    continue
                    
                filename = attr.filename
                
                # Apply pattern filter if provided
                if pattern and not re.match(pattern, filename):
                    continue
                    
                # Convert timestamp
                modified_time = datetime.fromtimestamp(attr.st_mtime) if attr.st_mtime else datetime.now()
                
                # Apply age filter
                if modified_time < cutoff_time:
                    logging.debug(f"⏰ Skipping old file: {filename} (modified: {modified_time})")
                    continue
                
                file_info = SFTPFileInfo(
                    filename=filename,
                    remote_path=f"{remote_path.rstrip('/')}/{filename}",
                    size=attr.st_size or 0,
                    modified_time=modified_time
                )
                
                files.append(file_info)
                logging.info(f"📄 Found: {filename} ({file_info.size} bytes, {modified_time})")
            
            logging.info(f"🎯 Found {len(files)} matching files")
            return files
            
        except Exception as e:
            logging.error(f"❌ Failed to list files in {remote_path}: {e}")
            return []
    
    def download_file(self, remote_file_info: SFTPFileInfo, local_path: Path) -> Optional[Path]:
        """
        Download a file from SFTP server
        
        Args:
            remote_file_info: Information about the remote file
            local_path: Local directory to download to
            
        Returns:
            Path to downloaded file, or None if failed
        """
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
            
        try:
            # Ensure local directory exists
            local_path.mkdir(parents=True, exist_ok=True)
            
            # Determine local filename
            local_file_path = local_path / remote_file_info.filename
            
            logging.info(f"⬇️ Downloading {remote_file_info.filename} ({remote_file_info.size} bytes)")
            
            # Download file
            self.sftp.get(remote_file_info.remote_path, str(local_file_path))
            
            # Verify download
            if local_file_path.exists() and local_file_path.stat().st_size > 0:
                logging.info(f"✅ Downloaded: {local_file_path.name}")
                return local_file_path
            else:
                logging.error(f"❌ Download verification failed: {local_file_path}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Failed to download {remote_file_info.filename}: {e}")
            return None
    
    def download_matching_files(self, remote_path: str, local_path: Path, 
                              patterns: List[str], max_files: int = 10) -> List[Path]:
        """
        Download files matching patterns from remote directory
        
        Args:
            remote_path: Remote directory path
            local_path: Local directory to download to
            patterns: List of regex patterns to match
            max_files: Maximum number of files to download
            
        Returns:
            List of paths to downloaded files
        """
        downloaded_files = []
        
        try:
            for pattern in patterns:
                if len(downloaded_files) >= max_files:
                    break
                    
                logging.info(f"🔍 Searching for files matching: {pattern}")
                
                # List files matching pattern (use 3650 days = ~10 years for age limit)
                file_infos = self.list_files(remote_path, pattern, max_age_days=3650)
                
                # Sort by modification time (newest first)
                file_infos.sort(key=lambda f: f.modified_time, reverse=True)
                
                # Download files
                for file_info in file_infos:
                    if len(downloaded_files) >= max_files:
                        break
                        
                    local_file = self.download_file(file_info, local_path)
                    if local_file:
                        downloaded_files.append(local_file)
            
            logging.info(f"🎯 Downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            logging.error(f"❌ Failed to download matching files: {e}")
            return downloaded_files

def create_sftp_discovery(connection_config: Dict) -> SFTPFileDiscovery:
    """
    Factory function to create SFTPFileDiscovery from connection config
    
    Args:
        connection_config: Dictionary containing connection parameters
        
    Returns:
        Configured SFTPFileDiscovery instance
    """
    # Handle empty strings as None for proper authentication method selection
    password = connection_config.get('password')
    if password == '':
        password = None
        
    private_key_path = connection_config.get('private_key_path')
    if private_key_path == '':
        private_key_path = None
        
    private_key_passphrase = connection_config.get('private_key_passphrase')
    if private_key_passphrase == '':
        private_key_passphrase = None
    
    return SFTPFileDiscovery(
        host=connection_config.get('host'),
        port=connection_config.get('port', 22),
        username=connection_config.get('user') or connection_config.get('username'),
        password=password,
        private_key_path=private_key_path,
        private_key_passphrase=private_key_passphrase
    )

def discover_provider_files(provider: str, read_type: str, connection_config: Dict, 
                          provider_config: Dict, local_path: Path) -> List[Path]:
    """
    High-level function to discover and download files for a provider
    
    Args:
        provider: Provider name (e.g., 'bluecurrent')
        read_type: Read type (e.g., 'daily', 'interval')
        connection_config: SFTP connection configuration
        provider_config: Provider configuration from providers.yml
        local_path: Local path to download files to
        
    Returns:
        List of downloaded file paths
    """
    logging.info(f"🔎 Starting file discovery for {provider} {read_type}")
    
    try:
        # Create SFTP discovery instance
        with create_sftp_discovery(connection_config) as sftp:
            # Get file patterns for this read type
            patterns = []
            for version in provider_config.get('versions', []):
                detection_rules = version.get('detection_rules', {})
                if detection_rules.get('read_type') == read_type:
                    pattern = detection_rules.get('filename_pattern')
                    if pattern:
                        patterns.append(pattern)
            
            if not patterns:
                logging.warning(f"⚠️ No file patterns found for {provider} {read_type}")
                return []
            
            # Get remote path from provider config - check for read-type-specific path first
            sftp_config = provider_config.get('sftp_config', {})
            read_type_config = sftp_config.get(read_type, {})
            remote_path = read_type_config.get('remote_path') or sftp_config.get('remote_path', '/')
            
            # Download matching files (use 3650 days = ~10 years for age limit)
            downloaded_files = sftp.download_matching_files(
                remote_path=remote_path,
                local_path=local_path,
                patterns=patterns,
                max_files=5  # Limit to prevent overwhelming the system
            )
            
            logging.info(f"🎯 File discovery complete: {len(downloaded_files)} files downloaded")
            return downloaded_files
            
    except Exception as e:
        logging.error(f"❌ File discovery failed for {provider} {read_type}: {e}")
        return [] 