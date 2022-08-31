import ssl
from ..exceptions import MonitorException
import logging

__author__ = 'leifj'


class SNISSLContext(ssl.SSLContext):
  def __new__(cls, protocol, server_hostname, *args, **kwargs):
    return super().__new__(cls, protocol, *args, *kwargs)

  def __init__(self, protocol, server_hostname, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._server_hostname = server_hostname

  def wrap_socket(self, sock, *args, **kwargs):
    kwargs['server_hostname'] = self._server_hostname
    return super().wrap_socket(sock, *args, **kwargs)


def _check_http(host, vhost=None, url=None, match=None, use_tls=False, port=None):
    if use_tls:
        if port is None:
            port = 443
        logging.debug("HTTPS connection to %s" % host)
        context = SNISSLContext(ssl.PROTOCOL_TLS_CLIENT, vhost)
        context.load_default_certs()
        h = httplib.HTTPSConnection(host, port, context=context)
    else:
        if port is None:
            port = 80
        logging.debug("HTTP connection to %s:%d" % (host, port))
        h = httplib.HTTPConnection(host, port)
    logging.debug("GET %s (vhost=%s)" % (url, vhost))
    h.request('GET', url, "", {'Host': vhost})
    resp = h.getresponse()
    logging.debug("%d - %s" % (resp.status, resp.msg))
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
    import http.client as httplib
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
