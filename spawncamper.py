#!/usr/bin/python
#nag_auto_add.py

# TODO: Add host exclusion list

import argparse
import axfr
import re
import os
from netaddr import IPNetwork, IPAddress

# Intitialize lists
#hostobjectsbyaddress = ['0.0.0.0']
#hostobjectsbyname = ['@']

def build_template(hostdirectory, templatefile):
	"""Adds the Spawncamper template to Nagios templates config if it is not there already"""
	tf = open("%s/%s" % (hostdirectory, templatefile), 'a+')
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

def host_list(hostdirectory = '/usr/local/nagios/etc/objects'):
	"""Generates lists of host names and IPs in existing Nagios object definitions"""
	hostobjectsbyname = []
	hostobjectsbyaddress = []
	for rootdir, dirnames, filenames in os.walk(hostdirectory):
		print "Check object defs in %s" % hostdirectory
		for file in filenames:
			fh = open("%s/%s" % (rootdir, file))
			for line in fh.readlines():
				m1 = re.search(r'^#*?\s+host_name\s+(\w+)\s*;?\w*?[\S\s]*?$', line)
				m2 = re.search(r'^#*?\s+address\s+([\d\.]+)\s*;?\w*?[\S\s]*?$', line)
				if m1:
					hostobjectsbyname.append(m1.group(1).lower())
					print "Found %s in object defs." % m1.group(1)
				elif m2:
					hostobjectsbyaddress.append(m2.group(1))
					print "Found %s in object defs." % m2.group(1)
			fh.close()
	return hostobjectsbyaddress, hostobjectsbyname

def host_match(matchtype = 'cidr', hostlist = None, subnet = None, startip = None, endip = None, hostdirectory = '/usr/local/nagios/etc/objects', iplist = None, namelist = None):
	"""Determines whether or not a host matches the specified criteria for addition to spawncamper.cfg"""
	if matchtype == "cidr":
		suffix = str(subnet).split('/')[1] # get CIDR suffix
		targetnet = IPNetwork(subnet)	
		for name, ip in hostlist.items():
			name = str(name).lower()
			ipnet = IPNetwork('%s/%s' % (ip, suffix))
			if ipnet == targetnet:
				if ip in iplist or name in namelist:
					print "%s matches, but already exists." % name
				else:
					print "%s matches and does not exist. Adding." % name
					write_host(name, ip, hostdirectory)
			else:
				print "%s does not match." % name
	elif matchtype == "iprange":
		startip = IPAddress(startip)
		endip = IPAddress(endip)
		for name, ip in hostlist.items():
			name = str(name).lower()
			ip = IPAddress(ip)
			if ip >= startip and ip <= endip:
				if ip in iplist or name in namelist:
					print "%s matches, but already exists." % name
				else:
					print "%s matches and does not exist. Adding." % name
					write_host(name, ip, hostdirectory)
			else:
				print "%s is not within the target subnet." % name

def write_host(hostname, ip, hostdirectory):
	"""Adds the specified host to spawncamper.cfg"""
	fh = open("%s/spawncamper.cfg" % hostdirectory, 'a+')
	fh.write("""
#define_host{
#	use		spawncamper-host
#	host_name	%s
#	address		%s
#	}

	""" % (hostname, ip))
		
def main(args):
	# Show args to user
	print args

	build_template(args.hostdirectory, args.templatefile)
	hostlist = axfr.transfer(args.zone, args.nameserver)
	l1, l2 = host_list(args.hostdirectory)

	if args.subnet and (args.startip or args.endip):
		print "Cannot use -c with -s or -e. Please use -c or -s and -e."
		quit()
	elif args.subnet:
		host_match(matchtype = "cidr", hostlist = hostlist, subnet = args.subnet, hostdirectory = args.hostdirectory, iplist = l1, namelist = l2)
	elif args.startip and args.endip:
		host_match(matchtype = "iprange", hostlist = hostlist, startip = args.startip, endip = args.endip, hostdirectory = args.hostdirectory, iplist = l1, namelist = l2)
	else:
		print "Matching for entire zone %s. Press Enter if you're sure." % args.zone
		raw_input()

if __name__ == '__main__':
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

	main(args)
