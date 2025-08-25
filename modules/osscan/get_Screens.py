from colorama import Fore, Style
import commons

# Open wordlist file
with open("modules/osscan/wordlist/ScreenNames.txt", "r") as file_screen_wordlist:
    # read content of file
    wordlist_screen_names = file_screen_wordlist.readlines()

# Close file
file_screen_wordlist.close()

# Remove spaces between words
wordlist_screen_names = [word.strip() for word in wordlist_screen_names]

def check_screenName(screen_name):
    for word in wordlist_screen_names:
       if word.lower() in screen_name.lower():
           return True
    return False

def get_all_pages(data, environment_url):
    potential_screen_found = False
    found_screen_names = []

    url_mappings = data["manifest"]["urlMappings"]
    for key in url_mappings.keys():
        if "moduleservices" not in key.lower():
            if check_screenName(key.lower()):
                print(f"| {Fore.WHITE}[200]{Style.RESET_ALL} {Fore.YELLOW}[WARNING] {environment_url}{key}{Style.RESET_ALL}")
                found_screen_names.append(key)
                if not potential_screen_found:
                    potential_screen_found = True
            else:
                print(f"| {Fore.WHITE}[200] {Style.DIM}{environment_url}{key}{Style.RESET_ALL}")
                found_screen_names.append(key)
    if potential_screen_found:
        print(f"{Fore.RED}[i] {commons.get_current_datetime()} Potentially vulnerable test screens were found in{Style.RESET_ALL} {Fore.YELLOW}yellow{Style.RESET_ALL} {Fore.RED}above.{Style.RESET_ALL}")
        print(f"{Fore.RED}[i] {commons.get_current_datetime()} Soon you will be able to use other commands to perform a full page scan.{Style.RESET_ALL}")

    return found_screen_names
