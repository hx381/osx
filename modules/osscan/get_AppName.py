import re
import requests
import urllib3
from colorama import Fore, Style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_app_name_from_response(environment, header, timeout=30):
    """
    Extract OutSystems application name from initial GET request response.
    Looks for patterns like *.appDefinition.js or *.index.js in the HTML response.
    
    Args:
        environment (str): Base URL of the OutSystems environment
        header (dict): HTTP headers for the request
        timeout (int): Request timeout in seconds
        
    Returns:
        str: Application name if found, None otherwise
    """
    try:
        # Send GET request to root path
        response = requests.get(environment, headers=header, verify=False, timeout=timeout)
        
        if response.status_code != 200:
            print(f"{Fore.RED}[!] Failed to get initial response: {response.status_code} - {response.reason}{Style.RESET_ALL}")
            return None
            
        html_content = response.text
        
        # Pattern 1: Look for *.appDefinition.js files
        app_definition_pattern = r'src="[^"]*scripts/([^/]+)\.appDefinition\.js[^"]*"'
        app_definition_matches = re.findall(app_definition_pattern, html_content, re.IGNORECASE)
        
        if app_definition_matches:
            app_name = app_definition_matches[0]
            print(f"{Fore.GREEN}[+] App name extracted from .appDefinition.js: {app_name}{Style.RESET_ALL}")
            return app_name
        
        # Pattern 2: Look for *.index.js files as fallback
        index_pattern = r'src="[^"]*scripts/([^/]+)\.index\.js[^"]*"'
        index_matches = re.findall(index_pattern, html_content, re.IGNORECASE)
        
        if index_matches:
            app_name = index_matches[0]
            print(f"{Fore.GREEN}[+] App name extracted from .index.js: {app_name}{Style.RESET_ALL}")
            return app_name
        
        # Pattern 3: Look for any module JS files that might contain app name
        module_pattern = r'src="[^"]*scripts/([^/\.]+)(?:\.[^/]*)?\.js[^"]*"'
        module_matches = re.findall(module_pattern, html_content, re.IGNORECASE)
        
        # Filter out common OutSystems framework files
        framework_files = ['OutSystemsReactWidgets', 'OutSystemsUI', 'OutSystemsMaps']
        app_candidates = [match for match in module_matches if match not in framework_files]
        
        if app_candidates:
            # Take the first non-framework JS file as potential app name
            app_name = app_candidates[0]
            print(f"{Fore.YELLOW}[?] Potential app name from JS files: {app_name}{Style.RESET_ALL}")
            return app_name
        
        print(f"{Fore.RED}[!] Could not extract app name from response{Style.RESET_ALL}")
        return None
        
    except Exception as e:
        print(f"{Fore.RED}[!] Error extracting app name: {e}{Style.RESET_ALL}")
        return None


def get_app_and_module_info(target_url, header, timeout=30):
    """
    Extract both application name and module name from OutSystems target.
    
    Args:
        target_url (str): Full target URL
        header (dict): HTTP headers
        timeout (int): Request timeout
        
    Returns:
        tuple: (app_name, module_name) or (None, None) if extraction fails
    """
    from urllib.parse import urlparse
    
    parsed_url = urlparse(target_url)
    environment = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    print(f"{Fore.CYAN}[*] Extracting app and module information...{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target: {target_url}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Environment: {environment}{Style.RESET_ALL}")
    
    # Extract app name from initial response
    app_name = extract_app_name_from_response(environment, header, timeout)
    
    
    if app_name:
        print(f"{Fore.GREEN}[+] Successfully extracted - App: {app_name}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[!] Failed to extract app information{Style.RESET_ALL}")
    
    return app_name
