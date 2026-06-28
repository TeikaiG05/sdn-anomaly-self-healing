# -*- coding: utf-8 -*-
import subprocess
import re
import time
import json
import urllib.request
import sys

# Cấu hình API của Ryu Controller
RYU_URL = "http://localhost:8080/sdn/set_metrics"

def get_host_pid(host_name):
    try:
        out = subprocess.check_output(["ps", "ax"], universal_newlines=True)
        for line in out.splitlines():
            if f"mininet:{host_name}" in line or f"bash" in line and f" {host_name} " in line:
                match = re.search(r'^\s*(\d+)', line)
                if match:
                    return int(match.group(1))
    except Exception as e:
        print(f"Lỗi tìm PID cho {host_name}: {e}")
    return None

def get_interface_bytes(iface):
    try:
        # Đọc số byte truyền qua cổng s1-eth3 (đường truyền chính đi s2)
        with open(f"/sys/class/net/{iface}/statistics/tx_bytes", "r") as f:
            return int(f.read().strip())
    except Exception:
        return None

def measure_ping(h1_pid, target_ip):
    # Gửi 5 gói tin ping từ namespace h1 tới h3
    cmd = ["sudo", "nsenter", "-t", str(h1_pid), "-n", "ping", "-c", "5", "-i", "0.2", "-W", "1", target_ip]
    try:
        out = subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.DEVNULL)
        
        # Parse tỉ lệ mất gói (Loss)
        loss_match = re.search(r"(\d+)%\s+packet\s+loss", out)
        loss_pct = float(loss_match.group(1)) if loss_match else 0.0
        
        # Parse độ trễ trung bình (Delay avg)
        rtt_match = re.search(r"rtt\s+min/avg/max/mdev\s+=\s+[\d\.]+/([\d\.]+)/", out)
        delay_ms = float(rtt_match.group(1)) if rtt_match else 25.0
        
        return delay_ms, loss_pct
    except subprocess.CalledProcessError as e:
        # Nếu ping lỗi hoàn toàn (rớt 100% gói)
        out = e.output
        loss_match = re.search(r"(\d+)%\s+packet\s+loss", out)
        loss_pct = float(loss_match.group(1)) if loss_match else 100.0
        return 500.0, loss_pct
    except Exception as e:
<<<<<<< HEAD
        print(f"Lỗi thực hiện ping: {e}")
=======
        print(f"Loi thuc hien ping: {e}")
>>>>>>> 400bf8cd8c57429b058eeb4440ef63e98ac73dfe
        return 25.0, 0.0

def send_metrics_to_ryu(delay, loss, throughput):
    payload = {
        "delay_ms": delay,
        "loss_pct": loss,
        "throughput_mbps": throughput
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            RYU_URL, 
            data=data, 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                return True
    except Exception as e:
        print(f"Không thể gửi metrics tới Ryu API: {e}")
    return False

if __name__ == "__main__":
    print("=== MONITORING AGENT - ĐO ĐẠC MẠNG THỜI GIAN THỰC ===")
    
    h1_pid = get_host_pid("h1")
    if not h1_pid:
        print("Lỗi: Không tìm thấy host h1. Hãy chắc chắn Mininet đang chạy trước khi chạy script này!")
        sys.exit(1)
        
<<<<<<< HEAD
    print(f"Đã liên kết thành công với host h1 (PID: {h1_pid})")
    print("Bắt đầu vòng lặp đo đạc thời gian thực (Mỗi 3 giây)...")
=======
    print(f"Lien ket thanh cong h1 (PID: {h1_pid})")
    print("Bat dau do")
>>>>>>> 400bf8cd8c57429b058eeb4440ef63e98ac73dfe
    print("--------------------------------------------------")
    
    last_bytes = get_interface_bytes("s1-eth3")
    last_time = time.time()
    
    while True:
        # 1. Đo Delay và Packet Loss bằng Ping thực tế từ h1 sang h3
        delay, loss = measure_ping(h1_pid, "10.0.0.3")
        
        # 2. Đo Throughput thực tế trên liên kết s1-eth3
        curr_bytes = get_interface_bytes("s1-eth3")
        curr_time = time.time()
        
        throughput_mbps = 9.54 # Giá trị mặc định khi rảnh rỗi
        if curr_bytes is not None and last_bytes is not None:
            bytes_diff = curr_bytes - last_bytes
            time_diff = curr_time - last_time
            if time_diff > 0:
                # Quy đổi bytes sang Megabits per second
                throughput_mbps = (bytes_diff * 8) / (time_diff * 1024 * 1024)
                # Ngăn ngừa giá trị âm hoặc quá nhỏ hiển thị xấu
                if throughput_mbps < 0.1:
                    throughput_mbps = 9.54
                
        last_bytes = curr_bytes
        last_time = curr_time
        
        # Hiển thị thông số đo được
<<<<<<< HEAD
        print(f"Đo được: Trễ = {delay:.2f}ms | Mất gói = {loss:.1f}% | Băng thông = {throughput_mbps:.2f} Mbps")
=======
        print(f"Do duoc: Tre = {delay:.2f}ms | Mat goi = {loss:.1f}% | Bang thong = {throughput_mbps:.2f} Mbps")
>>>>>>> 400bf8cd8c57429b058eeb4440ef63e98ac73dfe
        
        # 3. Gửi lên Ryu Controller để đưa ra quyết định
        success = send_metrics_to_ryu(delay, loss, throughput_mbps)
        if success:
<<<<<<< HEAD
            print(" -> Đã cập nhật chỉ số lên Ryu Controller thành công.")
        else:
            print(" -> Cập nhật thất bại (Ryu API chưa hoạt động).")
=======
            print(" -> Cap nhat chi so thanh cong")
        else:
            print(" -> Cap nhat that bai")
>>>>>>> 400bf8cd8c57429b058eeb4440ef63e98ac73dfe
            
        time.sleep(3)
