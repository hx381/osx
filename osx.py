#!/usr/bin/env python3
"""
OSX Framework - OutSystems Security Testing Toolkit
Modern CLI framework inspired by msfconsole
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.console import OSXConsole
from utils.colors import print_banner, Colors

def main():
    """Main entry point"""
    
    # Print banner
    print_banner()
    
    # Initialize console
    console = OSXConsole()
    
    # Start interactive shell
    try:
        console.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Goodbye!{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
