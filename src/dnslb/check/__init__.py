from ..exceptions import MonitorException
import logging

__author__ = 'leifj'


def _check_http(host, vhost=None, url=None, match=None, use_tls=False, port=None):
    if use_tls:
        if port is None:
            port = 443
        logging.debug("HTTPS connection to %s:%d" % (host,port))
        h = httplib.HTTPSConnection("{0}:{1}".format(host,port), context=ssl._create_unverified_context())
    else:
        if port is None:
            port = 80
        logging.debug("HTTP connection to %s:%d" % (host,port))
        h = httplib.HTTPConnection("{0}:{1}".format(host,port))
    logging.debug("GET %s (vhost=%s)" % (url, vhost))
    h.request('GET', url, "", {'Host': vhost})
    resp = h.getresponse()
    logging.debug("%d - %s" % (resp.status,resp.msg))
    if not resp.status == 200:
        raise MonitorException("%d %s" % (resp.status, resp.reason))

    if match is not None:
        body = resp.read()
        logging.debug("looking for %s in %s" % (match, body))
        return match in body or match == body
    else:
        return True

check_http = None
try: 
    import ssl
    import httplib
    check_http = _check_http
except ImportError:
    logging.debug("Missing httplib - not providing check_http")


def _check_xmpp(host, port=5222, jid=None, password=None):
    logging.debug("XMPP connection to %s" % host)
    jID = xmpp.protocol.JID(jid)
    cl = xmpp.Client((host, port), debug=[])
    connection = cl.connect()
    if not connection:
        raise MonitorException("Unable to connect to %s" % host)
    auth = cl.auth(jID.getNode(), password, jID.getResource())
    if not auth:
        raise MonitorException("Authentication failed")
    return True

check_xmpp = None
try:
    import xmpp 
    check_xmpp = _check_xmpp
except ImportError:
    logging.debug("Missing xmpppy - not providing check_xmpp")
