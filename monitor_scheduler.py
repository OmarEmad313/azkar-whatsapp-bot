import os
import sys
import time
import psutil
import datetime
import subprocess
from pathlib import Path
import argparse

def get_scheduler_processes():
    """Find Python processes that appear to be our scheduler"""
    scheduler_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            # Look for python processes with scheduler command in args
            if proc.info['name'].lower() in ('python.exe', 'pythonw.exe'):
                cmdline = proc.info['cmdline']
                if cmdline and any('scheduler' in arg for arg in cmdline) and any('interfaces.cli' in arg for arg in cmdline):
                    scheduler_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return scheduler_processes

def format_time_ago(timestamp):
    """Format timestamp as time ago"""
    now = datetime.datetime.now()
    dt = now - datetime.datetime.fromtimestamp(timestamp)
    
    seconds = dt.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds/60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds/3600)} hours ago"
    else:
        return f"{int(seconds/86400)} days ago"

def show_recent_logs(lines=10):
    """Show recent log entries"""
    log_path = Path("logs/scheduler.log")
    
    if not log_path.exists():
        return "Log file not found."
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            log_contents = f.readlines()
        
        if not log_contents:
            return "Log file is empty."
        
        return ''.join(log_contents[-lines:])
    except Exception as e:
        return f"Error reading log file: {e}"

def terminate_process(pid):
    """Terminate a process by PID"""
    try:
        process = psutil.Process(pid)
        process.terminate()
        
        # Give it a moment to terminate gracefully
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()  # Force kill if it doesn't terminate
        
        return True
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        print(f"Error terminating process: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitor and control Azkar Bot scheduler")
    parser.add_argument("--kill", action="store_true", help="Terminate the scheduler process")
    parser.add_argument("--logs", type=int, default=10, help="Number of recent log lines to show")
    args = parser.parse_args()

    # Get processes
    processes = get_scheduler_processes()
    
    # Header
    print("=" * 50)
    print("AZKAR BOT SCHEDULER MONITOR")
    print("=" * 50)
    
    # Process information
    if processes:
        print(f"✅ Found {len(processes)} scheduler process(es):")
        for i, proc in enumerate(processes):
            try:
                create_time = datetime.datetime.fromtimestamp(proc.info['create_time'])
                running_time = format_time_ago(proc.info['create_time'])
                mem_usage = proc.memory_info().rss / (1024 * 1024)  # MB
                
                print(f"\nProcess #{i+1}")
                print(f"PID: {proc.pid}")
                print(f"Started: {create_time.strftime('%Y-%m-%d %H:%M:%S')} ({running_time})")
                print(f"Memory: {mem_usage:.1f} MB")
                
                if args.kill:
                    print(f"Terminating process {proc.pid}...")
                    if terminate_process(proc.pid):
                        print(f"✓ Successfully terminated")
                    else:
                        print(f"✗ Failed to terminate")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"Error accessing process: {e}")
    else:
        print("❌ No scheduler processes found running")
    
    # Log information
    log_path = Path("logs/scheduler.log")
    if log_path.exists():
        mod_time = datetime.datetime.fromtimestamp(log_path.stat().st_mtime)
        time_ago = format_time_ago(log_path.stat().st_mtime)
        print(f"\nLog last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_ago})")
    
    # Show recent logs if requested
    if args.logs > 0:
        print(f"\nRecent log entries (last {args.logs} lines):")
        print("-" * 50)
        print(show_recent_logs(args.logs))
        print("-" * 50)
    
    # Helpful tips
    print("\nTIPS:")
    print("- To kill the scheduler: --kill")
    print("- To view more log lines: --logs 50")
    print("- To restart after code changes, use Task Scheduler or kill and restart")

if __name__ == "__main__":
    main()
