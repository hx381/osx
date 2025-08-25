from colorama import Fore, Style
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_mobile_apps(environment,header):

    # Sending a GET request to the URL
    url = environment+'/NativeAppBuilder/rest/NativeApps/GetNativeApps'
    response = requests.get(url, headers=header, verify=False)

    # Checking the response code
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type")
        mime_type, _ = content_type.split(';')
        if mime_type == "application/json":
            data = json.loads(response.text)
            if data == []:
                print(f"| {Fore.WHITE}[404] {Style.DIM}No mobile applications found in the scanned environment.{Style.RESET_ALL}")
            else:
                print(f"| {Fore.WHITE}[200] {Style.DIM}{response.text}{Style.RESET_ALL}")
    else:
        # Error in request
        print(f"{Fore.RED}{Style.DIM}get_mobileapp.py - Erro: {response.status_code} - {response.reason}{Style.RESET_ALL}")
