from random import random
from unittest import TestCase
import time
from dnslb import Monitor
from dnslb.check import check_http
import logging

__author__ = 'leifj'


class TestConnect(TestCase):

    def testConnect(self):
        mon = Monitor(['connect01.acp.sunet.se', 'connect02.acp.sunet.se'])
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect.sunet.se")
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect.sunet.se")
        mon.shutdown()
        print mon
        assert (mon.ok("connect01.acp.sunet.se") or mon.ok("connect02.acp.sunet.se"))

    def testEarlyShutdown(self):
        mon = Monitor(['connect01.acp.sunet.se', 'connect02.acp.sunet.se'])
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect.sunet.se")
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect.sunet.se")
        mon.halt()
        assert (not mon.ok("connect01.acp.sunet.se") or not mon.ok("connect02.acp.sunet.se"))
