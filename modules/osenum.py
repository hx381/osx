"""
OSEnum module for OSX Framework
Advanced enumeration for OutSystems applications
"""

import requests
import urllib3
from urllib.parse import urlparse, urljoin
import re
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.colors import Colors

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    import logging
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class OSEnum:
    """Advanced enumeration for OutSystems applications"""
    
    description = "Advanced enumeration for OutSystems applications"
    
    options = {
        'TIMEOUT': {
            'value': '30',
            'required': False,
            'description': 'Request timeout in seconds'
        },
        'USER_AGENT': {
            'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'required': False,
            'description': 'User agent string for requests'
        },
        'PROXY': {
            'value': '',
            'required': False,
            'description': 'Proxy URL (http://proxy:port)'
        },
        'WORKSPACE_MANAGER': {
            'value': None,
            'required': False,
            'description': 'Workspace manager instance for saving results'
        },
        'HEADLESS': {
            'value': 'true',
            'required': False,
            'description': 'Run browser in headless mode (true/false)'
        },
        'SCREENSHOTS': {
            'value': 'true',
            'required': False,
            'description': 'Take screenshots of screens (true/false)'
        },
        'THREADS': {
            'value': '5',
            'required': False,
            'description': 'Number of concurrent threads for screen testing'
        },
        'VERBOSE': {
            'value': 'false',
            'required': False,
            'description': 'Show detailed output (true/false)'
        },
        'SLEEP_TIME': {
            'value': '5',
            'required': False,
            'description': 'Time to wait for JavaScript execution (seconds)'
        }
    }
    
    def __init__(self, options):
        self.options = options
        self.target = options.get('TARGET', '')
        self.timeout = int(options.get('TIMEOUT', 30))
        self.user_agent = options.get('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.proxy = options.get('PROXY', '')
        self.workspace_manager = options.get('WORKSPACE_MANAGER')
        self.headless = options.get('HEADLESS', 'true').lower() == 'true'
        self.screenshots = options.get('SCREENSHOTS', 'true').lower() == 'true'
        self.threads = int(options.get('THREADS', 5))
        self.verbose = options.get('VERBOSE', 'false').lower() == 'true'
        self.sleep_time = int(options.get('SLEEP_TIME', 5))
        
        # Results storage
        self.results = {
            'target': self.target,
            'app_name': None,
            'screens': [],
            'enumeration_data': {}
        }
        self.results_lock = threading.Lock()
        
        if not self.verbose and SELENIUM_AVAILABLE:
            # Suppress Selenium and urllib3 logging
            logging.getLogger('selenium').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)
        
    def _get_requests_kwargs(self):
        """Helper to get common requests arguments including headers and proxies."""
        kwargs = {
            'headers': {"User-Agent": self.user_agent},
            'verify': False,
            'timeout': self.timeout,
            'allow_redirects': False  # Don't follow redirects to detect them
        }
        if self.proxy:
            kwargs['proxies'] = {
                'http': self.proxy,
                'https': self.proxy
            }
        return kwargs

    def run(self):
        """Execute the OSEnum module"""
        if not self.target:
            print("[-] TARGET not set")
            return
            
        print(f"[*] Target: {self.target}")
        if self.proxy and self.verbose:
            print(f"[*] Using proxy: {self.proxy}")
        if self.verbose:
            print(f"[*] Threads: {self.threads}")
            print(f"[*] Sleep time: {self.sleep_time}s")
            print(f"[*] Verbose: {self.verbose}")
        print()
        
        if not SELENIUM_AVAILABLE:
            print("[-] Selenium not available. Install with: pip install selenium")
            print("[*] Falling back to basic enumeration...")
        else:
            if self.verbose:
                print("[*] Selenium available. Will use headless browser for advanced enumeration.")

        
        # Extract app name from initial request
        app_name = self._extract_app_name()
        if app_name:
            print(f"[+] Application Name: {Colors.CYAN}{app_name}{Colors.RESET}")
            self.results['app_name'] = app_name
            

            screens = self._get_screens_list(app_name)

            
            if screens and SELENIUM_AVAILABLE:
                self._test_screens_with_browser(app_name, screens)
                self._show_recap()
            elif screens:
                print(f"[*] Found {len(screens)} screens but browser testing unavailable")
                if self.verbose:
                    for screen in screens:
                        print(f"[*] Screen found: {screen}")
            else:
                print("[*] No screens found or available for testing")
        else:
            print("[-] Could not extract application name")
            
        # Save results if requested
        if self.workspace_manager:
            self._save_to_workspace()
    
    def _extract_app_name(self):
        """Extract OutSystems application name from initial GET request"""
        try:
            if self.verbose:
                print("[*] Extracting application name...")
            
            kwargs = self._get_requests_kwargs()
            kwargs['allow_redirects'] = True
            response = requests.get(self.target, **kwargs)
            
            if response.status_code != 200:
                print(f"[-] Failed to get target page, status code: {response.status_code}")
                return None
            
            html_content = response.text
            
            app_def_pattern = r'src="[^"]*?([^/]+)\.appDefinition\.js[^"]*"'
            app_def_match = re.search(app_def_pattern, html_content, re.IGNORECASE)
            
            if app_def_match:
                app_name = app_def_match.group(1)
                return app_name
            
            index_pattern = r'src="[^"]*?([^/]+)\.index\.js[^"]*"'
            index_match = re.search(index_pattern, html_content, re.IGNORECASE)
            
            if index_match:
                app_name = index_match.group(1)
                return app_name
            
            print("[-] No application name patterns found in response")
            return None
            
        except Exception as e:
            print(f"[-] Error extracting app name: {e}")
            return None
    
    def _get_screens_list(self, app_name):
        """Get list of screens using the updated get_Screens script"""
        try:
            if self.verbose:
                print(f"\n[*] Getting screens list for: {Colors.CYAN}{app_name}{Colors.RESET}")
            
            osscan_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'osscan')
            if osscan_path not in sys.path:
                sys.path.insert(0, osscan_path)
            
            import get_Screens
            
            parsed_url = urlparse(self.target)
            environment = f"{parsed_url.scheme}://{parsed_url.netloc}"
            app_module_name = parsed_url.path.lstrip("/")
            module_info_url = f"{environment}/{app_module_name}/moduleservices/moduleinfo/"
            
            kwargs = self._get_requests_kwargs()
            kwargs['allow_redirects'] = True
            
            response = requests.get(module_info_url, **kwargs)
            if response.status_code == 200:
                module_data = response.json()
                screens = get_Screens.get_all_pages(module_data, environment)
                
                if screens and isinstance(screens, list):
                    return screens
                else:
                    return []
            else:
                print(f"[-] Failed to get module data: {response.status_code}")
                return []
            
        except Exception as e:
            print(f"[-] Error getting screens list: {e}")
            return []

    def _test_screens_with_browser(self, app_name, screens):
        """Test each screen with headless browser using threading"""
        if not screens:
            print("[*] No screens to test")
            return
            
        print(f"\n[*] Testing {len(screens)} screens with {self.threads} threads...")
        
        parsed_url = urlparse(self.target)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_screen = {
                executor.submit(self._test_single_screen_threaded, base_url, app_name, screen): screen 
                for screen in screens
            }
            
            for future in as_completed(future_to_screen):
                screen = future_to_screen[future]
                try:
                    future.result()
                except Exception as e:
                    if self.verbose:
                        print(f"[-] Error in thread for {screen}: {e}")
        
    def _test_single_screen_threaded(self, base_url, app_name, screen):
        """Test a single screen in a separate thread with its own browser instance"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--user-agent={self.user_agent}")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        if not self.verbose:
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
        
        driver = None
        try:
            service = None
            if not self.verbose:
                service = Service(log_path=os.devnull)
            
            driver = webdriver.Chrome(options=chrome_options, service=service)
            driver.set_page_load_timeout(self.timeout)
            driver.maximize_window()
            
            self._test_single_screen(driver, base_url, app_name, screen)
            
        except WebDriverException as e:
            if self.verbose:
                print(f"[-] Browser setup failed for {screen}: {e}")
        except Exception as e:
            if self.verbose:
                print(f"[-] Error during browser testing for {screen}: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def _test_single_screen(self, driver, base_url, app_name, screen):
        """Test a single screen for availability and redirects"""
        try:
            screen_url = f"{base_url}{screen}"
            if self.verbose:
                print(f"[*] Testing: {screen_url}")
            
            initial_url = screen_url
            
            driver.get(screen_url)
            
            try:
                WebDriverWait(driver, 3).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                import time
                time.sleep(self.sleep_time)
                
                current_url_after_wait = driver.current_url
                
            except TimeoutException:
                current_url_after_wait = driver.current_url
            
            current_url = driver.current_url
            current_path = urlparse(current_url).path
            initial_path = urlparse(initial_url).path
            
            with self.results_lock:
                if current_url != initial_url or current_path != initial_path:
                    if 'login' in current_path.lower() or 'signin' in current_path.lower():
                        if self.verbose:
                            print(f"[*] {Colors.BLUE}Redirected to Login: {current_path}{Colors.RESET}")
                        else:
                            print(f"[*] {Colors.BLUE}{screen} -> Login{Colors.RESET}")
                    
                        self.results['screens'].append({
                            'name': screen,
                            'status': 'redirected',
                            'redirect_to': current_path,
                            'original_url': initial_url,
                            'final_url': current_url
                        })
                else:
                    try:
                        page_source = driver.page_source.lower()
                        if ('login' in page_source and 'password' in page_source) or \
                           ('signin' in page_source and 'password' in page_source):
                            if self.verbose:
                                print(f"[*] {Colors.BLUE}Content redirected to Login (URL unchanged){Colors.RESET}")
                            else:
                                print(f"[*] {Colors.BLUE}{screen} -> Login (content){Colors.RESET}")
                            self.results['screens'].append({
                                'name': screen,
                                'status': 'content_redirected',
                                'redirect_to': 'Login',
                                'url': current_url
                            })
                        else:
                            if self.verbose:
                                print(f"[+] {Colors.GREEN}Screen available: {screen}{Colors.RESET}")
                            else:
                                print(f"[+] {Colors.GREEN}{screen}{Colors.RESET}")
                            self.results['screens'].append({
                                'name': screen,
                                'status': 'available',
                                'url': screen_url
                            })
                            
                            if self.screenshots:
                                self._take_screenshot(driver, screen, app_name)
                    except Exception as content_check_error:
                        if self.verbose:
                            print(f"[+] {Colors.GREEN}Screen available: {screen}{Colors.RESET}")
                        else:
                            print(f"[+] {Colors.GREEN}{screen}{Colors.RESET}")
                        self.results['screens'].append({
                            'name': screen,
                            'status': 'available',
                            'url': screen_url
                        })
            
        except TimeoutException:
            with self.results_lock:
                if self.verbose:
                    print(f"[-] {Colors.RED}Timeout loading: {screen}{Colors.RESET}")
                else:
                    print(f"[-] {Colors.RED}{screen} (timeout){Colors.RESET}")
                self.results['screens'].append({
                    'name': screen,
                    'status': 'timeout',
                    'url': screen_url
                })
        except Exception as e:
            with self.results_lock:
                if self.verbose:
                    print(f"[-] {Colors.RED}Error testing {screen}: {e}{Colors.RESET}")
                else:
                    print(f"[-] {Colors.RED}{screen} (error){Colors.RESET}")
                self.results['screens'].append({
                    'name': screen,
                    'status': 'error',
                    'error': str(e),
                    'url': screen_url
                })

    def _take_screenshot(self, driver, screen_name, app_name):
        """Take fullscreen screenshot of the current screen"""
        try:
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            
            safe_screen_name = re.sub(r'[^\w\-_.]', '_', screen_name)
            filename = f"{screenshots_dir}/{app_name}_{safe_screen_name}.png"
            
            driver.execute_script("window.scrollTo(0, 0);")
            
            total_width = driver.execute_script("return document.body.scrollWidth")
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            driver.set_window_size(total_width, total_height)
            
            driver.save_screenshot(filename)
            
            if self.verbose:
                print(f"[*] Screenshot saved: {filename}")
            
        except Exception as e:
            if self.verbose:
                print(f"[-] Error taking screenshot: {e}")

    def _save_to_workspace(self):
        """Save results to workspace"""
        try:
            result_file = self.workspace_manager.save_scan_results('osenum', self.results)
            print(f"\n[*] Results saved to workspace: {result_file}")
        except Exception as e:
            print(f"[-] Error saving to workspace: {e}")

    def _show_recap(self):
        """Show recap of enumeration results"""
        print(f"\n{Colors.CYAN}=== ENUMERATION RECAP ==={Colors.RESET}")
        
        available_screens = [s for s in self.results['screens'] if s['status'] == 'available']
        redirected_screens = [s for s in self.results['screens'] if s['status'] in ['redirected', 'content_redirected']]
        
        print(f"[+] Available Screens ({len(available_screens)}):")
        for screen in available_screens:
            print(f"    {Colors.GREEN}{screen['name']}{Colors.RESET}")
        
        if redirected_screens:
            unique_redirects = {}
            for screen in redirected_screens:
                redirect_to = screen.get('redirect_to', 'Unknown')
                if redirect_to not in unique_redirects:
                    unique_redirects[redirect_to] = []
                unique_redirects[redirect_to].append(screen['name'])
            
            print(f"\n[*] Unique Redirects ({len(unique_redirects)}):")
            for redirect_to, screens in unique_redirects.items():
                print(f"    {Colors.BLUE}{redirect_to}{Colors.RESET} ({len(screens)} screens)")
                if self.verbose:
                    for screen in screens:
                        print(f"      - {screen}")
        
        print(f"\n[*] Total screens tested: {len(self.results['screens'])}")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
