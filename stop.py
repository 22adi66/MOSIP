#!/usr/bin/env python3
"""
MOSIP OCR System Stop Script
Stops all running MOSIP services
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def find_processes():
    """Find all MOSIP-related processes"""
    processes = []
    
    # Commands to look for
    commands = [
        "ngrok http 8000",
        "uvicorn src.api.main:app",
        "streamlit run streamlit_app.py"
    ]
    
    try:
        # Get all processes
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            for cmd in commands:
                if cmd in line and 'python' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        processes.append({
                            'pid': pid,
                            'command': cmd,
                            'line': line
                        })
                        break
    
    except Exception as e:
        print(f"{Colors.FAIL}Error finding processes: {e}{Colors.ENDC}")
    
    return processes

def stop_process(pid, name):
    """Stop a process by PID"""
    try:
        print(f"🛑 Stopping {name} (PID: {pid})")
        os.kill(int(pid), signal.SIGTERM)
        return True
    except ProcessLookupError:
        print(f"  ⚠️  Process {pid} already stopped")
        return True
    except Exception as e:
        print(f"  {Colors.FAIL}❌ Error stopping {pid}: {e}{Colors.ENDC}")
        return False

def force_kill_process(pid, name):
    """Force kill a process"""
    try:
        print(f"💀 Force killing {name} (PID: {pid})")
        os.kill(int(pid), signal.SIGKILL)
        return True
    except ProcessLookupError:
        return True
    except Exception as e:
        print(f"  {Colors.FAIL}❌ Error force killing {pid}: {e}{Colors.ENDC}")
        return False

def stop_port_processes():
    """Stop processes using specific ports"""
    ports = [8000, 8501, 4040]  # API, Streamlit, Ngrok web interface
    
    for port in ports:
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"🛑 Stopping process on port {port} (PID: {pid})")
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                        except:
                            pass
        except FileNotFoundError:
            # lsof not available, skip
            pass
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Could not check port {port}: {e}{Colors.ENDC}")

def main():
    """Main entry point"""
    print(f"""
{Colors.BOLD}🛑 MOSIP OCR System - Stop All Services{Colors.ENDC}
{'=' * 45}
""")
    
    # Find and stop MOSIP processes
    processes = find_processes()
    
    if not processes:
        print(f"{Colors.OKGREEN}✅ No MOSIP services found running{Colors.ENDC}")
    else:
        print(f"Found {len(processes)} MOSIP processes to stop:")
        
        for proc in processes:
            stop_process(proc['pid'], proc['command'])
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Check if any are still running and force kill
        remaining = find_processes()
        if remaining:
            print(f"\n{Colors.WARNING}Force killing {len(remaining)} remaining processes:{Colors.ENDC}")
            for proc in remaining:
                force_kill_process(proc['pid'], proc['command'])
    
    # Also stop any processes using our ports
    print(f"\n🔍 Checking for processes on MOSIP ports...")
    stop_port_processes()
    
    # Clean up log files if they exist
    log_dir = Path("logs")
    if log_dir.exists():
        print(f"\n📄 Log files available in: {log_dir.absolute()}")
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print("  Recent logs:")
            for log_file in sorted(log_files):
                size = log_file.stat().st_size
                print(f"    {log_file.name} ({size} bytes)")
    
    print(f"\n{Colors.OKGREEN}✅ MOSIP OCR system stopped{Colors.ENDC}")

if __name__ == "__main__":
    main()