from random import random
from unittest import TestCase
import time
from dnslb import Monitor
from dnslb.check import check_http
import logging

__author__ = 'leifj'


class TestConnect(TestCase):

    def testConnect(self):
        mon = Monitor(['ac-sunet-1.nordu.net', 'ac-sunet-2.nordu.net'])
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect")
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect")
        mon.shutdown()
        print mon
        assert (mon.ok("ac-sunet-1.nordu.net") or mon.ok("ac-sunet-2.nordu.net"))

    def testEarlyShutdown(self):
        mon = Monitor(['ac-sunet-1.nordu.net', 'ac-sunet-2.nordu.net'])
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect")
        mon.schedule(check_http, vhost="connect.sunet.se", url="/_lvs.txt", match="connect")
        mon.halt()
        assert (not mon.ok("ac-sunet-1.nordu.net") or not mon.ok("ac-sunet-2.nordu.net"))

    def testConnectHttps(self):
        mon = Monitor(['www.ietf.org'])
        mon.schedule(check_http, vhost="www.ietf.org", url="/", match="IETF", use_tls=True)
        mon.shutdown()
        print mon
        assert (mon.ok("www.ietf.org"))
