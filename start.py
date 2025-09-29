#!/usr/bin/env python3
"""
MOSIP OCR System Startup Script
Starts all required services: Ngrok, FastAPI (Uvicorn), and Streamlit
Each service runs with separate logging for easy debugging
"""

import os
import sys
import time
import signal
import subprocess
import threading
from datetime import datetime
from pathlib import Path

class Colors:
    """ANSI color codes for console output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ServiceManager:
    """Manages multiple services with separate logging"""
    
    def __init__(self):
        self.services = {}
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.running = False
        
        # Service configurations
        self.config = {
            "ngrok": {
                "command": ["ngrok", "http", "8000"],
                "cwd": ".",
                "log_file": "logs/ngrok.log",
                "name": "Ngrok Tunnel",
                "port": None,
                "startup_delay": 2
            },
            "api": {
                "command": ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"],
                "cwd": ".",
                "log_file": "logs/api.log",
                "name": "FastAPI Server",
                "port": 8000,
                "startup_delay": 3
            },
            "streamlit": {
                "command": ["streamlit", "run", "streamlit_app.py", "--server.port", "8501"],
                "cwd": ".",
                "log_file": "logs/streamlit.log",
                "name": "Streamlit Frontend",
                "port": 8501,
                "startup_delay": 5
            }
        }
    
    def print_banner(self):
        """Print startup banner"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                 MOSIP OCR SYSTEM STARTUP                     ║
║                   Text Extraction & Verification             ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}

{Colors.OKCYAN}Starting services at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}
"""
        print(banner)
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print(f"{Colors.OKBLUE}🔍 Checking dependencies...{Colors.ENDC}")
        
        dependencies = [
            ("python", "Python interpreter"),
            ("ngrok", "Ngrok tunnel service"),
            ("uvicorn", "FastAPI server"),
            ("streamlit", "Streamlit framework")
        ]
        
        missing = []
        for cmd, desc in dependencies:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    print(f"  ✅ {desc}")
                else:
                    missing.append((cmd, desc))
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing.append((cmd, desc))
        
        if missing:
            print(f"\n{Colors.FAIL}❌ Missing dependencies:{Colors.ENDC}")
            for cmd, desc in missing:
                print(f"  - {desc} ({cmd})")
            print(f"\n{Colors.WARNING}Please install missing dependencies and try again.{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✅ All dependencies found!{Colors.ENDC}\n")
        return True
    
    def activate_venv(self):
        """Activate virtual environment if it exists"""
        venv_path = Path("venv")
        if venv_path.exists():
            if os.name == 'nt':  # Windows
                activate_script = venv_path / "Scripts" / "activate.bat"
                python_path = venv_path / "Scripts" / "python.exe"
            else:  # Unix/Linux/Mac
                activate_script = venv_path / "bin" / "activate"
                python_path = venv_path / "bin" / "python"
            
            if activate_script.exists() and python_path.exists():
                print(f"{Colors.OKBLUE}🐍 Using virtual environment: {venv_path.absolute()}{Colors.ENDC}")
                
                # Update Python path for subprocesses
                venv_bin = str(python_path.parent)
                os.environ["PATH"] = f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"
                os.environ["VIRTUAL_ENV"] = str(venv_path.absolute())
                
                # Update service commands to use venv python
                self.config["api"]["command"][0] = str(python_path.parent / "uvicorn")
                self.config["streamlit"]["command"][0] = str(python_path.parent / "streamlit")
                
                return True
        
        print(f"{Colors.WARNING}⚠️  No virtual environment found, using system Python{Colors.ENDC}")
        return False
    
    def start_service(self, service_name):
        """Start a single service"""
        config = self.config[service_name]
        
        print(f"{Colors.OKBLUE}🚀 Starting {config['name']}...{Colors.ENDC}")
        
        # Create log file
        log_file = open(config["log_file"], "w", encoding="utf-8")
        
        # Write startup header to log
        log_file.write(f"=== {config['name']} Log - Started at {datetime.now().isoformat()} ===\n")
        log_file.flush()
        
        try:
            # Start the process
            process = subprocess.Popen(
                config["command"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=config["cwd"],
                text=True,
                bufsize=1
            )
            
            self.services[service_name] = {
                "process": process,
                "log_file": log_file,
                "config": config
            }
            
            print(f"  ✅ {config['name']} started (PID: {process.pid})")
            print(f"  📄 Logs: {config['log_file']}")
            
            if config.get("port"):
                print(f"  🌐 Port: {config['port']}")
            
            # Wait for startup delay
            time.sleep(config["startup_delay"])
            
            return True
            
        except Exception as e:
            print(f"  {Colors.FAIL}❌ Failed to start {config['name']}: {e}{Colors.ENDC}")
            log_file.close()
            return False
    
    def check_service_health(self, service_name):
        """Check if a service is running"""
        if service_name not in self.services:
            return False
        
        process = self.services[service_name]["process"]
        return process.poll() is None
    
    def stop_service(self, service_name):
        """Stop a single service"""
        if service_name not in self.services:
            return
        
        service = self.services[service_name]
        config = service["config"]
        
        print(f"{Colors.WARNING}🛑 Stopping {config['name']}...{Colors.ENDC}")
        
        try:
            process = service["process"]
            
            # Try graceful shutdown first
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                process.kill()
                process.wait()
            
            # Close log file
            service["log_file"].close()
            
            print(f"  ✅ {config['name']} stopped")
            
        except Exception as e:
            print(f"  {Colors.FAIL}❌ Error stopping {config['name']}: {e}{Colors.ENDC}")
        
        finally:
            del self.services[service_name]
    
    def monitor_services(self):
        """Monitor services and restart if they crash"""
        print(f"\n{Colors.OKGREEN}🔄 Monitoring services (Press Ctrl+C to stop all){Colors.ENDC}")
        
        while self.running:
            try:
                time.sleep(10)  # Check every 10 seconds
                
                for service_name in list(self.services.keys()):
                    if not self.check_service_health(service_name):
                        config = self.services[service_name]["config"]
                        print(f"{Colors.FAIL}💥 {config['name']} crashed! Restarting...{Colors.ENDC}")
                        
                        # Clean up crashed service
                        self.stop_service(service_name)
                        
                        # Restart service
                        time.sleep(2)
                        self.start_service(service_name)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Colors.FAIL}❌ Monitor error: {e}{Colors.ENDC}")
    
    def print_status(self):
        """Print current status of all services"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}📊 Service Status:{Colors.ENDC}")
        print("═" * 50)
        
        for service_name, config in self.config.items():
            if service_name in self.services:
                status = "🟢 Running" if self.check_service_health(service_name) else "🔴 Stopped"
                pid = self.services[service_name]["process"].pid
                print(f"{config['name']:<20} {status} (PID: {pid})")
            else:
                print(f"{config['name']:<20} 🔴 Not Started")
        
        print("\n📄 Log Files:")
        for service_name, config in self.config.items():
            print(f"  {config['name']:<20} {config['log_file']}")
        
        # Show access URLs
        print(f"\n🌐 Access URLs:")
        if "api" in self.services and self.check_service_health("api"):
            print(f"  API Documentation:    http://localhost:8000/docs")
            print(f"  API Health Check:     http://localhost:8000/health")
        
        if "streamlit" in self.services and self.check_service_health("streamlit"):
            print(f"  Web Interface:        http://localhost:8501")
        
        if "ngrok" in self.services and self.check_service_health("ngrok"):
            print(f"  Ngrok Status:         http://localhost:4040")
            print(f"  Public URL:           Check ngrok.log for public URL")
    
    def start_all(self):
        """Start all services"""
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Activate virtual environment
        self.activate_venv()
        
        self.running = True
        
        # Start services in order
        services_order = ["ngrok", "api", "streamlit"]
        
        for service_name in services_order:
            if not self.start_service(service_name):
                print(f"{Colors.FAIL}❌ Failed to start {service_name}, stopping...{Colors.ENDC}")
                self.stop_all()
                return False
            
            print()  # Add spacing
        
        # Print status
        self.print_status()
        
        # Start monitoring
        try:
            self.monitor_services()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()
        
        return True
    
    def stop_all(self):
        """Stop all services"""
        print(f"\n{Colors.WARNING}🛑 Shutting down all services...{Colors.ENDC}")
        
        self.running = False
        
        # Stop services in reverse order
        services_order = ["streamlit", "api", "ngrok"]
        
        for service_name in services_order:
            if service_name in self.services:
                self.stop_service(service_name)
        
        print(f"{Colors.OKGREEN}✅ All services stopped{Colors.ENDC}")
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n{Colors.WARNING}⚡ Received signal {signum}, shutting down...{Colors.ENDC}")
        self.stop_all()
        sys.exit(0)

def main():
    """Main entry point"""
    manager = ServiceManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        success = manager.start_all()
        return 0 if success else 1
    except Exception as e:
        print(f"{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")
        manager.stop_all()
        return 1

if __name__ == "__main__":
    sys.exit(main())