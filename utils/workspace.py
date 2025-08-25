"""
OSX Framework - Workspace Management
Creates target-specific folders for persistent work
"""

import os
import json
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

class WorkspaceManager:
    """Manages target-specific workspaces"""
    
    def __init__(self, base_dir="workspaces"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        print(f"[+] Workspaces base directory: {self.base_dir.resolve()}")
        self.current_workspace = None
        
    def create_workspace(self, target_url):
        """Create workspace folder from target URL"""
        # Parse URL and create safe folder name
        parsed = urlparse(target_url)
        
        # Create folder name: protocol.domain.path
        folder_name = parsed.scheme or "http"
        folder_name += "." + (parsed.netloc or "localhost")
        
        if parsed.path and parsed.path != "/":
            # Replace slashes and special chars
            path_part = parsed.path.strip("/").replace("/", ".")
            path_part = "".join(c if c.isalnum() or c in ".-_" else "_" for c in path_part)
            folder_name += "." + path_part
            
        folder_name += ".results"
        
        # Create workspace directory
        workspace_path = self.base_dir / folder_name
        workspace_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (workspace_path / "scans").mkdir(exist_ok=True)
        (workspace_path / "logs").mkdir(exist_ok=True)
        (workspace_path / "evidence").mkdir(exist_ok=True)
        
        self.current_workspace = workspace_path
        
        # Create workspace info file
        info = {
            "target_url": target_url,
            "created": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "scans_performed": []
        }
        
        info_file = workspace_path / "workspace_info.json"
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
            
        return workspace_path
    
    def get_workspace_path(self):
        """Get current workspace path"""
        return self.current_workspace
    
    def save_scan_results(self, module_name, results):
        """Save scan results to workspace"""
        if not self.current_workspace:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{module_name}_{timestamp}.json"
        
        scan_file = self.current_workspace / "scans" / filename
        
        with open(scan_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        # Update workspace info
        info_file = self.current_workspace / "workspace_info.json"
        if info_file.exists():
            with open(info_file, 'r') as f:
                info = json.load(f)
                
            info["last_accessed"] = datetime.now().isoformat()
            info["scans_performed"].append({
                "module": module_name,
                "timestamp": timestamp,
                "file": filename
            })
            
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
                
        return scan_file
    
    def log_activity(self, message):
        """Log activity to workspace"""
        if not self.current_workspace:
            return
            
        log_file = self.current_workspace / "logs" / "activity.log"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
