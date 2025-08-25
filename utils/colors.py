"""
OSX Framework - Minimal colors like MSF
"""

class Colors:
    """Minimal color palette - only when needed"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Only essential colors
    RED = '\033[31m'      # Errors only
    GREEN = '\033[32m'    # Success/Set values only  
    YELLOW = '\033[33m'   # Warnings only
    BLUE = '\033[34m'     # Module names only
    WHITE = '\033[37m'    # Normal text
    DIM = '\033[2m'       # Secondary info
    CYAN = '\033[36m'     # Info messages only

def print_banner():
    """Simple banner like MSF"""
    banner = """
       ____  ______  __
      / __ \\/ ___/ |/ /
     / / / /\\__ \\|   / 
    / /_/ /___/ /   |  
    \\____//____/_/|_|  
                       
    OutSystems Penetration Testing Toolkit
    
    Credits:
      * OS-Scan by LUCAS 5O4R3S
      * By HX 
    """
    
    print(banner)
    print("=" * 50)
    
