# -*- coding: utf-8 -*-

# Ngưỡng phát hiện bất thường (Anomaly Detection Thresholds)
LOSS_THRESHOLD = 5.0        # Nếu mất gói > 5% thì coi là ANOMALY
DELAY_THRESHOLD = 50.0      # Nếu độ trễ > 50ms thì coi là WARNING
THROUGHPUT_THRESHOLD = 2.0  # Nếu băng thông < 2Mbps thì coi là WARNING

# Cấu hình cổng mạng (Switch Port Mapping)
# Switch s1 ports
S1_PORT_H1 = 1
S1_PORT_H2 = 2
S1_PORT_S2 = 3  # Đường truyền chính sang s2
S1_PORT_S3 = 4  # Đường truyền dự phòng sang s3

# Switch s2 ports
S2_PORT_H4 = 1
S2_PORT_S1 = 2
S2_PORT_S3 = 3

# Switch s3 ports
S3_PORT_H3 = 1
S3_PORT_S2 = 2  # Đường truyền chính sang s2
S3_PORT_S1 = 3  # Đường truyền dự phòng sang s1

def detect_status(delay_ms, loss_pct, throughput_mbps):
    """
    Phân loại trạng thái hiệu năng mạng dựa trên các chỉ số.
    """
    if loss_pct > LOSS_THRESHOLD:
        return "ANOMALY"
    if delay_ms > DELAY_THRESHOLD:
        return "WARNING"
    if throughput_mbps < THROUGHPUT_THRESHOLD:
        return "WARNING"
    return "NORMAL"
