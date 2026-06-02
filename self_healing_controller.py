# -*- coding: utf-8 -*-

import json
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import hub
from webob import Response

# Import configuration and common functions
import sdn_config


class SelfHealingStatsController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SelfHealingStatsController, self).__init__(req, link, data, **config)
        self.ryu_app = data['ryu_app']

    @route('sdn', '/sdn/stats', methods=['GET'])
    def get_stats(self, req, **kwargs):
        body = json.dumps(self.ryu_app.metrics)
        return Response(content_type='application/json', body=body)

    @route('sdn', '/sdn/set_metrics', methods=['POST'])
    def set_metrics(self, req, **kwargs):
        try:
            data = json.loads(req.body.decode('utf-8'))
            self.ryu_app.logger.info("Received simulated metrics: %s", data)
            
            if 'delay_ms' in data:
                self.ryu_app.metrics['delay_ms'] = float(data['delay_ms'])
            if 'loss_pct' in data:
                self.ryu_app.metrics['loss_pct'] = float(data['loss_pct'])
            if 'throughput_mbps' in data:
                self.ryu_app.metrics['throughput_mbps'] = float(data['throughput_mbps'])
                
            return Response(status=200, body=b"OK")
        except Exception as e:
            self.ryu_app.logger.error("Error setting metrics: %s", e)
            return Response(status=400, body=str(e).encode('utf-8'))


class SelfHealingController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SelfHealingController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(SelfHealingStatsController, {'ryu_app': self})
        
        self.datapaths = {}
        self.healed = False
        
        # Initial network metrics
        self.metrics = {
            'delay_ms': 25.159,
            'loss_pct': 0.0,
            'throughput_mbps': 9.54,
            'status': 0  # 0=NORMAL, 1=WARNING, 2=ANOMALY, 3=RECOVERED
        }
        
        # Spawn the background monitor thread
        self.monitor_thread = hub.spawn(self._monitor_loop)

    def add_flow(self, datapath, priority, match, actions, cookie=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            cookie=cookie
        )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info("Register datapath: %016x", datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info("Unregister datapath: %016x", datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser

        self.logger.info("Switch connected: %s", dpid)

        # Default drop to avoid loop
        match = parser.OFPMatch()
        actions = []
        self.add_flow(datapath, 0, match, actions)

        if dpid == 1:
            self.install_s1(datapath)
        elif dpid == 2:
            self.install_s2(datapath)
        elif dpid == 3:
            self.install_s3(datapath)

    def install_s1(self, datapath):
        parser = datapath.ofproto_parser

        # IPv4 h1/h2 -> h3 via main path s1 -> s2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.1',
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S1_PORT_S2)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.2',
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S1_PORT_S2)])

        # IPv4 h3 -> h1/h2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.1'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S1_PORT_H1)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.2'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S1_PORT_H2)])

        # ARP h1/h2 asking for h3 -> s2
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.3'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S1_PORT_S2)])

        # ARP h3 asking/replying for h1 -> h1
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.1'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S1_PORT_H1)])

        # ARP h3 asking/replying for h2 -> h2
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.2'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S1_PORT_H2)])

        self.logger.info("Installed default flows on s1")

    def install_s2(self, datapath):
        parser = datapath.ofproto_parser

        # IPv4 h1/h2 -> h3
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S2_PORT_S3)])

        # IPv4 h3 -> h1/h2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.1'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S2_PORT_S1)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.2'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S2_PORT_S1)])

        # ARP to h3 -> s3
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.3'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S2_PORT_S3)])

        # ARP to h1/h2 -> s1
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.1'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S2_PORT_S1)])

        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.2'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S2_PORT_S1)])

        self.logger.info("Installed default flows on s2")

    def install_s3(self, datapath):
        parser = datapath.ofproto_parser

        # IPv4 h1/h2 -> h3
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S3_PORT_H3)])

        # IPv4 h3 -> h1/h2 via s2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.1'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S3_PORT_S2)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.2'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(sdn_config.S3_PORT_S2)])

        # ARP to h3 -> h3
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.3'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S3_PORT_H3)])

        # ARP to h1/h2 -> s2
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.1'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S3_PORT_S2)])

        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.2'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(sdn_config.S3_PORT_S2)])

        self.logger.info("Installed default flows on s3")

    def _monitor_loop(self):
        while True:
            hub.sleep(2)
            
            status_str = sdn_config.detect_status(
                self.metrics['delay_ms'],
                self.metrics['loss_pct'],
                self.metrics['throughput_mbps']
            )
            
            self.logger.debug(
                "Monitor: delay=%.2f, loss=%.2f, throughput=%.2f -> %s (healed=%s)",
                self.metrics['delay_ms'], self.metrics['loss_pct'],
                self.metrics['throughput_mbps'], status_str, self.healed
            )
            
            if status_str == "ANOMALY":
                if not self.healed:
                    self.logger.warning("[MONITOR] ANOMALY detected! Initiating Self-Healing.")
                    self.apply_self_healing()
            elif status_str == "NORMAL":
                if self.healed:
                    self.logger.info("[MONITOR] Status NORMAL. Initiating Restore (Failback).")
                    self.restore_primary_path()
                else:
                    self.metrics['status'] = 0  # NORMAL
            elif status_str == "WARNING":
                if not self.healed:
                    self.metrics['status'] = 1  # WARNING

    def apply_self_healing(self):
        dp1 = self.datapaths.get(1)
        dp3 = self.datapaths.get(3)
        
        if not dp1 or not dp3:
            self.logger.error("[SELF-HEALING] Cannot apply healing: s1 or s3 not connected")
            return
            
        parser1 = dp1.ofproto_parser
        parser3 = dp3.ofproto_parser
        
        self.logger.info("[SELF-HEALING] Installing high priority flows (priority=200) for backup path")
        
        # s1: Redirect IP h1/h2 -> h3 and ARP to s3 backup (Port 4)
        match_ip_h1 = parser1.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.1', ipv4_dst='10.0.0.3')
        match_ip_h2 = parser1.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.2', ipv4_dst='10.0.0.3')
        match_arp_h3 = parser1.OFPMatch(eth_type=0x0806, arp_tpa='10.0.0.3')
        
        self.add_flow(dp1, 200, match_ip_h1, [parser1.OFPActionOutput(sdn_config.S1_PORT_S3)], cookie=999)
        self.add_flow(dp1, 200, match_ip_h2, [parser1.OFPActionOutput(sdn_config.S1_PORT_S3)], cookie=999)
        self.add_flow(dp1, 200, match_arp_h3, [parser1.OFPActionOutput(sdn_config.S1_PORT_S3)], cookie=999)
        
        # s3: Redirect IP h3 -> h1/h2 and ARP to s1 backup (Port 3)
        match_ip_h3_to_h1 = parser3.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.3', ipv4_dst='10.0.0.1')
        match_ip_h3_to_h2 = parser3.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.3', ipv4_dst='10.0.0.2')
        match_arp_h1 = parser3.OFPMatch(eth_type=0x0806, arp_tpa='10.0.0.1')
        match_arp_h2 = parser3.OFPMatch(eth_type=0x0806, arp_tpa='10.0.0.2')
        
        self.add_flow(dp3, 200, match_ip_h3_to_h1, [parser3.OFPActionOutput(sdn_config.S3_PORT_S1)], cookie=999)
        self.add_flow(dp3, 200, match_ip_h3_to_h2, [parser3.OFPActionOutput(sdn_config.S3_PORT_S1)], cookie=999)
        self.add_flow(dp3, 200, match_arp_h1, [parser3.OFPActionOutput(sdn_config.S3_PORT_S1)], cookie=999)
        self.add_flow(dp3, 200, match_arp_h2, [parser3.OFPActionOutput(sdn_config.S3_PORT_S1)], cookie=999)
        
        self.healed = True
        self.metrics['status'] = 2  # ANOMALY status (representing reroute active)
        self.logger.info("[SELF-HEALING] Backup path active. Reroute completed.")

    def restore_primary_path(self):
        dp1 = self.datapaths.get(1)
        dp3 = self.datapaths.get(3)
        
        self.logger.info("[SELF-HEALING] Restoring primary path. Deleting backup flows (cookie=999)")
        
        if dp1:
            ofproto = dp1.ofproto
            parser = dp1.ofproto_parser
            mod = parser.OFPFlowMod(
                datapath=dp1,
                cookie=999,
                cookie_mask=0xFFFFFFFF,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY
            )
            dp1.send_msg(mod)
            
        if dp3:
            ofproto = dp3.ofproto
            parser = dp3.ofproto_parser
            mod = parser.OFPFlowMod(
                datapath=dp3,
                cookie=999,
                cookie_mask=0xFFFFFFFF,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY
            )
            dp3.send_msg(mod)
            
        self.healed = False
        self.metrics['status'] = 3  # RECOVERED status (meaning back to normal)
        self.logger.info("[SELF-HEALING] Restored to primary path. Failback completed.")
