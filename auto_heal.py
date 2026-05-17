import os
import time

def apply_reroute():
    print("[SELF-HEALING] Applying backup path s1 -> s3")

    os.system('sudo ovs-ofctl -O OpenFlow13 add-flow s1 "priority=200,ip,nw_src=10.0.0.1,nw_dst=10.0.0.3,actions=output:4"')
    os.system('sudo ovs-ofctl -O OpenFlow13 add-flow s3 "priority=200,ip,nw_src=10.0.0.3,nw_dst=10.0.0.1,actions=output:3"')

    os.system('sudo ovs-ofctl -O OpenFlow13 add-flow s1 "priority=200,ip,nw_src=10.0.0.2,nw_dst=10.0.0.3,actions=output:4"')
    os.system('sudo ovs-ofctl -O OpenFlow13 add-flow s3 "priority=200,ip,nw_src=10.0.0.3,nw_dst=10.0.0.2,actions=output:3"')

    print("[SELF-HEALING] Reroute completed")


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

healed = False

for s in samples:
    status = detect(
        s["delay_ms"],
        s["loss_pct"],
        s["throughput_mbps"]
    )

    print("Scenario:", s["scenario"])
    print("Status:", status)

    if status == "ANOMALY" and not healed:
        apply_reroute()
        healed = True

    time.sleep(3)
