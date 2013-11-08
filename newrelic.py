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

# File Name : test.py
# Creation Date : 11-06-2013
# Created By : Jamie Duncan
# Last Modified : Fri 08 Nov 2013 12:17:07 AM EST
# Purpose : 

import json
import psutil
import platform
import urllib2
import ConfigParser
import os
import sys

class NewRHELic:

    def __init__(self, debug=False):

        self.hostname = platform.node()
        self.debug = debug

        try:
            config_file = os.path.expanduser('~/.newrelic')
            config = ConfigParser.RawConfigParser()
            config.read(config_file)

            self.license_key = config.get('site', 'key')
            self.api_url = config.get('site', 'url')
            self.duration = config.getint('plugin', 'duration')
            self.guid = config.get('plugin', 'guid')
            self.name = config.get('plugin', 'name')

            if config.getboolean('plugin','enable_all') == True:
                self.enable_disk = True
                self.enable_net = True
                self.enable_mem = True
                self.enable_proc = True
            else:
                self.enable_disk = config.getboolean('plugin', 'enable_disk')
                self.enable_net = config.getboolean('plugin', 'enable_network')
                self.enable_mem = config.getboolean('plugin', 'enable_memory')
                self.enable_proc = config.getboolean('plugin', 'enable_proc')

            if self.enable_disk:
                self.disk_title = config.get('disk','title')
                self.disk_units = config.get('disk','units')

            if self.enable_net:
                self.net_title = config.get('network','title')
                self.net_interfaces = config.get('network','interfaces').split(',') #split them into a tuple so they can be evaluated

            if self.enable_mem:
                self.mem_title = config.get('memory','title')
                self.mem_units = config.get('memory', 'units')

            if self.enable_proc:
                self.proc_title = config.get('proc','title')
                self.proc_cpu_time_title = config.get('proc','cpu_time_title')
                self.proc_util_title = config.get('proc','cpu_util_title')
                self.proc_cpu_units = config.get('proc', 'cpu_units')

        except:
            print "Cannot Open Config File", sys.exc_info()[0]
            raise

    def _get_net_stats(self):
        '''This will form network IO stats for the entire system'''
        data = {}
        io = psutil.network_io_counters()

        for i in range(0,len(io)-1):
            title = "%s/%s[%s]" % (self.mem_title, io._fields[i], self.mem_units)
            data[title] = io[i]

        return data

    def _get_cpu_states(self):
        '''This will get CPU states as a percentage of time'''
        data = {}
        cpu_states = psutil.cpu_times_percent()

        for i in range(0, len(cpu_states)-1):
            title = "%s/%s[%s]" % (self.proc_cpu_time_title, cpu_states._fields[i], self.proc_cpu_units)
            data[title] = cpu_states[i]

        return data

    def _get_cpu_utilization(self):
        '''This will return per-CPU utilization'''
        data = {}
        cpu_util = psutil.cpu_percent(interval=0, percpu=True)

        for i in range(0, len(cpu_util)-1):
            title = "%s/%s[%s]" % (self.proc_util_title, cpu_util._fields[i], self.proc_cpu_units)
            data[title] = cpu_util[i]

        return data

    def _get_disk_utilization(self):
        '''This will return disk utilziation percentage for each mountpoint'''
        data = {}
        disks = psutil.disk_partitions() #all of the various partitions / volumes on a device
        for p in disks:
            title = "%s/%s[%s]" % (self.disk_title, p.mountpoint, self.disk_units)
            x = psutil.disk_usage(p.mountpoint)
            data[title] = x.percent

        return data




'''
#do some heavy lifting
io = psutil.network_io_counters()

# form the raw data up
data = {"agent": {
                    'host': hostname,
                    'pid': 1000,
                    'version': '0.1'
                    },
        "components": [{
                        'name': 'network_io_stats',
                        'guid':'com.cms.network_io',
                        'duration': 60,
                        'metrics': {
                            'Network IO Stats/bytes_sent[bytes]': io[0],
                            'Network IO Stats/[bytes]bytes_recv[bytes]': io[1],
                            'Network IO Stats/packets_sent[bytes]': io[2],
                            'Network IO Stats/packets_recv[bytes]': io[3],
                            'Network IO Stats/errin[bytes]': io[4],
                            'Network IO Stats/errout[bytes]': io[5],
                            'Network IO Stats/dropin[bytes]': io[6],
                            'Network IO Stats/dropout[bytes]': io[7]
                        }
                    }]
}

#create the urllib headers and form the http object
req = urllib2.Request(api_url)
req.add_header("X-License-Key", license_key)
req.add_header("Content-Type","application/json")
req.add_header("Accept","application/json")

json_data = json.dumps(data)
print "json encoded data: %s" % json_data
response = urllib2.urlopen(req, json_data)
print response.getcode()
'''
