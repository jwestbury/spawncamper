#!/usr/bin/python
#nag_auto_add.py

# TODO: Add host exclusion list

import argparse
import axfr
import re
import os
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
parser.add_argument('-t', '--templatefile', help="""Nagios template file
	name. Default: templates.cfg.""", default="templates.cfg")
parser.add_argument('-m', '--email', help="""Send e-mails to this address when
	new hosts are discovered.""")
args = parser.parse_args()

hostlist = axfr.transfer(args.zone, args.nameserver)

# Show args to user
print args

# Check to see if spawncamper template already exists
tf = open("%s/%s" % (args.hostdirectory, args.templatefile), 'a+')
if not "spawncamper-host" in tf.read():
	template = """
###############################################################################
###############################################################################
#
# SPAWNCAMPER
#
###############################################################################
###############################################################################

# Template for hosts automatically added using spawncamper.py

define host{
	name				spawncamper-host
	notifications_enabled		0
	event_handler_enabled		1
	flap_detection_enabled		1
	process_perf_data		1
	retain_status_information	1
	retain_non_status_information	1
	register			0
	}
	"""
	
	tf.write(template)

tf.close()

# Get a list of hosts already in the object definitions
hostobjects = []

for rootdir, dirnames, filenames in os.walk(args.hostdirectory):
	for file in filenames:
		fh = open("%s/%s" % (rootdir, file))
		for line in fh.readlines():
			m = re.search(r'^\s+host_name\s+(\w+)\s*;?\w*?[\S\s]*?$', line)
			if m:
				hostobjects.append(m.group(1).lower())
		fh.close()

# Function to match hosts based on user-specified match type
def host_match(matchtype):
	fh = open("%s/spawncamper.cfg" % args.hostdirectory, 'a+')
	if matchtype == "cidr":
		suffix = str(args.subnet).split('/')[1] # get CIDR suffix
		targetnet = IPNetwork(args.subnet)	
		for name, ip in hostlist.items():
			name = str(name).lower()
			ipnet = IPNetwork('%s/%s' % (ip, suffix))
			if ipnet == targetnet:
				if name in hostobjects:
					print "%s matches, but already exists." % name
				else:
					print "%s matches and does not exist. Adding." % name
					fh.write("""
#define_host{
#	use		spawncamper-host
#	host_name	%s
#	address		%s
#	}

					""" % (name, ip))
			else:
				print "%s does not match." % name
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
