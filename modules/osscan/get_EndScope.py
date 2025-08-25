from colorama import Fore, Style
import commons

def scan_completed():
    print(f"\n")
    print(f"[i] {commons.get_current_datetime()} Scan finished!")
    print(f"\n")
    print(f"{Fore.YELLOW}Warning: {Style.RESET_ALL}This is a tool for security professionals or OutSystems developers who want to maintain and create safer applications. Improper use of this tool can bring severe consequences.")
    print(f"If you would like to contribute to the evolution of this tool, please contact me at https://soarescorp.com/.")
