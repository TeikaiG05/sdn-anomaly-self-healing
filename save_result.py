# -*- coding: utf-8 -*-

import csv
from datetime import datetime
import sdn_config

samples = [
    {
        "scenario": "normal",
        "delay_ms": 25.101,
        "loss_pct": 0,
        "throughput_mbps": 9.55
    },
    {
        "scenario": "udp_congestion",
        "delay_ms": 347.558,
        "loss_pct": 20,
        "throughput_mbps": 7.01
    }
]

with open("result.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "time",
        "scenario",
        "delay_ms",
        "loss_pct",
        "throughput_mbps",
        "status"
    ])

    for s in samples:
        status = sdn_config.detect_status(
            s["delay_ms"],
            s["loss_pct"],
            s["throughput_mbps"]
        )

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            s["scenario"],
            s["delay_ms"],
            s["loss_pct"],
            s["throughput_mbps"],
            status
        ])

print("Saved result.csv")
