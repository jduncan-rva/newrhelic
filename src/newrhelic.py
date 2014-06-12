#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# Copyright (C) 2013  Jamie Duncan (jamie.e.duncan@gmail.com)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# File Name : newrelic.py
# Creation Date : 11-06-2013
# Created By : Jamie Duncan
# Last Modified : Thu 12 Jun 2014 04:49:23 PM EDT
# Purpose : A RHEL/CentOS - specific OS plugin for New Relic

import json
import psutil
import urllib2
import ConfigParser
import os
import sys
import time
from subprocess import Popen, PIPE
import logging
import socket

class NewRHELic:

    def __init__(self, debug=False, conf='/etc/newrhelic.conf'):

        self.config_file = conf
        socket.setdefaulttimeout(5)

        #store some system info
        self.uname = os.uname()
        self.pid = os.getpid()
        self.hostname = self.uname[1]  #this will likely be Linux-specific, but I don't want to load a whole module to get a hostname another way
        self.kernel = self.uname[2]
        self.arch = self.uname[4]

        self.debug = debug

        self.json_data = {}     #a construct to hold the json call data as we build it

        self.first_run = True   #this is set to False after the first run function is called


        self.on_fedora = False
        distro_test = open('/etc/redhat-release','r')
        d_version = distro_test[0].split()[0]
        if d_version = 'Fedora':    #we're using Fedora, psutil is a different here.
            self.on_fedora = True

	#Various IO buffers
        self.buffers = {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'errin' : 0,
            'errout' : 0,
            'dropin': 0,
            'dropout': 0,
            'read_count': 0,
            'write_count': 0,
            'read_bytes': 0,
            'write_bytes': 0,
            'read_time': 0,
            'write_time': 0,
            'sin': 0,
            'sout': 0,
        }

        # Open the config and log files in their own try/except
        try:
            config = ConfigParser.RawConfigParser()
            config.read(self.config_file)
          
            logfilename = config.get('plugin','logfile')
            loglevel = config.get('plugin','loglevel')
            logging.basicConfig(filename=logfilename,
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s: %(message)s',
                    )
            self.logger = logging.getLogger(__name__)
            if self.debug:
                # DEBUG logs!
                console = logging.StreamHandler()
                formatter = logging.Formatter('%(levelname)-8s %(name)s:%(funcName)s: %(message)s')
                console.setLevel(logging.DEBUG)
                console.setFormatter(formatter)
                self.logger.addHandler(console)
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(loglevel)

        except Exception, e:
            # Might be nice to properly catch this and emit a nice message?
            # Can't depend on "logger" here
            raise e

        try:
            self.license_key = config.get('site', 'key')
            self.api_url = config.get('site', 'url')
            self.duration = config.getint('plugin', 'duration')
            self.guid = config.get('plugin', 'guid')
            self.name = config.get('plugin', 'name')
            self.version = config.get('plugin','version')
            self.enable_proxy = config.getboolean('proxy','enable_proxy')

            if self.enable_proxy:
                proxy_host = config.get('proxy','proxy_host')
                proxy_port = config.get('proxy','proxy_port')
                # These proxy_setttings will be used by urllib2
                self.proxy_settings = {
                        'http': '%s:%s' % (proxy_host, proxy_port),
                        'https': '%s:%s' % (proxy_host, proxy_port)
                }
                self.logger.info("Configured to use proxy: %s:%s" % (proxy_host, proxy_port))


            #create a dictionary to hold the various data metrics.
            self.metric_data = {}

            if config.getboolean('plugin','enable_all') == True:
                self.enable_disk = True
                self.enable_net = True
                self.enable_mem = True
                self.enable_proc = True
                self.enable_swap = True
                self.enable_nfs = True

            else:
                self.enable_disk = config.getboolean('plugin', 'enable_disk')
                self.enable_net = config.getboolean('plugin', 'enable_network')
                self.enable_mem = config.getboolean('plugin', 'enable_memory')
                self.enable_proc = config.getboolean('plugin', 'enable_proc')
                self.enable_swap = config.getboolean('plugin', 'enable_swap')
                self.enable_nfs = config.getboolean('plugin', 'enable_nfs')

            self._build_agent_stanza()

        except Exception, e:
            self.logger.exception(e)
            raise e

    def _get_boottime(self):
        try:
            '''a quick function to make uptime human-readable'''
            a = time.gmtime(psutil.BOOT_TIME)
            boottime = "%s-%s-%s %s:%s:%s" % (a.tm_mon, a.tm_mday, a.tm_year, a.tm_hour, a.tm_min, a.tm_sec)

            return boottime
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _get_sys_info(self):
        '''This will populate some basic system information
	### INPUT OTHER THAN INTEGERS IS CURRENLTLY NOT SUPPORTED BY NEW RELIC ###'''

        try:
            #self.metric_data['Component/System Information/Kernel[string]'] = self.kernel
            #self.metric_data['Component/System Information/Arch[string]'] = self.arch
            #self.metric_data['Component/System Information/Boot Time[datetime]'] = self._get_boottime()
            self.metric_data['Component/System Information/Process Count[process]'] = len(psutil.get_pid_list())
            self.metric_data['Component/System Information/Core Count[core]'] = psutil.NUM_CPUS
            self.metric_data['Component/System Information/Active Sessions[session]'] = len(psutil.get_users())
        except Exception, e:
            loging.exception(e)
            pass

    def _get_net_stats(self):
        '''This will form network IO stats for the entire system'''
        try:
            if self.on_fedora:
                io = psutil.net_io_counters()
            else:
                io = psutil.network_io_counters()

            for i in range(len(io)):
                title = "Component/Network/IO/%s[bytes]" % io._fields[i]
                val = io[i] - self.buffers[io._fields[i]]
                self.buffers[io._fields[i]] = io[i]
                self.metric_data[title] = val

        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_cpu_states(self):
        '''This will get CPU states as a percentage of time'''
        try:
            cpu_states = psutil.cpu_times_percent()

            for i in range(len(cpu_states)):
                title = "Component/CPU/State Time/%s[percent]" % cpu_states._fields[i]
                self.metric_data[title] = cpu_states[i]
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_cpu_utilization(self):
        '''This will return per-CPU utilization'''
        try:
            cpu_util = psutil.cpu_percent(interval=0, percpu=True)
            cpu_util_agg = psutil.cpu_percent(interval=0)

            self.metric_data['Component/CPU/Utilization/Aggregate[percent]'] = cpu_util_agg

            for i in range(len(cpu_util)):
                title = "Component/CPU/Utilization/Processor-%s[percent]" % i
                self.metric_data[title] = cpu_util[i]
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_cpu_load(self):
        '''returns the 1/5/15 minute load averages'''
        try:
            l = os.getloadavg()

            self.metric_data['Component/CPU/Load/1min[avg]'] = l[0]
            self.metric_data['Component/CPU/Load/5min[avg]'] = l[1]
            self.metric_data['Component/CPU/Load/15min[avg]'] = l[2]
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_disk_utilization(self):
        '''This will return disk utilziation percentage for each mountpoint'''
        try:
            disks = psutil.disk_partitions() #all of the various partitions / volumes on a device
            for p in disks:
                title = "Component/Disk/Utilization/%s[percent]" % p.mountpoint.replace('/','|')
                x = psutil.disk_usage(p.mountpoint)
                self.metric_data[title] = x.percent
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_disk_stats(self):
        '''this will show system-wide disk statistics'''
        try:
            d = psutil.disk_io_counters()

            for i in range(len(d)):
                if d._fields[i] == 'read_time' or d._fields[i] == 'write_time':         #statistics come in multiple units from this output
                    title = "Component/Disk/Read-Write Time/%s[ms]" % d._fields[i]
                    val = d[i]
                elif d._fields[i] == 'read_count' or d._fields[i] == 'write_count':
                    title = "Component/Disk/Read-Write Count/%s[integer]" % d._fields[i]
                    val = d[i] - self.buffers[d._fields[i]]
                    self.buffers[d._fields[i]] = d[i]
                else:
                    title = "Component/Disk/IO/%s[bytes]" % d._fields[i]
                    val = d[i] - self.buffers[d._fields[i]]
                    self.buffers[d._fields[i]] = d[i]

                self.metric_data[title] = val
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_mem_stats(self):
        '''this will return memory utilization statistics'''
        try:
            mem = psutil.virtual_memory()
            program = mem.total - mem.available
            self.metric_data['Component/Memory/IO/program[bytes]'] = program
            for i in range(len(mem)):
                if mem._fields[i] == 'percent':
                    title = "Component/Memory/Utilization/%s[percent]" % mem._fields[i]
                elif mem._fields[i] == 'active' or mem._fields[i] == 'inactive':
                    title = "Component/Memory/Recent Activity/%s[bytes]" % mem._fields[i]
                elif mem._fields[i] == 'total' or mem._fields[i] == 'used' or mem._fields[i] == 'available':
                    title = "Component/Memory/System Total/%s[bytes]" % mem._fields[i]
                else:
                    title = "Component/Memory/IO/%s[bytes]" % mem._fields[i]

                self.metric_data[title] = mem[i]
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_swap_stats(self):
        '''this will return swap information'''
        try:
            swap = psutil.swap_memory()
            for i in range(len(swap)):
                if swap._fields[i] == 'percent':
                    title = "Component/Swap/Utilization/%s[percent]" % swap._fields[i]
                    val = swap[i]
                elif swap._fields[i] == 'sin' or swap._fields[i] == 'sout':
                    title = "Component/Swap/IO/%s[bytes]" % swap._fields[i]
                    val = swap[i] - self.buffers[swap._fields[i]]
                    self.buffers[swap._fields[i]] = swap[i] 
                else:
                    title = "Component/Swap/IO/%s[bytes]" % swap._fields[i]
                    val = swap[i]

                self.metric_data[title] = val
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_nfs_mounts(self):
        '''this will return either a list of active NFS mounts, or False'''
        p = Popen(['/etc/init.d/netfs', 'status'], stdout=PIPE, stderr=PIPE)
        mnt_data = p.stdout.readlines()
        new_mnt_data = []
        for i in range(len(mnt_data)):
            if 'Active NFS mountpoints' not in mnt_data[i]: #if this exists, we remove it
                new_mnt_data.append(mnt_data[i].rstrip())
        return new_mnt_data

    def _get_nfs_info(self, volume):
        '''this will add NFS stats for a given NFS mount to metric_data'''
        try:
            p = Popen(['/usr/sbin/nfsiostat', '%s' % volume ], stdout=PIPE, stderr=PIPE)
            retcode = p.wait()
            statdict = []
            volname = 'Component/NFS%s/' % volume
            for i in iter(p.stdout.readline, ''):
                statdict.append(i.rstrip('/').rstrip())
            statdict.remove(statdict[0])

            nfs_data = {
                volname + 'Metrics/ops[sec]': float(statdict[3].split()[0]),
                volname + 'Metrics/rpcbklog[int]': float(statdict[3].split()[1]),
                volname + 'Read/ops[sec]': float(statdict[5].split()[0]),
                volname + 'Read/kb[sec]': float(statdict[5].split()[1]),
                volname + 'Read/ops[kb]': float(statdict[5].split()[2]),
                volname + 'Read/retrans[int]': int(statdict[5].split()[3]),
                volname + 'Time/Read/RTT/avg[ms]': float(statdict[5].split()[5]),
                volname + 'Time/Read/Execute Time/avg[ms]': float(statdict[5].split()[6]),
                volname + 'Write/writes[sec]': float(statdict[7].split()[0]),
                volname + 'Write/kb[sec]': float(statdict[7].split()[1]),
                volname + 'Write/ops[kb]': float(statdict[7].split()[2]),
                volname + 'Write/retrans[int]': int(statdict[7].split()[3]),
                volname + 'Time/Write/RTT/avg[ms]': float(statdict[7].split()[5]),
                volname + 'Time/Write/Execute Time/avg[ms]': float(statdict[7].split()[6]),
            }

            for k,v in nfs_data.items():
                self.metric_data[k] = v
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_nfs_stats(self):
        '''this is called to iterate through all NFS mounts on a system and collate the data'''
        try:
            mounts = self._get_nfs_mounts()
            if mounts > 0:
                for vol in mounts:
                    self._get_nfs_info(vol)
                    self.logger.debug("processing NFS volume - %s" % vol)
        except Exception, e:
            self.logger.exception(e)
            pass

    def _build_agent_stanza(self):
        '''this will build the 'agent' stanza of the new relic json call'''
        try:
            values = {}
            values['host'] = self.hostname
            values['pid'] = self.pid
            values['version'] = self.version

            self.json_data['agent'] = values
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _reset_json_data(self):
        '''this will 'reset' the json data structure and prepare for the next call. It does this by mimicing what happens in __init__'''
        try:
            self.metric_data = {}
            self.json_data = {}
            self._build_agent_stanza()
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _build_component_stanza(self):
        '''this will build the 'component' stanza for the new relic json call'''
        try:
            c_list = []
            c_dict = {}
            c_dict['name'] = self.hostname
            c_dict['guid'] = self.guid
            c_dict['duration'] = self.duration

            #always get the sys information
            self._get_sys_info()

            if self.enable_disk:
                self._get_disk_utilization()
                self._get_disk_stats()
            if self.enable_proc:
                self._get_cpu_utilization()
                self._get_cpu_states()
                self._get_cpu_load()
            if self.enable_mem:
                self._get_mem_stats()
            if self.enable_net:
                self._get_net_stats()
            if self.enable_swap:
                self._get_swap_stats()
            if self.enable_nfs:
                self._get_nfs_stats()

            c_dict['metrics'] = self.metric_data
            c_list.append(c_dict)

            self.json_data['components'] = c_list
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _prep_first_run(self):
        '''this will prime the needed buffers to present valid data when math is needed'''
        try:
            #create the first counter values to do math against for network, disk and swap
            if self.on_fedora:
                net_io = psutil.net_io_counters()
            else:
                net_io = psutil.network_io_counters()
            for i in range(len(net_io)):
                self.buffers[net_io._fields[i]] = net_io[i]

            disk_io = psutil.disk_io_counters()
            for i in range(len(disk_io)):
                self.buffers[disk_io._fields[i]] = disk_io[i]

            swap_io = psutil.swap_memory()
            for i in range(len(swap_io)):
                if swap_io._fields[i] == 'sin' or swap_io._fields[i] == 'sout':
                    self.buffers[swap_io._fields[i]] = swap_io[i]

            #then we sleep so the math represents 1 minute intervals when we do it next
            self.logger.debug("sleeping...")
            time.sleep(60)
            self.first_run = False
            self.logger.debug("The pump is primed")

            return True
        except Exception, e:
            self.logger.exception(e)
            raise e

    def add_to_newrelic(self):
        '''this will glue it all together into a json request and execute'''
        if self.first_run:
            self._prep_first_run()  #prime the data buffers if it's the first loop

        self._build_component_stanza()  #get the data added up
        try:
            if self.enable_proxy:
                proxy_handler = urllib2.ProxyHandler(self.proxy_settings)
                opener = urllib2.build_opener(proxy_handler)
            else:
                opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())

            request = urllib2.Request(self.api_url)
            request.add_header("X-License-Key", self.license_key)
            request.add_header("Content-Type","application/json")
            request.add_header("Accept","application/json")

            response = opener.open(request, json.dumps(self.json_data))

            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("%s (%s)" % (request.get_full_url(), response.getcode()))
                self.logger.debug(json.dumps(self.json_data))

            response.close()

        except urllib2.HTTPError, err:
            self.logger.error("HTTP Error: %s" % err)
            pass    #i know, i don't like it either, but we don't want a single failed connection to break the loop.

        except urllib2.URLError, err:
            self.logger.error("URL Error (DNS Error?): %s" % err)
            pass
        self._reset_json_data()
