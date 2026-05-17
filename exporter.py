from prometheus_client import start_http_server, Gauge
import time

delay_gauge = Gauge("sdn_delay_ms", "SDN average delay in milliseconds")
loss_gauge = Gauge("sdn_loss_pct", "SDN packet loss percentage")
throughput_gauge = Gauge("sdn_throughput_mbps", "SDN throughput in Mbps")
status_gauge = Gauge("sdn_status", "0=NORMAL, 1=WARNING, 2=ANOMALY, 3=RECOVERED")

samples = [
    {
        "scenario": "normal_main_path",
        "delay_ms": 25.159,
        "loss_pct": 0,
        "throughput_mbps": 9.54,
        "status": 0
    },
    {
        "scenario": "udp_congestion",
        "delay_ms": 347.558,
        "loss_pct": 20,
        "throughput_mbps": 7.01,
        "status": 2
    },
    {
        "scenario": "after_self_healing",
        "delay_ms": 24.871,
        "loss_pct": 0,
        "throughput_mbps": 19.1,
        "status": 3
    }
]

if __name__ == "__main__":
    start_http_server(8000)
    print("Exporter running on http://localhost:8000/metrics")

    i = 0
    while True:
        s = samples[i % len(samples)]

        delay_gauge.set(s["delay_ms"])
        loss_gauge.set(s["loss_pct"])
        throughput_gauge.set(s["throughput_mbps"])
        status_gauge.set(s["status"])

        print(
            s["scenario"],
            "delay=", s["delay_ms"],
            "loss=", s["loss_pct"],
            "throughput=", s["throughput_mbps"],
            "status=", s["status"]
        )

        i += 1
        time.sleep(10)
