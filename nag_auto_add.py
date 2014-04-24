#!/usr/bin/python
#nag_auto_add.py

import argparse
import axfr

parser = argparse.ArgumentParser(description="""Automatically adds hosts 
	to Nagios configurations, using AXFR zone transfers from a specified 
	DNS server""")

parser.add_argument('-z', '--zone', type=str, required=True, help="""DNS zone to query
	(e.g. internal.company.com)""")
parser.add_argument('-n', '--nameserver', required=True, help="""Nameserver against
	which to perform query""")
parser.add_argument('-c', '--subnet', help="""CIDR subnet in which monitored
	hosts reside. Cannot be used in conjunction with -s and -e.""")
parser.add_argument('-s', '--start-ip', help="""Must be used with -e. Defines
	the start point of an IP range in which monitored hosts reside. Cannot
	be used in conjunction with -c.""")
parser.add_argument('-e', '--end-ip', help="""Must be used with -s. Defines the
	end point of an IP range in which monitored hosts reside. Cannot be
	used in conjunction with -c.""")
parser.add_argument('-d', '--host-directory', help="""Nagios host configuration
	directory. nag_auto_add will not add new hosts if they already exist in
	a file within this directory. Default: /usr/local/nagios/etc/objects""",
	default="/usr/local/nagios/etc/objects")
args = parser.parse_args()

axfr.transfer(zone)


#DESCRIPTION
#	Queries a DNS server, performing an AXFR zone transfer to obtain a list
#	of hosts which may need to be monitored by Nagios. Takes arguments
#	for nameserver and DNS zone, and optional arguments to define 
#
#OPTIONS
#	-z	: DNS zone to query (e.g. internal.company.com)
#	-n	: Nameserver against which to perform query
#	-c	: CIDR subnet in which monitored hosts reside. Cannot be used
#		  in conjunction with options -s/e. (Default: All IPs.)
#	-s/e	: Starting and ending IP addresses, defining a range in which
#		  monitored hosts reside. Cannot be used in conjunction with
#		  option -c. (Default: All IPs.)
#	-h	: Nagios host configuration directory. nag_auto_add will not
#		  add new hosts if they already exist in a file within this
#		  directory. (Default: /usr/local/nagios/etc/objects)
#	-m	:Send updates to this address when hosts are discovered.
#"""
