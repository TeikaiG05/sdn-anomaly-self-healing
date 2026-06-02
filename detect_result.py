# -*- coding: utf-8 -*-

import sdn_config

samples = [
    {
        "scenario": "normal_main_path",
        "delay_ms": 25.159,
        "loss_pct": 0,
        "throughput_mbps": 9.54
    },
    {
        "scenario": "udp_congestion",
        "delay_ms": 347.558,
        "loss_pct": 20,
        "throughput_mbps": 7.01
    },
    {
        "scenario": "after_self_healing",
        "delay_ms": 24.871,
        "loss_pct": 0,
        "throughput_mbps": 19.1
    }
]

for s in samples:
    status = sdn_config.detect_status(
        s["delay_ms"],
        s["loss_pct"],
        s["throughput_mbps"]
    )

    if s["scenario"] == "after_self_healing" and status == "NORMAL":
        status = "RECOVERED"

    print(
        s["scenario"],
        "delay=", s["delay_ms"],
        "loss=", s["loss_pct"],
        "throughput=", s["throughput_mbps"],
        "=>",
        status
    )
