"""
Connection Manager Utility for Airflow DAGs

Centralized connection management for various file transfer protocols.
Supports SFTP, FTPS, and potential future protocols with robust error handling.

Author: SpotOn Data Team
"""

import os
import ssl
import paramiko
from ftplib import FTP_TLS, FTP
from typing import Dict, Tuple, List, Optional
from pathlib import Path
import logging
import re
import time


class ConnectionManager:
    """
    Centralized connection management for various file transfer protocols
    Supports SFTP, FTPS, and potential future protocols
    """
    
    @staticmethod
    def get_connection_config(
        protocol: str = 'SFTP', 
        prefix: str = 'NZX',
        default_host: Optional[str] = None,
        default_port: Optional[int] = None,
        default_user: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get connection configuration from environment variables
        
        :param protocol: Connection protocol (SFTP, FTPS)
        :param prefix: Environment variable prefix (e.g., NZX, MTRX)
        :param default_host: Default host if not specified in environment
        :param default_port: Default port if not specified in environment
        :param default_user: Default user if not specified in environment
        :return: Connection configuration dictionary
        """
        # Get values from environment variables with fallbacks to defaults
        env_host = os.getenv(f'{prefix}_HOST')
        host = (env_host.strip() if env_host is not None else default_host) or 'localhost'
        
        env_port = os.getenv(f'{prefix}_PORT')
        try:
            port = int(env_port) if env_port is not None else (default_port or 22)
        except ValueError:
            port = default_port or 22
        
        env_user = os.getenv(f'{prefix}_USER')
        user = (env_user.strip() if env_user is not None else default_user) or 'anonymous'
        
        # Check for password in both PREFIX_PASS and PREFIX_PASSWORD environment variables
        env_pass = os.getenv(f'{prefix}_PASS') or os.getenv(f'{prefix}_PASSWORD')
        password = env_pass.strip() if env_pass is not None else ''
        
        # Check for key in both PREFIX_KEY and PREFIX_PRIVATE_KEY environment variables
        env_key = os.getenv(f'{prefix}_KEY') or os.getenv(f'{prefix}_PRIVATE_KEY')
        key_path = env_key.strip() if env_key is not None else None
        
        # Check for key passphrase
        env_key_pass = os.getenv(f'{prefix}_KEY_PASSPHRASE') or os.getenv(f'{prefix}_PRIVATE_KEY_PASSPHRASE')
        key_passphrase = env_key_pass.strip() if env_key_pass is not None else None
        
        env_remote_path = os.getenv(f'{prefix}_REMOTE_PATH')
        remote_path = env_remote_path.strip() if env_remote_path is not None else '/'
        
        # Timeout settings
        env_timeout = os.getenv(f'{prefix}_TIMEOUT')
        try:
            timeout = int(env_timeout) if env_timeout is not None else 30
        except ValueError:
            timeout = 30
        
        # FTPS specific settings
        env_explicit = os.getenv(f'{prefix}_FTPS_EXPLICIT')
        ftps_explicit = ConnectionManager._parse_bool_env(env_explicit, True)
        
        env_verify = os.getenv(f'{prefix}_VERIFY_SSL')
        verify_ssl = ConnectionManager._parse_bool_env(env_verify, False)
        
        # Retry settings
        env_retries = os.getenv(f'{prefix}_MAX_RETRIES')
        try:
            max_retries = int(env_retries) if env_retries is not None else 3
        except ValueError:
            max_retries = 3
        
        config = {
            'protocol': protocol.upper(),
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'key_path': key_path,
            'key_passphrase': key_passphrase,
            'remote_path': remote_path,
            'timeout': timeout,
            'ftps_explicit': ftps_explicit,
            'verify_ssl': verify_ssl,
            'max_retries': max_retries
        }
        
        return config
    
    @staticmethod
    def _parse_bool_env(env_var: str, default: bool) -> bool:
        """
        Parse boolean environment variable
        
        :param env_var: Environment variable name or value
        :param default: Default value if not specified
        :return: Boolean value
        """
        if env_var is None:
            return default
            
        # If env_var is already a string value, use it directly
        if not env_var.startswith('$'):
            value = env_var.lower().strip()
        else:
            # Otherwise treat it as an environment variable name
            env_name = env_var.lstrip('$')
            env_value = os.getenv(env_name)
            if env_value is None:
                return default
            value = env_value.lower().strip()
        
        return value in ('true', 'yes', 'y', '1', 'on')
    
    @staticmethod
    def create_ssl_context(verify: bool = False) -> ssl.SSLContext:
        """
        Create a flexible SSL context for FTPS connections
        
        :param verify: Whether to verify SSL certificates
        :return: Configured SSL context
        """
        context = ssl.create_default_context()
        
        if not verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Compatibility settings for self-signed or legacy certificates
        context.set_ciphers('DEFAULT:@SECLEVEL=1')
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE
        
        return context
    
    @classmethod
    def connect_sftp(cls, config: Dict[str, str]) -> Tuple[paramiko.SFTPClient, paramiko.SSHClient]:
        """
        Establish SFTP connection with robust error handling and multiple authentication methods
        
        :param config: Connection configuration dictionary
        :return: Tuple of (SFTP client, SSH client)
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Prepare connection parameters
            connect_params = {
                'hostname': config['host'],
                'port': config['port'],
                'username': config['user'],
                'timeout': config.get('timeout', 30),
                'compress': True,
                'allow_agent': False,
                'look_for_keys': False,
            }
            
            # Log connection attempt
            logging.info(f"Connecting to SFTP server {config['host']}:{config['port']} as {config['user']}")
            
            # Always use password if available (simplest authentication method)
            if 'password' in config and config['password']:
                connect_params['password'] = config['password']
                logging.info("Using password authentication")
            # Fall back to key authentication if available
            elif config.get('key_path'):
                # SSH Key authentication
                from pathlib import Path
                key_path = Path(config['key_path'])
                
                try:
                    # Try different key types
                    private_key = None
                    key_passphrase = config.get('key_passphrase') or None
                    
                    # Try RSA key first
                    try:
                        private_key = paramiko.RSAKey.from_private_key_file(
                            str(key_path), 
                            password=key_passphrase
                        )
                        logging.info("Using RSA private key for authentication")
                    except paramiko.PasswordRequiredException:
                        raise ValueError("Private key requires passphrase, set {prefix}_PRIVATE_KEY_PASSPHRASE")
                    except paramiko.SSHException:
                        # Try DSS key
                        try:
                            private_key = paramiko.DSSKey.from_private_key_file(
                                str(key_path), 
                                password=key_passphrase
                            )
                            logging.info("Using DSS private key for authentication")
                        except paramiko.SSHException:
                            # Try ECDSA key
                            try:
                                private_key = paramiko.ECDSAKey.from_private_key_file(
                                    str(key_path), 
                                    password=key_passphrase
                                )
                                logging.info("Using ECDSA private key for authentication")
                            except paramiko.SSHException:
                                # Try Ed25519 key
                                try:
                                    private_key = paramiko.Ed25519Key.from_private_key_file(
                                        str(key_path), 
                                        password=key_passphrase
                                    )
                                    logging.info("Using Ed25519 private key for authentication")
                                except paramiko.SSHException:
                                    raise ValueError(f"Unsupported private key format: {key_path}")
                    
                    connect_params['pkey'] = private_key
                    
                except Exception as e:
                    raise ValueError(f"Failed to load private key from {key_path}: {str(e)}")
            
            else:
                # Try to use any available authentication method
                connect_params['allow_agent'] = True
                connect_params['look_for_keys'] = True
                logging.info("No explicit authentication method provided, trying available methods")
            
            # Establish SSH connection
            ssh.connect(**connect_params)
            
            # Open SFTP channel
            sftp = ssh.open_sftp()
            
            # Test connection by listing root directory
            sftp.listdir('.')
            
            logging.info(f"✅ SFTP connection established to {config['host']}:{config['port']}")
            return sftp, ssh
        
        except Exception as e:
            if ssh:
                ssh.close()
            logging.error(f"❌ SFTP connection failed: {str(e)}")
            raise ConnectionError(f"SFTP connection failed: {str(e)}")
    
    @classmethod
    def connect_ftps(cls, config: Dict[str, str]) -> FTP_TLS:
        """
        Establish explicit FTPS connection with robust error handling
        
        :param config: Connection configuration dictionary
        :return: FTPS client
        """
        # Create SSL context based on verification setting
        ssl_context = cls.create_ssl_context(config.get('verify_ssl', False))
        
        # Custom FTP_TLS class for explicit FTPS with plain data connections
        class FTP_TLS_Explicit(FTP_TLS):
            def ntransfercmd(self, cmd, rest=None):
                """Override to always use plain data connections for FileZilla compatibility"""
                # Always use plain FTP data connections to avoid TLS session resumption issues
                # Control connection remains encrypted for secure authentication
                conn, size = FTP.ntransfercmd(self, cmd, rest)
                return conn, size
        
        try:
            # Create explicit FTPS connection
            ftps = FTP_TLS_Explicit(context=ssl_context)
            
            # Connect and secure control connection
            ftps.connect(config['host'], config['port'], timeout=30)
            ftps.auth()  # Upgrade to TLS
            
            # Login after securing control connection
            ftps.login(config['user'], config['password'])
            
            # Set passive mode based on configuration
            ftps.set_pasv(config.get('passive_mode', True))
            
            logging.info(f"✅ FTPS connection established to {config['host']}:{config['port']}")
            return ftps
        
        except Exception as e:
            logging.error(f"❌ FTPS connection failed: {str(e)}")
            raise ConnectionError(f"FTPS connection failed: {str(e)}")
    
    @classmethod
    def test_connection(cls, config: Dict[str, str]) -> bool:
        """
        Test connection to remote server
        
        :param config: Connection configuration
        :return: Whether connection test was successful
        """
        try:
            if config['protocol'] == 'SFTP':
                sftp, ssh = cls.connect_sftp(config)
                sftp.close()
                ssh.close()
            elif config['protocol'] == 'FTPS':
                ftps = cls.connect_ftps(config)
                ftps.quit()
            
            logging.info(f"✅ {config['protocol']} connection test successful")
            return True
            
        except Exception as e:
            logging.error(f"❌ {config['protocol']} connection test failed: {e}")
            return False
    
    @classmethod
    def list_remote_files(
        cls, 
        config: Dict[str, str], 
        file_pattern: str = r'^.*$'
    ) -> List[str]:
        """
        List files on remote server matching a pattern
        
        :param config: Connection configuration
        :param file_pattern: Regex pattern to filter files
        :return: List of matching filenames
        """
        try:
            logging.info(f"📁 Listing files on {config['host']}:{config['port']} at {config.get('remote_path', '/')} matching pattern '{file_pattern}'")
            
            # Check if we have authentication credentials
            if 'user' not in config or not config['user']:
                logging.warning(f"No username provided for {config['protocol']} connection to {config['host']}")
                config['user'] = 'anonymous'
            
            if 'password' not in config or not config['password']:
                logging.warning(f"No authentication credentials provided for {config['protocol']} connection to {config['host']}")
            
            if config['protocol'] == 'SFTP':
                # Connect to SFTP server
                sftp, ssh = cls.connect_sftp(config)
                
                try:
                    # Change to remote directory
                    remote_path = config.get('remote_path', '/')
                    if remote_path and remote_path != '/':
                        try:
                            sftp.chdir(remote_path)
                        except IOError as e:
                            logging.error(f"❌ Remote path does not exist: {remote_path}")
                            sftp.close()
                            ssh.close()
                            return []
                    
                    # List files in directory
                    files = sftp.listdir()
                    
                    # Filter files by pattern
                    import re
                    pattern = re.compile(file_pattern)
                    matching_files = [f for f in files if pattern.match(f)]
                    
                    logging.info(f"📁 Found {len(matching_files)}/{len(files)} matching files")
                    
                    # Close connections
                    sftp.close()
                    ssh.close()
                    
                    return matching_files
                    
                except Exception as e:
                    logging.error(f"❌ Error listing files: {str(e)}")
                    # Ensure connections are closed
                    try:
                        sftp.close()
                        ssh.close()
                    except:
                        pass
                    raise
                    
            elif config['protocol'] == 'FTPS':
                # FTPS implementation (similar to above)
                ftps = cls.connect_ftps(config)
                try:
                    ftps.cwd(config.get('remote_path', '/'))
                    files = ftps.nlst()
                    return [f for f in files if re.match(file_pattern, f)]
                except Exception as e:
                    logging.error(f"❌ Error listing FTPS files: {str(e)}")
                    raise
                finally:
                    try:
                        ftps.quit()
                    except:
                        pass
                
            else:
                logging.error(f"❌ Unsupported protocol: {config['protocol']}")
                return []
                
        except Exception as e:
            logging.error(f"❌ Error listing remote files: {str(e)}")
            raise
    
    @classmethod
    def download_file(
        cls, 
        config: Dict[str, str], 
        filename: str, 
        local_path: Path, 
        max_retries: Optional[int] = None
    ) -> bool:
        """
        Download a single file from remote server with retry logic
        
        :param config: Connection configuration
        :param filename: Name of file to download
        :param local_path: Local path to save file
        :param max_retries: Number of download retry attempts (uses config default if None)
        :return: Whether download was successful
        """
        # Use config retry settings if not specified
        if max_retries is None:
            max_retries = config.get('max_retries', 3)
        
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                if config['protocol'] == 'SFTP':
                    sftp, ssh = cls.connect_sftp(config)
                    try:
                        sftp.chdir(config.get('remote_path', '/'))
                        sftp.get(filename, str(local_path))
                        
                        # Verify file download
                        if local_path.exists() and local_path.stat().st_size > 0:
                            logging.info(f"✅ Downloaded {filename} via SFTP")
                            return True
                        else:
                            raise Exception("Downloaded file is empty or missing")
                    finally:
                        sftp.close()
                        ssh.close()
                
                elif config['protocol'] == 'FTPS':
                    ftps = cls.connect_ftps(config)
                    try:
                        ftps.cwd(config.get('remote_path', '/'))
                        with open(local_path, 'wb') as local_file:
                            ftps.retrbinary(f'RETR {filename}', local_file.write)
                        
                        # Verify file download
                        if local_path.exists() and local_path.stat().st_size > 0:
                            logging.info(f"✅ Downloaded {filename} via FTPS")
                            return True
                        else:
                            raise Exception("Downloaded file is empty or missing")
                    finally:
                        ftps.quit()
            
            except Exception as e:
                logging.warning(f"❌ Download attempt {attempt + 1} failed for {filename}: {e}")
                
                # Clean up partial download
                if local_path.exists():
                    local_path.unlink()
                
                if attempt < max_retries - 1:
                    logging.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"❌ All download attempts failed for {filename}")
                    return False
        
        return False


class DataSourceConfig:
    """
    Configuration class for different data sources
    """
    
    # WITS NZX Wholesale Prices
    WITS_NZX_PRICES = {
        'prefix': 'NZX',
        'protocol': 'SFTP',
        'default_host': None,  # Use NZX_HOST env var
        'default_port': None,  # Use NZX_PORT env var
        'default_user': None,  # Use NZX_USER env var
        'remote_path': '/wits/prices',
        'file_pattern': r'^final(\d{14})\.csv$',
        'description': 'WITS NZX Wholesale Prices'
    }
    
    # Metering Data Sources - Updated with ACTUAL discovered folder structures
    BLUECURRENT_RESIDENTIAL = {
        'prefix': 'BLUECURRENT_RES',
        'protocol': 'SFTP',
        'default_host': None,  # Use BLUECURRENT_RES_HOST env var
        'default_port': None,  # Use BLUECURRENT_RES_PORT env var
        'default_user': None,  # Use BLUECURRENT_RES_USER env var
        'remote_paths': {
            'drr': '/data/to_yesp/DRR',          # Daily Register Reads - FROM TABLE
            'hhr': '/data/to_yesp/HERM',         # Half-Hourly Reads in HERM - FROM TABLE
            'monthly': '/data/to_yesp/HERM'      # Monthly Register Reads in HERM - FROM TABLE
        },
        'remote_path': '/data/to_yesp/DRR',      # Default to DRR folder - FROM TABLE
        'file_pattern': r'^RM[A-Z]{4}YESP\d{14}IC\.C\d{2}\.csv$',
        'description': 'BlueCurrent Mass Market Metering'
    }
    
    BLUECURRENT_COMMERCIAL = {
        'prefix': 'BLUECURRENT_CI',
        'protocol': 'SFTP',
        'default_host': None,  # Use BLUECURRENT_CI_HOST env var
        'default_port': None,  # Use BLUECURRENT_CI_PORT env var
        'default_user': None,  # Use BLUECURRENT_CI_USER env var
        'remote_paths': {
            'daily_unvalidated': '/SFTP/C_I/Daily unvalidated',    # Daily unvalidated - FROM TABLE
            'monthly_validated': '/SFTP/C_I/Monthly validated',    # Monthly validated - FROM TABLE
            'drr': '/SFTP/C_I/Daily unvalidated',                  # Default to daily for DRR
            'monthly': '/SFTP/C_I/Monthly validated'               # Monthly data
        },
        'remote_path': '/SFTP/C_I/Daily unvalidated',  # Default to daily unvalidated - FROM TABLE
        'file_pattern': r'^ci_readings_\d{8}\.csv$',
        'description': 'BlueCurrent Commercial & Industrial'
    }
    
    INTELLIHUB = {
        'prefix': 'INTELLIHUB',
        'protocol': 'SFTP',
        'default_host': None,  # Use INTELLIHUB_HOST env var
        'default_port': None,  # Use INTELLIHUB_PORT env var
        'default_user': None,  # Use INTELLIHUB_USER env var
        'remote_paths': {
            'drr': '/RR',                        # Register Reads - ACTUAL PATH
            'hhr': '/HHR',                       # Half-Hourly Reads - ACTUAL PATH
            'events': '/Event'                   # Event data - ACTUAL PATH
        },
        'remote_path': '/RR',                    # Default to RR folder - ACTUAL PATH
        'file_pattern': r'^intellihub_\d{8}\.(csv|xml)$',
        'description': 'Intellihub Metering'
    }
    
    METRIX = {
        'prefix': 'MTRX',
        'protocol': 'SFTP',
        'default_host': None,  # Use MTRX_HOST env var
        'default_port': None,  # Use MTRX_PORT env var
        'default_user': None,  # Use MTRX_USER env var
        'remote_paths': {
            'drr': '/',    # Default to root, expecting env override
            'hhr': '/',                  # Default to root, expecting env override
            'monthly': '/'               # Default to root, expecting env override
        },
        'remote_path': '/',  # Default folder, expecting env override
        'file_pattern': r'^metrix_\d{8}\.(csv|xml)$',
        'description': 'Metrix Metering'
    }
    
    SMARTCO = {
        'prefix': 'SMARTCO_RES',
        'protocol': 'SFTP',
        'default_host': None,  # Use SMARTCO_RES_HOST env var
        'default_port': None,  # Use SMARTCO_RES_PORT env var
        'default_user': None,  # Use SMARTCO_RES_USER env var
        'remote_paths': {
            'drr': '/SFTP/DailyRegisterRead',    # Daily Register Reads - ACTUAL PATH
            'hhr': '/SFTP/HERM',                 # Half-Hourly in HERM folder - ACTUAL PATH
            'monthly': '/SFTP/HERM'              # Monthly in HERM folder - ACTUAL PATH
        },
        'remote_path': '/SFTP/DailyRegisterRead',  # Default to DRR - ACTUAL PATH
        'file_pattern': r'^RM[A-Z]{4}YESP\d{14}IC\.C\d{2}\.csv$',
        'description': 'SmartCo Metering'
    }
    
    # Registry Data Sources
    REGISTRY_SWITCHING = {
        'prefix': 'REGISTRY_SWITCH',
        'protocol': 'SFTP',
        'default_host': '',
        'default_port': 22,
        'default_user': '',
        'remote_path': '/registry/switching',
        'file_pattern': r'^switching_\d{8}\.csv$',
        'description': 'Registry Switching Files'
    }
    
    REGISTRY = {
        'prefix': 'REGISTRY',
        'protocol': 'SFTP',
        'default_host': '',
        'default_port': 22,
        'default_user': '',
        'remote_path': '/fromreg',
        'file_pattern': r'^.*\.(txt|zip)$',
        'description': 'Unified Registry SFTP (Information and Switching)'
    }
    
    @classmethod
    def get_config(cls, source_name: str) -> Dict:
        """Get configuration for a specific data source"""
        return getattr(cls, source_name, None)
    
    @classmethod
    def list_sources(cls) -> List[str]:
        """List all available data sources"""
        return [attr for attr in dir(cls) if not attr.startswith('_') and attr.isupper()]


def create_connection_manager(source_config: Dict) -> ConnectionManager:
    """
    Factory function to create a ConnectionManager with predefined source configuration
    
    :param source_config: Data source configuration from DataSourceConfig
    :return: Configured ConnectionManager instance
    """
    return ConnectionManager() 