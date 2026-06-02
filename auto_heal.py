# -*- coding: utf-8 -*-

import json
import time
import urllib.request
import sdn_config

# Danh sách kịch bản để chạy giả lập
samples = [
    {
        "scenario": "1. normal_main_path (Mạng bình thường - Đường dẫn chính)",
        "delay_ms": 25.159,
        "loss_pct": 0.0,
        "throughput_mbps": 9.54
    },
    {
        "scenario": "2. udp_congestion (Nghẽn mạng - Kích hoạt Reroute)",
        "delay_ms": 347.558,
        "loss_pct": 20.0,
        "throughput_mbps": 7.01
    },
    {
        "scenario": "3. after_self_healing (Phục hồi - Kích hoạt Failback/Restore)",
        "delay_ms": 24.871,
        "loss_pct": 0.0,
        "throughput_mbps": 19.1
    }
]

# URL API để đẩy metrics
RYU_DOCKER_URL = "http://sdn-ryu:8080/sdn/set_metrics"
RYU_LOCAL_URL = "http://localhost:8080/sdn/set_metrics"

def send_metrics(metrics):
    data = json.dumps(metrics).encode('utf-8')
    success = False
    
    for url in [RYU_DOCKER_URL, RYU_LOCAL_URL]:
        try:
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    print(f"Đã gửi thành công dữ liệu metrics tới {url}")
                    success = True
                    break
        except Exception:
            continue
            
    if not success:
        print("Lỗi: Không thể kết nối tới Ryu Controller (đã thử cả sdn-ryu và localhost)")

if __name__ == "__main__":
    print("Bắt đầu chạy script kịch bản giả lập tự phục hồi (Self-Healing)...")
    
    for s in samples:
        print("\n" + "="*50)
        print(f"Kịch bản: {s['scenario']}")
        print(f"Chỉ số gửi đi: Delay={s['delay_ms']}ms, Loss={s['loss_pct']}%, Throughput={s['throughput_mbps']}Mbps")
        
        # Đánh giá sơ bộ trạng thái local để hiển thị thông tin
        status = sdn_config.detect_status(s["delay_ms"], s["loss_pct"], s["throughput_mbps"])
        print(f"Đánh giá phân loại trạng thái (Local Classifier): {status}")
        
        # Gửi dữ liệu tới Ryu Controller
        send_metrics({
            "delay_ms": s["delay_ms"],
            "loss_pct": s["loss_pct"],
            "throughput_mbps": s["throughput_mbps"]
        })
        
        print("Đang chờ 10 giây để Ryu xử lý và Prometheus cập nhật dữ liệu...")
        time.sleep(10)
        
    print("\n" + "="*50)
    print("Hoàn thành kịch bản giả lập!")
