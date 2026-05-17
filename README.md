# SDN Anomaly Detection and Self-Healing System

## 1. Giới thiệu đề tài

Đây là đồ án chuyên ngành với đề tài:

**Xây dựng hệ thống phát hiện bất thường và tự phục hồi nhằm giảm nghẽn trong mạng SDN**

Hệ thống được xây dựng trong môi trường mô phỏng SDN bằng Mininet, Open vSwitch và Ryu Controller. Mục tiêu chính là phát hiện trạng thái bất thường của mạng dựa trên các chỉ số delay, packet loss và throughput, sau đó tự động kích hoạt cơ chế self-healing để chuyển lưu lượng sang đường dự phòng.

## 2. Công nghệ sử dụng

- Mininet
- Open vSwitch
- Ryu Controller
- Python
- iperf3
- Prometheus
- Grafana
- Git/GitHub

## 3. Kiến trúc hệ thống

Hệ thống gồm các thành phần chính:

1. Mininet Topology: mô phỏng mạng SDN gồm 4 host và 3 switch.
2. Ryu Controller: điều khiển Open vSwitch thông qua OpenFlow 1.3.
3. Anomaly Detection Module: phát hiện bất thường dựa trên delay, packet loss và throughput.
4. Self-Healing Module: tự động reroute khi phát hiện ANOMALY.
5. Prometheus Exporter: xuất metric mạng tại endpoint /metrics.
6. Grafana Dashboard: hiển thị delay, packet loss, throughput và trạng thái mạng.

## 4. Topology

Topology gồm 4 host và 3 switch:

    h1 ---\
           \
    h2 ---- s1 ---- s2 ---- s3 ---- h3
            \               /
             \-------------/
                   |
                  h4

Đường chính:

    s1 -> s2 -> s3

Đường dự phòng:

    s1 -> s3

Trong trạng thái bình thường, lưu lượng từ h1/h2 đến h3 đi qua đường chính. Khi phát hiện nghẽn, hệ thống chuyển lưu lượng sang đường dự phòng.

## 5. Danh sách file

| File | Mô tả |
|---|---|
| topo_sdn.py | File topology Mininet |
| self_healing_controller.py | Ryu Controller tùy chỉnh |
| detect_result.py | Kiểm thử mô-đun phát hiện bất thường |
| auto_heal.py | Script tự động kích hoạt reroute khi phát hiện ANOMALY |
| exporter.py | Prometheus exporter để xuất metric |
| save_result.py | Lưu kết quả kiểm thử ra file CSV |
| result.csv | File kết quả thực nghiệm |

## 6. Cách chạy hệ thống

### Bước 1: Chạy Ryu Controller

Mở terminal thứ nhất:

    ryu-manager --ofp-tcp-listen-port 6653 self_healing_controller.py

Controller sẽ chạy liên tục để điều khiển các switch trong Mininet.

### Bước 2: Chạy topology Mininet

Mở terminal thứ hai:

    sudo mn --custom topo_sdn.py --topo sdntopo --controller remote,ip=127.0.0.1,port=6653 --switch ovsk,protocols=OpenFlow13 --link tc

Kiểm tra kết nối từ h1 đến h3:

    h1 ping -c 5 10.0.0.3

Kiểm tra kết nối từ h2 đến h3:

    h2 ping -c 5 10.0.0.3

Lưu ý: pingall có thể không đạt 100% vì controller chỉ cài flow cho các luồng cần kiểm thử h1/h2 đến h3, không cài đầy đủ flow cho mọi cặp host.

### Bước 3: Chạy mô-đun phát hiện bất thường

    python3 detect_result.py

Kết quả mong đợi:

    normal_main_path delay=25.159 loss=0 throughput=9.54 => NORMAL
    udp_congestion delay=347.558 loss=20 throughput=7.01 => ANOMALY
    after_self_healing delay=24.871 loss=0 throughput=19.1 => RECOVERED

### Bước 4: Chạy self-healing

    python3 auto_heal.py

Khi phát hiện trạng thái ANOMALY, script sẽ tự động thêm flow rule có priority cao hơn để chuyển lưu lượng sang đường dự phòng.

Kiểm tra flow trên switch s1:

    sh ovs-ofctl -O OpenFlow13 dump-flows s1

Kiểm tra flow trên switch s3:

    sh ovs-ofctl -O OpenFlow13 dump-flows s3

Flow self-healing có dạng:

    priority=200, ip,nw_src=10.0.0.1,nw_dst=10.0.0.3 actions=output:s1-eth4
    priority=200, ip,nw_src=10.0.0.2,nw_dst=10.0.0.3 actions=output:s1-eth4
    priority=200, ip,nw_src=10.0.0.3,nw_dst=10.0.0.1 actions=output:s3-eth3
    priority=200, ip,nw_src=10.0.0.3,nw_dst=10.0.0.2 actions=output:s3-eth3

### Bước 5: Chạy Prometheus Exporter

    python3 exporter.py

Exporter chạy tại:

    http://localhost:8000/metrics

Các metric được xuất ra gồm:

| Metric | Ý nghĩa |
|---|---|
| sdn_delay_ms | Delay trung bình |
| sdn_loss_pct | Tỷ lệ packet loss |
| sdn_throughput_mbps | Throughput |
| sdn_status | Trạng thái mạng |

Quy ước trạng thái:

| Giá trị | Trạng thái |
|---:|---|
| 0 | NORMAL |
| 1 | WARNING |
| 2 | ANOMALY |
| 3 | RECOVERED |

### Bước 6: Chạy Prometheus

Trong thư mục Prometheus:

    cd ~/prometheus
    ./prometheus --config.file=prometheus.yml

Kiểm tra target:

    http://localhost:9090/targets

Target sdn_monitor cần ở trạng thái UP.

Ví dụ cấu hình prometheus.yml:

    global:
      scrape_interval: 5s

    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']

      - job_name: 'sdn_monitor'
        static_configs:
          - targets: ['localhost:8000']

### Bước 7: Chạy Grafana

Mở Grafana tại:

    http://localhost:3000

Tạo dashboard với các panel:

| Panel | Query |
|---|---|
| SDN Delay | sdn_delay_ms |
| Packet Loss | sdn_loss_pct |
| Throughput | sdn_throughput_mbps |
| Anomaly Status | sdn_status |

Gợi ý:
- Delay, Packet Loss và Throughput nên dùng Time series.
- Anomaly Status nên dùng Stat hoặc State timeline.
- Bật auto refresh 5s hoặc 10s để thấy dữ liệu thay đổi.

## 7. Kịch bản kiểm thử

### Kịch bản 1: Mạng bình thường

Kiểm tra ping từ h1 đến h3:

    h1 ping -c 20 10.0.0.3

Kết quả:

| Chỉ số | Giá trị |
|---|---:|
| Delay trung bình | 25.159 ms |
| Packet loss | 0% |
| Throughput | 9.54 Mbps |
| Trạng thái | NORMAL |

### Kịch bản 2: Gây nghẽn bằng UDP

Chạy iperf3 server trên h3:

    h3 iperf3 -s -p 5201 &
    h3 iperf3 -s -p 5202 &

Tạo hai luồng UDP từ h1 và h2 đến h3:

    h1 iperf3 -u -c 10.0.0.3 -p 5201 -t 60 -b 8M &
    h2 iperf3 -u -c 10.0.0.3 -p 5202 -t 60 -b 8M &

Đo ping trong lúc nghẽn:

    h1 ping -c 20 10.0.0.3

Kết quả:

| Chỉ số | Giá trị |
|---|---:|
| Delay trung bình | 347.558 ms |
| Packet loss | 20% |
| Throughput | 7.01 Mbps |
| Trạng thái | ANOMALY |

### Kịch bản 3: Sau self-healing

Sau khi chạy auto_heal.py, hệ thống chuyển lưu lượng sang đường dự phòng s1-s3.

Kiểm tra lại:

    h1 ping -c 20 10.0.0.3

Kết quả:

| Chỉ số | Giá trị |
|---|---:|
| Delay trung bình | 24.871 ms |
| Packet loss | 0% |
| Throughput | 19.1 Mbps |
| Trạng thái | RECOVERED |

## 8. Kết quả thực nghiệm tổng hợp

| Giai đoạn | Đường đi | Delay trung bình | Packet loss | Throughput | Trạng thái |
|---|---|---:|---:|---:|---|
| Bình thường | s1-s2-s3 | 25.159 ms | 0% | 9.54 Mbps | NORMAL |
| Khi nghẽn UDP | s1-s2-s3 | 347.558 ms | 20% | 7.01 Mbps | ANOMALY |
| Sau self-healing | s1-s3 | 24.871 ms | 0% | 19.1 Mbps | RECOVERED |

## 9. Nhận xét kết quả

Kết quả thực nghiệm cho thấy hệ thống đã phát hiện được trạng thái bất thường khi packet loss và delay tăng cao. Trong kịch bản nghẽn UDP, delay trung bình tăng lên 347.558 ms và packet loss đạt 20%, do đó mô-đun phát hiện phân loại trạng thái là ANOMALY.

Sau khi self-healing được kích hoạt, hệ thống cài đặt các flow rule có priority cao hơn để chuyển lưu lượng từ đường chính s1-s2-s3 sang đường dự phòng s1-s3. Kết quả sau phục hồi cho thấy delay giảm xuống còn 24.871 ms, packet loss trở về 0% và throughput tăng lên 19.1 Mbps.

Điều này chứng minh cơ chế reroute đã giúp hệ thống khôi phục hiệu năng mạng sau khi phát hiện nghẽn.

## 10. Hướng phát triển tiếp theo

- Tự động thu thập metric trực tiếp từ Mininet hoặc Ryu Controller.
- Tích hợp chặt chẽ hơn giữa Prometheus exporter và self-healing engine.
- Bổ sung thuật toán phát hiện bất thường bằng EWMA hoặc machine learning nhẹ.
- Thêm nhiều kịch bản nghẽn khác nhau.
- Đánh giá thêm các chỉ số jitter, link utilization và flow statistics.
- Tối ưu cơ chế chống dao động khi reroute nhiều lần.

## 11. Thành viên thực hiện

| Họ tên | MSSV |
|---|---|
| Đỗ Trần Tuấn Kiệt | 23520811 |
| Phùng Gia Kiệt | 23520818 |

