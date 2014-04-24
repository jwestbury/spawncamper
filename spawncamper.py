#!/usr/bin/python
#nag_auto_add.py

# TODO: check templates.cfg in nagios dir for spawncamper-auto-add template,
# create if not there.

import argparse
import axfr
from netaddr import IPNetwork, IPAddress

parser = argparse.ArgumentParser(description="""Automatically adds hosts 
	to Nagios configurations, using AXFR zone transfers from a specified 
	DNS server""")

parser.add_argument('-z', '--zone', type=str, required=True, help="""DNS zone to query
	(e.g. internal.company.com)""")
parser.add_argument('-n', '--nameserver', required=True, help="""Nameserver against
	which to perform query""")
parser.add_argument('-c', '--subnet', help="""CIDR subnet in which monitored
	hosts reside. Cannot be used in conjunction with -s and -e.""")
parser.add_argument('-s', '--startip', help="""Must be used with -e. Defines
	the start point of an IP range in which monitored hosts reside. Cannot
	be used in conjunction with -c.""")
parser.add_argument('-e', '--endip', help="""Must be used with -s. Defines the
	end point of an IP range in which monitored hosts reside. Cannot be
	used in conjunction with -c.""")
parser.add_argument('-d', '--hostdirectory', help="""Nagios host configuration
	directory. nag_auto_add will not add new hosts if they already exist in
	a file within this directory. Default: /usr/local/nagios/etc/objects""",
	default="/usr/local/nagios/etc/objects")
parser.add_argument('-m', '--email', help="""Send e-mails to this address when
	new hosts are discovered.""")
args = parser.parse_args()

hostlist = axfr.transfer(args.zone, args.nameserver)

def host_match(matchtype):
	if matchtype == "cidr":
		suffix = str(args.subnet).split('/')[1] # get CIDR suffix
		targetnet = IPNetwork(args.subnet)	
		for name, ip in hostlist.items():
			ipnet = IPNetwork('%s/%s' % (ip, suffix))
			if ipnet == targetnet:
				print "%s is within the target subnet." % name
			else:
				print "%s is not within the target subnet." % name
	elif matchtype == "iprange":
		startip = IPAddress(args.startip)
		endip = IPAddress(args.endip)
		for name, ip in hostlist.items():
			ip = IPAddress(ip)
			if ip >= startip and ip <= endip:
				print "%s is within the target subnet." % name
			else:
				print "%s is not within the target subnet." % name
		
if args.subnet and (args.startip or args.endip):
	print "Cannot use -c with -s or -e. Please use -c or -s and -e."
	quit()
elif args.subnet:
	host_match("cidr")
elif args.startip and args.endip:
	host_match("iprange")
else:
	print "Matching for entire zone %s. Press Enter if you're sure." % args.zone
	raw_input()
