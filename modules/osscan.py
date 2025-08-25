"""
OS-Scan module for OSX Framework
Comprehensive OutSystems application reconnaissance and vulnerability scanning
Based on the original osscan.py script by LUCAS 5O4R3S
"""

import requests
import urllib3
from urllib.parse import urlparse
import time
import json
import sys
import os
from pathlib import Path

# Add the osscan subfolder to path to import original files
osscan_dir = Path(__file__).parent / 'osscan'
sys.path.insert(0, str(osscan_dir))

# Import all original osscan modules from the osscan subfolder
try:
    import get_ClientVariables
    import get_EndScope
    import get_LoginSample
    import get_MobileApp
    import get_ModulesReferences
    import get_Resources
    import get_Roles
    import get_SAPInformations
    import get_Screens
    import commons
    import get_AppName  # New import for app name extraction
    import get_AppDefinitions
    import get_AppFeedback
except ImportError as e:
    print(f"[-] Error importing osscan modules: {e}")
    print(f"[-] Make sure all osscan files are in: {osscan_dir}")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OSScanner:
    """Comprehensive OutSystems application scanner"""
    
    description = "Comprehensive OutSystems reconnaissance and vulnerability scanner"
    
    options = {
        'DEEP_SCAN': {
            'value': 'true',
            'required': False,
            'description': 'Perform deep scanning of all modules (true/false)'
        },
        'SAVE_RESULTS': {
            'value': 'true',
            'required': False,
            'description': 'Save results to workspace (true/false)'
        }
    }
    
    def __init__(self, options):
        self.options = options
        self.target = options.get('TARGET', '')
        self.deep_scan = options.get('DEEP_SCAN', 'true').lower() == 'true'
        self.save_results = options.get('SAVE_RESULTS', 'true').lower() == 'true'
        self.timeout = int(options.get('TIMEOUT', 30))
        self.user_agent = options.get('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.workspace_manager = options.get('WORKSPACE_MANAGER')
        
        # Results storage
        self.scan_results = {
            'target_info': {},
            'vulnerabilities': [],
            'findings': [],
            'scan_timestamp': commons.get_current_datetime() if 'commons' in globals() else time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Initialize URL components
        self.environment = ""
        self.application = ""
        self.module_services = "moduleservices/"
        self.module_services_info = "moduleinfo/"
        self.module_informations_url = ""
        
    def run(self):
        """Execute the OS-Scan module"""
        if not self.target:
            print("[-] TARGET not set")
            return
            
        # Initialize URLs with dynamic app name extraction
        if not self._initialize_urls():
            return
            
        print(f"[*] Target: {self.target}")
        print(f"[*] Environment: {self.environment}")
        print(f"[*] Application: {self.application}")
        
        
        # Test initial connection
        if not self._test_connection():
            return
            
        # Get module information
        module_data = self._get_module_info()
        if not module_data:
            return
            
        # Run all original scanning functions exactly as developed
        self._run_original_scans(module_data)
        
        # Save results if requested
        if self.save_results and self.workspace_manager:
            self._save_to_workspace()
            
        # Show scan completion
        get_EndScope.scan_completed()
    
    def _initialize_urls(self):
        """Initialize URL components with dynamic app name extraction"""
        try:
            import get_AppName
        except ImportError:
            print("[-] Error: get_AppName module not found")
            return False
        
        self.url_full = self.target.rstrip('/')
        
        parsed_url = urlparse(self.url_full)
        self.environment = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        headers = {"User-Agent": self.user_agent}
        
        try:
            app_name = get_AppName.get_app_and_module_info(self.url_full, headers, self.timeout)
            print(f"[DEBUG] get_app_and_module_info returned: {app_name}")
            
            if isinstance(app_name, str) and app_name:
                self.application = app_name
            else:
                print(f"[-] Unexpected return format from get_app_and_module_info: {app_name}")
                app_name = None
                
        except Exception as e:
            print(f"[-] Error calling get_app_and_module_info: {e}")
            app_name = None
        
        self.application = app_name if app_name else "UnknownApp"
        
        app_module_name = parsed_url.path.lstrip("/")
        self.module_informations_url = f"{self.environment}/{app_module_name}/{self.module_services}{self.module_services_info}"
        
        self.scan_results['target_info'] = {
            'full_url': self.url_full,
            'environment': self.environment,
            'application': self.application,
            'module_info_url': self.module_informations_url
        }
        
        return True
    
    def _test_connection(self):
        """Test initial connection to target"""
        print(f"[*] {commons.get_current_datetime()} Testing connection...")
        
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(self.module_informations_url, headers=headers, 
                                  verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                print(f"[+] Application '{self.application}' is online")
                return True
            elif response.status_code == 403:
                print("[-] Access blocked, but application may still be accessible")
                print(f"[*] Try accessing: {self.module_informations_url}")
                return False
            else:
                print(f"[-] Connection failed: {response.status_code} - {response.reason}")
                return False
                
        except Exception as e:
            print(f"[-] Connection error: {e}")
            return False
    
    def _get_module_info(self):
        """Get module information"""
        print(f"[*] {commons.get_current_datetime()} Retrieving application information...")
        
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(self.module_informations_url, headers=headers, 
                                  verify=False, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                self.scan_results['app_data'] = data
                return data
            else:
                print(f"[-] Failed to get application info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[-] Error getting application info: {e}")
            return None
    
    def _run_original_scans(self, module_data):
        """Run all original scanning functions exactly as developed"""
        header = {"User-Agent": self.user_agent}
        
        print(f"\n[*] {commons.get_current_datetime()} Getting application definitions...")
        try:
            get_AppDefinitions.get_app_definitions(self.environment, self.application, header)
        except Exception as e:
            print(f"[-] Error getting app definitions: {e}")
        
        print(f"\n[*] {commons.get_current_datetime()} Checking app feedback vulnerabilities...")
        try:
            get_AppFeedback.get_EctAppFeedback(self.environment, self.application, header)
        except Exception as e:
            print(f"[-] Error checking app feedback: {e}")
        
        print(f"\n[*] {commons.get_current_datetime()} Running all exploit checks...")
        
        # CKEditor exploits
        try:
            from exploits.check_CKEditor import call_CKEditor_exploits
            call_CKEditor_exploits(self.environment, self.application, header, "CKEditor")
        except Exception as e:
            print(f"[-] Error running CKEditor exploits: {e}")
        
        # FroalaEditor exploits
        try:
            from exploits.check_FroalaEditor import call_FroalaEditor_exploits
            call_FroalaEditor_exploits(self.environment, self.application, header, "FroalaEditor")
        except Exception as e:
            print(f"[-] Error running FroalaEditor exploits: {e}")
        
        # PDFTron exploits
        try:
            from exploits.check_PDFTron import call_PDFTron_exploits
            call_PDFTron_exploits(self.environment, self.application, header, "PDFTron")
        except Exception as e:
            print(f"[-] Error running PDFTron exploits: {e}")
        
        # UltimatePDF exploits
        try:
            from exploits.check_UltimatePDF import call_UltimatePDF_exploits
            call_UltimatePDF_exploits(self.environment, self.application, header, "UltimatePDF")
        except Exception as e:
            print(f"[-] Error running UltimatePDF exploits: {e}")
        
        # Client Variables - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking client variables...")
        try:
            get_ClientVariables.get_all_clientvaribles(self.environment, self.application, header)
        except Exception as e:
            print(f"[-] Error in client variables: {e}")

        # Module References - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking module references...")
        try:
            get_ModulesReferences.get_module_references(self.environment, self.application, header)
        except Exception as e:
            print(f"[-] Error in module references: {e}")
        
        # Resources - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking public resources...")
        try:
            get_Resources.get_all_resources(module_data, self.environment)
        except Exception as e:
            print(f"[-] Error in resources: {e}")
        
        # Screens - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking available screens...")
        try:
            get_Screens.get_all_pages(module_data, self.environment)
        except Exception as e:
            print(f"[-] Error in screens: {e}")
        
        # Roles - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking application roles...")
        try:
            get_Roles.get_all_roles(self.environment, self.application, header)
        except Exception as e:
            print(f"[-] Error in roles: {e}")
        
        # Mobile Apps - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking mobile applications...")
        try:
            get_MobileApp.get_mobile_apps(self.environment, header)
        except Exception as e:
            print(f"[-] Error in mobile apps: {e}")
        
        # Login Samples - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking sample login screens...")
        try:
            get_LoginSample.get_LoginScreens(self.environment, header)
        except Exception as e:
            print(f"[-] Error in login samples: {e}")
        
        # SAP Information - exactly like original
        print(f"\n[*] {commons.get_current_datetime()} Checking SAP information...")
        try:
            get_SAPInformations.get_SapInformations(self.environment, header)
        except Exception as e:
            print(f"[-] Error in SAP info: {e}")

    
    def _save_to_workspace(self):
        """Save results to workspace"""
        try:
            self.scan_results['completed'] = commons.get_current_datetime()
            result_file = self.workspace_manager.save_scan_results('osscan', self.scan_results)
            print(f"\n[+] Results saved to workspace: {result_file}")
        except Exception as e:
            print(f"[-] Error saving to workspace: {e}")
