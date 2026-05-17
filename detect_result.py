def detect(delay_ms, loss_pct, throughput_mbps):
    if loss_pct > 5:
        return "ANOMALY"
    if delay_ms > 50:
        return "WARNING"
    if throughput_mbps < 2:
        return "WARNING"
    return "NORMAL"


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
    status = detect(
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
