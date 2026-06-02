# -*- coding: utf-8 -*-

import json
import time
import urllib.request
from prometheus_client import start_http_server, Gauge

# Định nghĩa các metrics cho Prometheus
delay_gauge = Gauge("sdn_delay_ms", "SDN average delay in milliseconds")
loss_gauge = Gauge("sdn_loss_pct", "SDN packet loss percentage")
throughput_gauge = Gauge("sdn_throughput_mbps", "SDN throughput in Mbps")
status_gauge = Gauge("sdn_status", "0=NORMAL, 1=WARNING, 2=ANOMALY, 3=RECOVERED")

# URL API của Ryu Controller
RYU_DOCKER_URL = "http://sdn-ryu:8080/sdn/stats"
RYU_LOCAL_URL = "http://localhost:8080/sdn/stats"

if __name__ == "__main__":
    start_http_server(8000)
    print("Exporter running on http://localhost:8000/metrics")
    print("Starting collection loop...")

    while True:
        res_body = None
        current_url = None
        
        # Thử lấy dữ liệu qua cổng docker, nếu không được thì fallback sang localhost
        for url in [RYU_DOCKER_URL, RYU_LOCAL_URL]:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as response:
                    res_body = response.read().decode('utf-8')
                    current_url = url
                    break
            except Exception:
                continue
                
        if res_body:
            try:
                data = json.loads(res_body)
                
                # Cập nhật Prometheus Gauges
                delay_gauge.set(data["delay_ms"])
                loss_gauge.set(data["loss_pct"])
                throughput_gauge.set(data["throughput_mbps"])
                status_gauge.set(data["status"])
                
                print(f"Scraped from {current_url} - delay: {data['delay_ms']}ms, loss: {data['loss_pct']}%, throughput: {data['throughput_mbps']}Mbps, status: {data['status']}")
            except Exception as parse_err:
                print(f"Error parsing json data: {parse_err}")
        else:
            print("Could not connect to Ryu Controller REST API (tried both sdn-ryu and localhost)")
            
        time.sleep(5)
