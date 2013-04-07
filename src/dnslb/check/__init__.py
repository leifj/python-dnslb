import httplib
from ..exceptions import MonitorException
import logging

__author__ = 'leifj'


def check_http(host, vhost=None, url=None, match=None):
    logging.debug("HTTP connection to %s" % host)
    h = httplib.HTTPConnection(host)
    logging.debug("GET %s (vhost=%s)" % (url, vhost))
    h.request('GET', url, "", {'Host': vhost})
    resp = h.getresponse()
    logging.debug(resp.msg)
    if not resp.status == 200:
        raise MonitorException("%d %s" % (resp.status, resp.reason))

    if match is not None:
        body = resp.read()
        logging.debug("looking for %s in %s" % (match, body))
        return match in body or match == body
    else:
        return True

