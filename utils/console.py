"""
OSX Framework Console - MSF-style interface with proper colors, global vars, and workspace support
"""

import os
import sys
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter

from .colors import Colors
from .workspace import WorkspaceManager

class OSXConsole:
    """MSF-style console interface with workspace support"""
    
    def __init__(self):
        self.current_module = None
        self.module_options = {}
        self.workspace_manager = WorkspaceManager()
        self.global_options = {
            'TARGET': {'value': '', 'required': True, 'description': 'Target OutSystems application URL'},
            'THREADS': {'value': '10', 'required': False, 'description': 'Number of threads'},
            'TIMEOUT': {'value': '30', 'required': False, 'description': 'Request timeout (seconds)'},
            'PROXY': {'value': '', 'required': False, 'description': 'HTTP proxy (e.g., http://127.0.0.1:8080)'},
            'USER_AGENT': {'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'required': False, 'description': 'User agent string'}
        }
        self.available_modules = self._load_modules()
        self.history = InMemoryHistory()
        
    def _load_modules(self) -> Dict[str, Any]:
        """Load all available modules"""
        modules = {}
        modules_dir = Path(__file__).parent.parent / 'modules'
        
        if not modules_dir.exists():
            print("[-] Modules directory not found")
            return modules
            
        for file_path in modules_dir.glob('*.py'):
            if file_path.name.startswith('__'):
                continue
                
            module_name = file_path.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None:
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        hasattr(obj, 'run') and 
                        hasattr(obj, 'description') and
                        hasattr(obj, 'options') and
                        not name.startswith('_')):
                        modules[module_name] = {
                            'class': obj,
                            'path': str(file_path),
                            'name': module_name,
                            'description': getattr(obj, 'description', 'No description')
                        }
                        break
                        
            except Exception as e:
                print(f"[-] Error loading {module_name}: {e}")
                
        return modules
    
    def run(self):
        """Main interactive loop"""
        print(f"[*] {len(self.available_modules)} modules loaded")
        
        
        commands = ['help', 'show', 'use', 'options', 'set', 'unset', 'run', 'back', 'workspace', 'exit']
        completer = WordCompleter(commands + list(self.available_modules.keys()))
        
        while True:
            try:
                if self.current_module:
                    prompt_text = f"osx {self.current_module} > "
                else:
                    prompt_text = "osx > "
                
                command = prompt(
                    prompt_text,
                    history=self.history,
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=completer
                ).strip()
                
                if not command:
                    continue
                    
                self._handle_command(command)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
    
    def _handle_command(self, command: str):
        """Parse and handle commands"""
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == 'help':
            self._show_help()
        elif cmd == 'show':
            self._handle_show(args)
        elif cmd == 'use':
            self._handle_use(args)
        elif cmd == 'options':
            self._show_options()
        elif cmd == 'set':
            self._handle_set(args)
        elif cmd == 'unset':
            self._handle_unset(args)
        elif cmd == 'run':
            self._handle_run()
        elif cmd == 'back':
            self._handle_back()
        elif cmd == 'workspace':
            self._handle_workspace(args)
        elif cmd == 'exit':
            print("Goodbye!")
            sys.exit(0)
        else:
            print(f"Unknown command: {cmd}")
    
    def _show_help(self):
        """Show help information - MSF style"""
        
        print("Core Commands")
        print("=============")
        
        print("    Command       Description")
        print("    -------       -----------")
        print("    help          Help menu")
        print("    show          Show modules, options, or info")
        print("    use           Select a module by name or number")
        print("    options       Show options for current module")
        print("    set           Set a variable to a value")
        print("    unset         Unset one or more variables")
        print("    run           Launch the current module")
        print("    back          Move back from the current context")
        print("    workspace     Show current workspace info")
        print("    exit          Exit the console")
        
    
    def _handle_show(self, args: List[str]):
        """Handle show command"""
        if not args:
            args = ['modules']
            
        if args[0] == 'modules':
            self._show_modules()
        elif args[0] == 'options':
            self._show_options()
        else:
            print(f"Unknown show option: {args[0]}")
    
    def _show_modules(self):
        """Show available modules - MSF style with numbers"""
        if not self.available_modules:
            print("No modules found")
            return
            
        
        print("OutSystems Modules")
        print("==================")
        
        print("   #   Name                Description")
        print("   -   ----                -----------")
        
        for i, (name, module_info) in enumerate(self.available_modules.items(), 1):
            description = module_info.get('description', 'No description')
            print(f"   {i:<3} {name:<18} {description}")
        
        
    
    def _show_options(self):
        """Show current options - clean table format"""
        
        print("Module options:")
        
        
        # Calculate column widths
        all_options = {**self.global_options, **self.module_options}
        if not all_options:
            print("No options available")
            return
            
        name_width = max(len(name) for name in all_options.keys())
        name_width = max(name_width, 4)  # minimum width for "Name"
        
        value_width = 20
        for option in all_options.values():
            if option['value']:
                value_width = max(value_width, len(str(option['value'])))
        value_width = min(value_width, 40)  # max width
        
        # Header
        print(f"   {'Name':<{name_width}} {'Current Setting':<{value_width}} {'Required':<8} Description")
        print(f"   {'-' * name_width} {'-' * value_width} {'-' * 8} -----------")
        
        # Global options first
        for name, option in self.global_options.items():
            value = option['value'] if option['value'] else ""
            if len(value) > value_width:
                value = value[:value_width-3] + "..."
            required = "yes" if option['required'] else "no"
            desc = option['description']
            
            # Color the value if it's set
            if option['value']:
                value_colored = f"{Colors.GREEN}{value}{Colors.RESET}"
            else:
                value_colored = value
                
            print(f"   {name:<{name_width}} {value_colored:<{value_width + (len(value_colored) - len(value))}} {required:<8} {desc}")
        
        # Module options
        for name, option in self.module_options.items():
            value = option['value'] if option['value'] else ""
            if len(value) > value_width:
                value = value[:value_width-3] + "..."
            required = "yes" if option['required'] else "no"
            desc = option['description']
            
            # Color the value if it's set
            if option['value']:
                value_colored = f"{Colors.GREEN}{value}{Colors.RESET}"
            else:
                value_colored = value
                
            print(f"   {name:<{name_width}} {value_colored:<{value_width + (len(value_colored) - len(value))}} {required:<8} {desc}")
        
        
    
    def _handle_use(self, args: List[str]):
        """Select a module by name or number"""
        if not args:
            print("Usage: use <module_name|module_number>")
            return
            
        module_identifier = args[0]
        module_name = None
        
        # Check if it's a number
        try:
            module_num = int(module_identifier)
            module_list = list(self.available_modules.keys())
            if 1 <= module_num <= len(module_list):
                module_name = module_list[module_num - 1]
            else:
                print(f"Invalid module number: {module_num}")
                return
        except ValueError:
            # It's a name
            if module_identifier in self.available_modules:
                module_name = module_identifier
            else:
                print(f"Invalid module: {module_identifier}")
                return
        
        self.current_module = module_name
        
        try:
            module_class = self.available_modules[module_name]['class']
            self.module_options = getattr(module_class, 'options', {})
            
        except Exception as e:
            print(f"Error loading module: {e}")
    
    def _handle_set(self, args: List[str]):
        """Set option value - works globally or in module context"""
        if len(args) < 2:
            print("Usage: set <option> <value>")
            return
            
        option_name = args[0].upper()
        option_value = ' '.join(args[1:])
        
        # Check global options first
        if option_name in self.global_options:
            self.global_options[option_name]['value'] = option_value
            print(f"{option_name} => {option_value}")
            
            # Create workspace when TARGET is set
            if option_name == 'TARGET':
                workspace_path = self.workspace_manager.create_workspace(option_value)
                print(f"[*] Workspace created: {workspace_path}")
                self.workspace_manager.log_activity(f"Target set to: {option_value}")
            return
            
        # Check module options if module is selected
        if option_name in self.module_options:
            self.module_options[option_name]['value'] = option_value
            print(f"{option_name} => {option_value}")
            return
            
        print(f"Unknown option: {option_name}")
    
    def _handle_unset(self, args: List[str]):
        """Clear option value"""
        if not args:
            print("Usage: unset <option>")
            return
            
        option_name = args[0].upper()
        
        if option_name in self.global_options:
            self.global_options[option_name]['value'] = ''
            print(f"Unsetting {option_name}...")
            return
            
        if option_name in self.module_options:
            self.module_options[option_name]['value'] = ''
            print(f"Unsetting {option_name}...")
            return
            
        print(f"Unknown option: {option_name}")
    
    def _handle_run(self):
        """Execute current module"""
        if not self.current_module:
            print("No module selected")
            return
            
        # Check required options
        missing = []
        
        for name, option in self.global_options.items():
            if option['required'] and not option['value']:
                missing.append(name)
                
        for name, option in self.module_options.items():
            if option['required'] and not option['value']:
                missing.append(name)
                
        if missing:
            print(f"[-] The following options are required: {', '.join(missing)}")
            return
            
        # Execute module
        try:
            module_class = self.available_modules[self.current_module]['class']
            
            all_options = {}
            for name, option in self.global_options.items():
                all_options[name] = option['value']
            for name, option in self.module_options.items():
                all_options[name] = option['value']
                
            # Add workspace manager to options
            all_options['WORKSPACE_MANAGER'] = self.workspace_manager
                
            module_instance = module_class(all_options)
            
            print(f"[*] Running module: {self.current_module}")
            self.workspace_manager.log_activity(f"Started module: {self.current_module}")
            
            
            module_instance.run()
            
            
            print(f"[+] Module execution completed")
            self.workspace_manager.log_activity(f"Completed module: {self.current_module}")
            
        except Exception as e:
            print(f"[-] Execution failed: {e}")
            self.workspace_manager.log_activity(f"Module failed: {self.current_module} - {e}")
    
    def _handle_back(self):
        """Deselect current module"""
        if self.current_module:
            self.current_module = None
            self.module_options = {}
        else:
            print("No module selected")
    
    def _handle_workspace(self, args: List[str]):
        """Show workspace information"""
        workspace_path = self.workspace_manager.get_workspace_path()
        
        if not workspace_path:
            print("No workspace active")
            return
            
        print(f"Current workspace: {workspace_path}")
        
        # Show workspace contents
        scans_dir = workspace_path / "scans"
        if scans_dir.exists():
            scan_files = list(scans_dir.glob("*.json"))
            print(f"Scan results: {len(scan_files)} files")
            
        logs_dir = workspace_path / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            print(f"Log files: {len(log_files)} files")
