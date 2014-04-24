#!/usr/bin/env python
# encoding: utf-8
"""
axfr.py

Created by Stefan Schmidt on 2009-08-09.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
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
#from sys import argv

# domain = "visitors.har2009.net"
# n="87.76.11.14"
# script, domain, n = argv

def transfer(domain, n):
#	domain = ''
#	n = ''
#	myopts, args = getopt.getopt(argv[1:],"z:n:")
#	for opt, content in myopts:
#		if opt == '-z':
#			domain = content
#		elif opt == '-n':
#			n = content
#		else:
#			print "Usage: %s -z ZONE -ns NAMESERVER" % argv[0]
		
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
#				print name
#				print " " + str(rdataset[0]) + ""
				return(name, str(rdataset[0]))
