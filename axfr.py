#!/usr/bin/env python
# encoding: utf-8
"""
axfr.py

Created by Stefan Schmidt on 2009-08-09.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

Last updated by James Westbury, 4/23/2014

CHANGELOG
4/23/2014
--Moved main functionality into subroutine, transfer()
---takes two arguments, DNS zone and nameserver
---returns a dictionary containing hostnames as keys and IPs as values
"""

import sys
import getopt
import os
import dnspython.query
import dnspython.zone
import dnspython.rdatatype
import dnspython.resolver
import dnspython.query
import dnspython.zone
from dnspython.exception import DNSException
from dnspython.rdataclass import IN
from dnspython.rdatatype import A

def transfer(domain, n):
	hostlist = {}
	print "Getting NS records for", domain
	answers = dnspython.resolver.query(domain, 'NS')
	print "\nTrying a zone transfer for %s from name server %s" % (domain, n)
	try:
		zone = dnspython.zone.from_xfr(dnspython.query.xfr(n, domain))
	except DNSException, e:
		print e.__class__, e
	for name, node in zone.nodes.items():
		rdatasets = node.rdatasets
		for rdataset in rdatasets:
			if rdataset.rdclass == IN and rdataset.rdtype is A:
				hostlist[name] = str(rdataset[0])
	return hostlist
