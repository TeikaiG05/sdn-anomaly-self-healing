from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3


class SelfHealingController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def add_flow(self, datapath, priority, match, actions):
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
            instructions=inst
        )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser

        print("Switch connected:", dpid)

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

        # s1 ports:
        # 1=h1, 2=h2, 3=s2, 4=s3 backup

        # IPv4 h1/h2 -> h3 via main path s1 -> s2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.1',
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(3)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.2',
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(3)])

        # IPv4 h3 -> h1/h2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.1'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(1)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.2'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(2)])

        # ARP h1/h2 asking for h3 -> s2
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.3'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(3)])

        # ARP h3 asking/replying for h1 -> h1
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.1'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(1)])

        # ARP h3 asking/replying for h2 -> h2
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.2'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(2)])

        print("Installed flows on s1")

    def install_s2(self, datapath):
        parser = datapath.ofproto_parser

        # s2 ports:
        # 1=h4, 2=s1, 3=s3

        # IPv4 h1/h2 -> h3
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(3)])

        # IPv4 h3 -> h1/h2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.1'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(2)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.2'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(2)])

        # ARP to h3 -> s3
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.3'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(3)])

        # ARP to h1/h2 -> s1
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.1'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(2)])

        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.2'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(2)])

        print("Installed flows on s2")

    def install_s3(self, datapath):
        parser = datapath.ofproto_parser

        # s3 ports:
        # 1=h3, 2=s2, 3=s1 backup

        # IPv4 h1/h2 -> h3
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst='10.0.0.3'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(1)])

        # IPv4 h3 -> h1/h2 via s2
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.1'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(2)])

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src='10.0.0.3',
            ipv4_dst='10.0.0.2'
        )
        self.add_flow(datapath, 100, match, [parser.OFPActionOutput(2)])

        # ARP to h3 -> h3
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.3'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(1)])

        # ARP to h1/h2 -> s2
        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.1'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(2)])

        match = parser.OFPMatch(
            eth_type=0x0806,
            arp_tpa='10.0.0.2'
        )
        self.add_flow(datapath, 50, match, [parser.OFPActionOutput(2)])

        print("Installed flows on s3")
