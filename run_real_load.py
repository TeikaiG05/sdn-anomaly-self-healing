# -*- coding: utf-8 -*-
import subprocess
import re
import time
import sys

def get_host_pid(host_name):
    try:
        # Tìm tiến trình của mininet host
        out = subprocess.check_output(["ps", "ax"], universal_newlines=True)
        for line in out.splitlines():
            # Mininet chạy bash shell cho host và tên cmd là mininet:h1
            if f"mininet:{host_name}" in line or f"bash" in line and f" {host_name} " in line:
                match = re.search(r'^\s*(\d+)', line)
                if match:
                    return int(match.group(1))
    except Exception as e:
        print(f"Loi tim PID cho {host_name}: {e}")
    return None

def run_in_namespace(host_name, cmd_args):
    pid = get_host_pid(host_name)
    if not pid:
        try:
            out = subprocess.check_output(["pgrep", "-f", f"mininet:{host_name}"], universal_newlines=True)
            pids = out.strip().split()
            if pids:
                pid = int(pids[0])
        except Exception:
            pass
            
    if not pid:
        print(f"Không tìm thấy tiến trình đang chạy của host {host_name}. Hãy chắc chắn Mininet đang chạy!")
        return False
        
    # Chạy lệnh trong network namespace của host bằng nsenter
    full_cmd = ["sudo", "nsenter", "-t", str(pid), "-n"] + cmd_args
    subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

if __name__ == "__main__":
    print("=== Tao tai bang IPERF3 ===")
    
    # 1. Khởi chạy iperf3 server trên h3
    if not run_in_namespace("h3", ["iperf3", "-s", "-p", "5201", "-D"]):
        sys.exit(1)
    run_in_namespace("h3", ["iperf3", "-s", "-p", "5202", "-D"])
    
    time.sleep(2)
    
    run_in_namespace("h1", ["iperf3", "-u", "-c", "10.0.0.3", "-p", "5201", "-t", "30", "-b", "8M"])
    run_in_namespace("h2", ["iperf3", "-u", "-c", "10.0.0.3", "-p", "5202", "-t", "30", "-b", "8M"])
    
    # Chờ tải chạy xong
    for i in range(60, 0, -5):
        print(f"Còn lại {i} giây...")
        time.sleep(5)
        
    print("\n=== Ket thuc thoi gian truyen tai ===")
    subprocess.call(["sudo", "killall", "iperf3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Hoan thanh kiem thu thuc te")
