import Queue
from collections import deque
import getopt
from itertools import chain
import json
import logging
import os
from random import random
import tempfile
from threading import Thread
from datetime import datetime, time
from time import sleep, gmtime, strftime
import traceback
import sys
from threadpool import ThreadPool, NoResultsPending, WorkRequest, NoWorkersAvailable
import yaml
from dnslb.check import check_http


__author__ = 'leifj'


class Node(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self.status = deque([], 5)

    def __str__(self):
        return "%s (%s)" % (self.hostname, ",".join("%s" % s[1] for s in self.status))

    def add_status(self, ok=True, reason=None, exc=None):
        self.status.appendleft([datetime.now(), ok, reason, exc])

    @property
    def ok(self):
        if not self.status:
            return False
        else:
            return self.status[0][1]


class Monitor(Thread):
    def __init__(self, hosts, mult=2, timeout=10, sleep_time=1):
        super(Monitor, self).__init__()
        self.num_workers = mult * len(hosts)
        self.pool = ThreadPool(self.num_workers)
        self.nodes = {}
        for host in hosts:
            self.nodes[host] = Node(host)
        self.timeout = timeout
        self.running = True
        self.stop = False
        self.remaining = 0
        self.sleep_time = sleep_time
        self.num_started = 0
        self.num_fail = 0
        self.num_ok = 0
        self.start()

    def ok(self, hostname):
        return self.nodes[hostname].ok

    @property
    def num_processed(self):
        return self.num_ok + self.num_fail

    def __str__(self):
        return "<Monitor " + ",".join(["%s" % n for n in self.nodes.values()]) + ">"

    def _test_result(self, req, res):
        self.remaining -= 1
        try:
            hostname = req.args[0]
            logging.debug("result for %s(%s): %s" % (hostname, req.callable, res))
            node = self.nodes[hostname]
            if res:
                self.num_ok += 1
                node.add_status(True)
            else:
                self.num_fail += 1
                node.add_status(False, "check failed")
        except Exception, ex:
            logging.warning(ex)
            pass

    def _test_fail(self, req, exc_info):
        try:
            self.remaining -= 1
            logging.debug("_test_fail %s" % repr(req))
            traceback.print_exception(*exc_info)
            hostname = req.args[0]
            node = self.nodes[hostname]
            self.num_fail += 1
            node.add_status(False, "caught exception", exc_info)
        except Exception, ex:
            logging.warning(ex)
            pass

    def schedule(self, check_callable, **kwargs):
        for node in self.nodes.values():
            req = WorkRequest(check_callable,
                              [node.hostname],
                              kwds=kwargs,
                              callback=self._test_result,
                              exc_callback=self._test_fail)
            try:
                logging.debug("adding new request for %s on %s using %s" % (check_callable, node.hostname, kwargs))
                self.pool.putRequest(req, timeout=self.timeout)
                self.num_started += 1
                self.remaining += 1
            except Queue.Full:
                logging.warning("Unable to schedule service check for %s (queue full)." % node.hostname)

    def halt(self):
        self.running = False
        self.join()

    def shutdown(self):
        self.stop = True
        self.join()

    def wait(self):
        if self.pool.workRequests:
            self.pool.wait()

    def run(self):
        logging.info("Starting up!"
                     "")
        while self.running:
            try:
                if self.stop:
                    logging.debug("waiting for all %d remaining tasks..." % self.remaining)
                    self.pool.wait()
                    logging.debug("now %d" % self.remaining)
                    if self.remaining == 0:
                        self.running = False
                else:
                    self.pool.poll(block=False)
            except KeyboardInterrupt:
                logging.info("Shutting down...")
                self.stop = True
            except NoResultsPending:
                sleep(self.sleep_time)
                pass
            except Exception, ex:
                logging.error(ex)
        if self.stop:
            assert (self.remaining == 0)
        self.pool.dismissWorkers(self.num_workers, do_join=True)
        return True

    def dns_zone(self, contact, nameservers, config):
        zone = dict()
        zone['ttl'] = 120
        zone['serial'] = int(strftime("%Y%M%d00", gmtime()))
        zone['contact'] = contact
        zone['max_hosts'] = 2

        ns = dict()
        for n in nameservers:
            ns[n] = None
        zone['data'] = {'': {'ns': ns}}

        def _add_addr(ip, cn_a):
            if '.' in ip:
                cn_a['a'].append([ip, "100"])
            elif ':' in ip:
                cn_a['aaaa'].append([ip, "100"])
            else:
                raise Exception("Unknown address format %s" % ip)

        for v in config['aliases']:
            zone['data'][v] = dict(alias="")

        vn_a = dict(a=[], aaaa=[])
        for cn in config['hosts'].keys():
            zone['data'].setdefault(cn, {})

            cn_a = dict(a=[], aaaa=[])
            for ip in config['hosts'][cn]:
                _add_addr(ip, cn_a)
                if self.ok(ip):
                    _add_addr(ip, vn_a)
                else:
                    logging.warn("Excluding (%s) %s - not ok" % (cn, ip))
            zone['data'][cn] = cn_a
            for vn in config['labels'][cn]:
                zone['data'][vn] = vn_a

        if len(vn_a['a']) > 0:
            zone['data']['']['a'] = vn_a['a']

        if len(vn_a['aaaa']) > 0:
            zone['data']['']['aaaa'] = vn_a['aaaa']

        return json.dumps(zone)


def safe_write(fn, data):
    tmpn = None
    try:
        dirname, basename = os.path.split(fn)
        with tempfile.NamedTemporaryFile('w', delete=False, prefix=".%s" % basename, dir=dirname) as tmp:
            tmp.write(data)
            tmpn = tmp.name
        if os.path.exists(tmpn) and os.stat(tmpn).st_size > 0:
            os.rename(tmpn, fn)
            return True
    except Exception, ex:
        logging.error(ex)
    finally:
        if tmpn is not None:
            try:
                os.unlink(tmpn)
            except Exception:
                pass
    return False


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hz:c:', ['help', 'loglevel=', 'logfile=', 'zone', 'config'])
    except getopt.error, msg:
        print msg
        print 'for help use --help'
        sys.exit(2)

    config_file = 'gdlb.yaml'
    zone_file = 'zone.json'
    logfile = None
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__
            sys.exit(0)
        elif o in '--loglevel':
            loglevel = getattr(logging, a.upper(), None)
            if not isinstance(loglevel, int):
                raise ValueError('Invalid log level: %s' % loglevel)
        elif o in '--logfile':
            logfile = a
        elif o in ('--config', '-c'):
            config_file = a
        elif o in ('--zone', '-z'):
            zone_file = a

    log_args = {'level': loglevel}
    if logfile is not None:
        log_args['filename'] = logfile
    logging.basicConfig(**log_args)

    config = None
    with open(config_file) as fd:
        config = yaml.safe_load(fd)

    mon = Monitor(list(chain.from_iterable(config['hosts'].values())), sleep_time=2)  # just monitor one address
    while True:
        try:
            for ch in config['checks']:
                for check_name, kwargs in ch.iteritems():
                    mon.schedule(getattr(check, check_name), **kwargs)
                s = int(random() * 10)
                sleep(s)

            if mon.num_processed > 0:
                zone = mon.dns_zone('leifj.mnt.se', ['ns1', 'ns2'], config)
                safe_write(zone_file, zone)

            sleep(60 * random())
        except KeyboardInterrupt:
            mon.halt()
            break
