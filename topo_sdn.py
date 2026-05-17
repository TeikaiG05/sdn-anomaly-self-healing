# -*- coding: utf-8 -*-

from mininet.topo import Topo
from mininet.link import TCLink

class SDNTopo(Topo):
    def build(self):
        # Hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')

        # Switches
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', protocols='OpenFlow13')

        # Host links
        self.addLink(h1, s1, cls=TCLink, bw=100, delay='1ms')
        self.addLink(h2, s1, cls=TCLink, bw=100, delay='1ms')
        self.addLink(h3, s3, cls=TCLink, bw=100, delay='1ms')
        self.addLink(h4, s2, cls=TCLink, bw=100, delay='1ms')

        # Main path
        self.addLink(s1, s2, cls=TCLink, bw=10, delay='5ms')
        self.addLink(s2, s3, cls=TCLink, bw=10, delay='5ms')

        # Backup path
        self.addLink(s1, s3, cls=TCLink, bw=20, delay='10ms')

topos = {'sdntopo': (lambda: SDNTopo())}
