#!/usr/bin/env python
#spawncamper.py

# TODO:
# Add in MAC address detection to avoid duplicate host entries -- use a
#    command-line option to decide whether a user wants to permit duplicate
#    entries (default: no duplicates).
# Allow for an exclusions file in user-specified location.

import argparse
import axfr
import os
import re
import smtplib
from netaddr import IPNetwork, IPAddress
from time import strftime
from shutil import copyfile
from sys import exit

def build_template(hostdirectory, templatefile):
    """Adds the Spawncamper template to Nagios templates config if it is not there already"""
    tf = open("%s/%s" % (hostdirectory, templatefile), 'a+')
    if not "spawncamper-host" in tf.read(): # double-check to see if the template exists
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
    name                          spawncamper-host
    notifications_enabled         0
    event_handler_enabled         1
    flap_detection_enabled        1
    process_perf_data             1
    retain_status_information     1
    retain_nonstatus_information  1
    register                      0
    }
        """
    
        tf.write(template)    
    
    tf.close()

def host_list(hostdirectory='/usr/local/nagios/etc/objects'):
    """Generates lists of host names and IPs in existing Nagios object definitions"""
    # two lists instead of a dict here because we don't need to do lookups
    hostobjectsbyname = []
    hostobjectsbyaddress = []
    exclusions = []
    for rootdir, dirnames, filenames in os.walk(hostdirectory):
        print "Check object defs in %s" % hostdirectory
        for file in filenames: # loop through our host def files
            if str(file).lower() == "exclusions": # no need to put these in our list
                continue
            fh = open("%s/%s" % (rootdir, file))
            for line in fh.readlines():
                # m1 gets the hostname from the object def, m2 gets the IP address
                m1 = re.search(r'^#*?\s+host_name\s+(\w+)\s*;?\w*?[\S\s]*?$', line)
                m2 = re.search(r'^#*?\s+address\s+([\d\.]+)\s*;?\w*?[\S\s]*?$', line)
                if m1:
                    hostobjectsbyname.append(m1.group(1).lower())
                    print "Found %s in object defs." % m1.group(1)
                elif m2:
                    hostobjectsbyaddress.append(m2.group(1))
                    print "Found %s in object defs." % m2.group(1)
            fh.close()
    fh = open("exclusions", 'r')
    for line in fh.readlines():
        exclusions.append(line.lower().rstrip('\r\n'))
    fh.close()
    return hostobjectsbyaddress, hostobjectsbyname, exclusions

def host_match(matchtype='cidr', hostlist=None, subnet=None, startip=None,
    endip=None, hostdirectory='/usr/local/nagios/etc/objects', iplist=None,
    namelist=None, exclusions=None):
    """Determines whether or not a host matches the specified criteria for addition to spawncamper.cfg"""
    foundhosts = []
    if matchtype == "cidr": # are we matching based on CIDR?
        suffix = str(subnet).split('/')[1] # get CIDR suffix
        targetnet = IPNetwork(subnet)
        for name, ip in hostlist.items():
            name = str(name).lower() # make sure we don't end up with case mismatches
            if name in exclusions:
                print "Found %s in exclusions list, skipping." % name
                continue
            ipnet = IPNetwork('%s/%s' % (ip, suffix)) # get the network this host IP is a part of
            if ipnet == targetnet: # is the host network our target network?
                if ip in iplist or name in namelist: # does this host's name or IP already exist in object defs?
                    print "%s matches, but already exists." % name
                else:
                    print ("%s matches and does not exist. Adding." % name)
                    write_host(name, ip, hostdirectory)
                    foundhosts.append(name)
            else:
                print "%s does not match." % name
    elif matchtype == "iprange": # are we matching based on an IP range?
        startip = IPAddress(startip)
        endip = IPAddress(endip)
        for name, ip in hostlist.items():
            name = str(name).lower() # make sure we don't end up with case mismatches
            ip = IPAddress(ip)
            if ip >= startip and ip <= endip: # is the IP in our specified range?
                if ip in iplist or name in namelist:
                    print "%s matches, but already exists." % name
                else:
                    print ("%s matches and does not exist. Adding." % name)
                    write_host(name, ip, hostdirectory)
                    foundhosts.add(name)
            else:
                print "%s is not within the target subnet." % name
    return foundhosts

def write_host(hostname, ip, hostdirectory):
    """Adds the specified host to spawncamper.cfg"""
    fh = open("%s/spawncamper.cfg" % hostdirectory, 'a+')
    fh.write("""
#define_host{
#    use        spawncamper-host
#    host_name    %s
#    address        %s
#    }

    """ % (hostname, ip))
        
def send_email(address=None, settings=None, hosts=None):
    if hosts and address:
        msg = "SUBJECT: Spawncamper report, generated %s\n\n" % strftime("%Y-%m-%d %H:%M")
        msg += "Spawncamper has added the following hosts to the spawncamper.cfg object defs:\n\n"
        for host in hosts:
            msg = msg + "\t%s\n" % host
        em = smtplib.SMTP_SSL(settings['server'], settings['port'])
        em.set_debuglevel(1) # debuglevel is binary - non-zero values provide all debug messages
        em.login(settings['username'], settings['password'])
        em.sendmail(settings['from'], address, msg)
        em.quit()
    elif hosts and not address:
        print "New hosts found, but no e-mail address specified."
    else:
        print "No new host list specified for e-mail."

def init_config():
    """Initializes the spawncamper SMTP config file."""
    dirname = os.path.dirname(os.path.realpath(__file__)) # gets the directory our script resides in
    if not os.path.isfile("%s/spawncamper.conf" % dirname): # only if it doesn't exist already!
        try:
            copyfile("%s/spawncamper.conf.example" % dirname, "%s/spawncamper.conf" % dirname)
            print "WARNING: It appears to be your first time running Spawncamper.",
            print "If you want to use e-mail functioanly, please edit spawncamper.conf",
            print "with parameters suitable to your environment. Press Enter to continue,",
            print "or press ctrl-c to exit and configure spawncamper.conf."
            raw_input()
        except KeyboardInterrupt:
            print "SIGINT detected, exiting."
            exit(0)
        except:
            try:
                fh = open("%s/spawncamper.conf" % dirname, 'a+')
                fh.write("server: smtp.gmail.com\n")
                fh.write("port: 465\n")
                fh.write("username: joejack\n")
                fh.write("from: user@example.tld\n")
                fh.write("password: password")
                fh.close()
            except:
                print "Could not open or create spawncamper.conf.",
                print "Please manually copy spawncamper.conf.example to spawncamper.conf.",
                print "Press Enter to quit."
                raw_input()
                exit()

    
def read_config(config=None):
    if config:
        cfg = open(config, 'r')
    else:
        cfg = open("spawncamper.conf", 'r')
    settings = {}
    for line in cfg.readlines():
        # settings.update([e.strip() for e in line.split(':')])
        l = [e.strip() for e in line.split(':')]
        settings[l[0]] = l[1]
    return settings

def main(args):
    init_config()
    build_template(args.hostdirectory, args.templatefile)
    hostlist = axfr.transfer(args.zone, args.nameserver)
    l1, l2, exclusions = host_list(args.hostdirectory)

    if args.configfile:
        settings = read_config(config = args.configfile)
    else:
        settings = read_config()
    if args.subnet and (args.startip or args.endip):
        print "Cannot use -c with -s or -e. Please use -c or -s and -e."
        exit()
    elif args.subnet:
        foundhosts = host_match(matchtype = "cidr", hostlist = hostlist,
            subnet = args.subnet, hostdirectory = args.hostdirectory,
            iplist = l1, namelist = l2, exclusions = exclusions)
    elif args.startip and args.endip:
        foundhosts = host_match(matchtype = "iprange", hostlist = hostlist,
            startip = args.startip, endip = args.endip,
            hostdirectory = args.hostdirectory, iplist = l1, namelist = l2,
            exclusions = exclusions)
    else:
        print ("Matching for entire zone %s. Press Enter if you're sure." % args.zone)
        raw_input()
    if args.email:
        send_email(address = args.email, settings = settings, hosts = foundhosts)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Automatically adds hosts
            to Nagios configurations, using AXFR zone transfers from a specified
            DNS server""")

    parser.add_argument('-z', '--zone', type=str, required=True,
    help="""DNS zone to query (e.g. internal.company.com)""")
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
    parser.add_argument('--configfile', help="""Specify alternate config file. 
    Default: spawncamper.conf""")
    args = parser.parse_args()

    main(args)
