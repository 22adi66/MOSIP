#!/usr/bin/env python3
"""
MOSIP OCR System Status Checker
Shows the current status of all MOSIP services
"""

import subprocess
import requests
import sys
from datetime import datetime
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check_process(command_pattern):
    """Check if a process is running"""
    try:
        result = subprocess.run(["pgrep", "-f", command_pattern], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return pids
        return []
    except:
        return []

def check_port(port):
    """Check if a port is in use"""
    try:
        result = subprocess.run(["lsof", "-ti", f":{port}"], 
                              capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False

def check_url(url, timeout=5):
    """Check if a URL is accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def get_log_info(log_file):
    """Get log file information"""
    log_path = Path(log_file)
    if log_path.exists():
        stat = log_path.stat()
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime)
        return {
            'exists': True,
            'size': size,
            'modified': modified,
            'size_mb': round(size / 1024 / 1024, 2)
        }
    return {'exists': False}

def print_service_status(name, is_running, details=None):
    """Print formatted service status"""
    status_color = Colors.OKGREEN if is_running else Colors.FAIL
    status_text = "🟢 RUNNING" if is_running else "🔴 STOPPED"
    
    print(f"{name:<20} {status_color}{status_text}{Colors.ENDC}")
    
    if details and is_running:
        for detail in details:
            print(f"{'':22} {detail}")

def main():
    """Main status checker"""
    print(f"""
{Colors.HEADER}{Colors.BOLD}📊 MOSIP OCR System Status{Colors.ENDC}
{Colors.HEADER}{'=' * 40}{Colors.ENDC}
{Colors.OKBLUE}Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}

""")
    
    # Check each service
    services = [
        {
            'name': 'Ngrok Tunnel',
            'process': 'ngrok http 8000',
            'port': 4040,
            'url': 'http://localhost:4040/api/tunnels',
            'log': 'logs/ngrok.log'
        },
        {
            'name': 'FastAPI Server',
            'process': 'uvicorn src.api.main:app',
            'port': 8000,
            'url': 'http://localhost:8000/health',
            'log': 'logs/api.log'
        },
        {
            'name': 'Streamlit Frontend',
            'process': 'streamlit run streamlit_app.py',
            'port': 8501,
            'url': 'http://localhost:8501',
            'log': 'logs/streamlit.log'
        }
    ]
    
    print(f"{Colors.BOLD}🔄 Service Status:{Colors.ENDC}")
    print("-" * 50)
    
    all_running = True
    
    for service in services:
        # Check if process is running
        pids = check_process(service['process'])
        is_running = len(pids) > 0
        
        if not is_running:
            all_running = False
        
        details = []
        
        if is_running:
            details.append(f"PID: {', '.join(pids)}")
            
            # Check port
            if check_port(service['port']):
                details.append(f"Port {service['port']}: ✅ Open")
            else:
                details.append(f"Port {service['port']}: ❌ Closed")
            
            # Check URL if service is API or has web interface
            if 'url' in service:
                if check_url(service['url']):
                    details.append(f"HTTP: ✅ Responding")
                else:
                    details.append(f"HTTP: ❌ Not responding")
        
        print_service_status(service['name'], is_running, details)
    
    # Check log files
    print(f"\n{Colors.BOLD}📄 Log Files:{Colors.ENDC}")
    print("-" * 50)
    
    log_dir = Path("logs")
    if log_dir.exists():
        for service in services:
            log_info = get_log_info(service['log'])
            log_name = Path(service['log']).name
            
            if log_info['exists']:
                print(f"{log_name:<15} ✅ {log_info['size_mb']} MB (updated: {log_info['modified'].strftime('%H:%M:%S')})")
            else:
                print(f"{log_name:<15} ❌ Not found")
    else:
        print("Log directory not found")
    
    # Show access URLs
    print(f"\n{Colors.BOLD}🌐 Access URLs:{Colors.ENDC}")
    print("-" * 50)
    
    urls = [
        ("API Documentation", "http://localhost:8000/docs"),
        ("API Health Check", "http://localhost:8000/health"),
        ("Web Interface", "http://localhost:8501"),
        ("Ngrok Inspector", "http://localhost:4040")
    ]
    
    for name, url in urls:
        accessible = check_url(url, timeout=3)
        status = "✅ Available" if accessible else "❌ Unavailable"
        print(f"{name:<20} {url} - {status}")
    
    # Get Ngrok public URL
    print(f"\n{Colors.BOLD}🚀 Public Access:{Colors.ENDC}")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        public_url = tunnel.get('public_url')
                        print(f"Public API URL:      {public_url}")
                        print(f"API Docs:           {public_url}/docs")
                        break
            else:
                print("No active tunnels found")
        else:
            print("Cannot connect to Ngrok API")
    except:
        print("Ngrok not running or not accessible")
    
    # Overall status
    print(f"\n{Colors.BOLD}📈 Overall Status:{Colors.ENDC}")
    print("-" * 50)
    
    if all_running:
        print(f"{Colors.OKGREEN}✅ All services are running normally{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.WARNING}⚠️  Some services are not running{Colors.ENDC}")
        print(f"{Colors.OKBLUE}💡 Run 'python start.py' to start all services{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())