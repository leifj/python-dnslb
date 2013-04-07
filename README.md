Python DNS LB & Traffic Director
================================

This snippet of python is meant to be used with https://github.com/abh/geodns - a geo-aware
DNS server in GO. The idea is to monitor a set of services and periodically generate a JSON
zone based on the service instances that are up and responding correctly. This can be used
as a poor-mans "global dns load balancer".

Installation
------------

	pip install python-dlslb

or 

	git clone https://github.com/leifj/python-dnslb
	cd python-dnslb
	./setup.py install


Running
-------

Create a yaml-file somewhere (lets call it example.com.yaml):

```yaml
hosts:
	host-1:
		- 1.2.3.4
	host-2:
		- 1.2.3.5
		- 1.2.4.1
aliases:
	- www
labels:
	- host-1
		- north-america
	- host-2
		- europe
checks:
	- check_http:
		  vhost: "www.example.com"
		url: "/"
```

Then run the following command:

	dnslb --loglevel=DEBUG -z example.com.json -c example.com.yaml

The monitor will startup and connect to each IP address listed for all hosts in the
hosts table, issuing a GET request for '/' with the Host header set to www.example.com
Periodically the monitor will write a json zonefile to example.com.json. The zonefile
will always list A and AAAA recoreds for the hosts but will only list A and AAAA for
the zone (example.com in our case) and for each label for those addresses that passes
the test (check_http in this case).

The zonefile can be fed directly into geodns.

