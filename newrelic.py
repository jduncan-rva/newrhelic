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
# Last Modified : Sat 09 Nov 2013 02:38:46 PM EST
# Purpose : A RHEL/CentOS - specific OS plugin for New Relic

import json
import psutil
import urllib2
import ConfigParser
import os
import sys

class NewRHELic:

    def __init__(self, debug=False):

        self.hostname = os.uname()[1]   #this will likely be Linux-specific, but I don't want to load a whole module to get a hostname another way
        self.debug = debug

        self.json_data = {}     #a construct to hold the json call data as we build it

        try:
            config_file = os.path.expanduser('~/.newrelic')
            config = ConfigParser.RawConfigParser()
            config.read(config_file)

            self.license_key = config.get('site', 'key')
            self.api_url = config.get('site', 'url')
            self.duration = config.getint('plugin', 'duration')
            self.guid = config.get('plugin', 'guid')
            self.name = config.get('plugin', 'name')
            self.version = config.get('plugin','version')

            self.req = urllib2.Request(self.api_url)
            self.req.add_header("X-License-Key", self.license_key)
            self.req.add_header("Content-Type","application/json")
            self.req.add_header("Accept","application/json")

            #create a dictionary to hold the various data metrics.
            self.metric_data = {}

            if config.getboolean('plugin','enable_all') == True:
                self.enable_disk = True
                self.enable_net = True
                self.enable_mem = True
                self.enable_proc = True
                self.enable_swap = True
            else:
                self.enable_disk = config.getboolean('plugin', 'enable_disk')
                self.enable_net = config.getboolean('plugin', 'enable_network')
                self.enable_mem = config.getboolean('plugin', 'enable_memory')
                self.enable_proc = config.getboolean('plugin', 'enable_proc')
                self.enable_swap = config.getboolean('plugin', 'enable_swap')

            if self.enable_disk:
                self.disk_title = config.get('disk','title')

            if self.enable_net:
                self.net_title = config.get('network','title')
                self.net_interfaces = config.get('network','interfaces').split(',') #split them into a tuple so they can be evaluated

            if self.enable_mem:
                self.mem_title = config.get('memory','title')

            if self.enable_proc:
                self.proc_title = config.get('proc','title')
                self.proc_cpu_time_title = config.get('proc','cpu_time_title')
                self.proc_util_title = config.get('proc','cpu_util_title')

            if self.enable_swap:
                self.swap_title = config.get('swap','title')

            self._build_agent_stanza()

        except:
            print "Cannot Open Config File", sys.exc_info()[0]
            raise

    def _get_net_stats(self):
        '''This will form network IO stats for the entire system'''
        io = psutil.network_io_counters()

        for i in range(0,len(io)-1):
            title = "Component/%s/%s[bytes]" % (self.mem_title, io._fields[i])
            self.metric_data[title] = io[i]

    def _get_cpu_states(self):
        '''This will get CPU states as a percentage of time'''
        cpu_states = psutil.cpu_times_percent()

        for i in range(0, len(cpu_states)-1):
            title = "Component/%s/%s[percent]" % (self.proc_cpu_time_title, cpu_states._fields[i])
            self.metric_data[title] = cpu_states[i]

    def _get_cpu_utilization(self):
        '''This will return per-CPU utilization'''
        cpu_util = psutil.cpu_percent(interval=0, percpu=True)

        for i in range(0, len(cpu_util)-1):
            title = "Component/%s/CPU%s[percent]" % (self.proc_util_title, i)
            self.metric_data[title] = cpu_util[i]

    def _get_cpu_load(self):
        '''returns the 1/5/15 minute load averages'''
        l = os.getloadavg()

        self.metric_data['Component/CPU Load-1min[avg]'] = l[0]
        self.metric_data['Component/CPU Load-5min[avg]'] = l[1]
        self.metric_data['Component/CPU Load-15min[avg]'] = l[2]

    def _get_disk_utilization(self):
        '''This will return disk utilziation percentage for each mountpoint'''
        disks = psutil.disk_partitions() #all of the various partitions / volumes on a device
        for p in disks:
            title = "Component/%s/%s[percent]" % (self.disk_title, p.mountpoint.replace('/','root-'))
            x = psutil.disk_usage(p.mountpoint)
            self.metric_data[title] = x.percent

    def _get_disk_stats(self):
        '''this will show system-wide disk statistics'''
        d = psutil.disk_io_counters()

        for i in range(0,len(d)-1):
            if d._fields[i] == 'read_time' or d._fields[i] == 'write_time':         #statistics come in multiple units from this output
                title = "Component/%s/%s[ms]" % (self.disk_title, d._fields[i])
            elif d._fields[i] == 'read_count' or d._fields[i] == 'write_count':
                title = "Component/%s/%s[integer]" % (self.disk_title, d._fields[i])
            else:
                title = "Component/%s/%s[bytes]" % (self.disk_title, d._fields[i])
            self.metric_data[title] = d[i]

    def _get_mem_stats(self):
        '''this will return memory utilization statistics'''
        mem = psutil.virtual_memory()
        for i in range(0, len(mem)-1):
            if mem._fields[i] == 'percent':
                title = "Component/%s/%s[percent]" % (self.mem_title, mem._fields[i])
            else:
                title = "Component/%s/%s[bytes]" % (self.mem_title, mem._fields[i])

            self.metric_data[title] = mem[i]

    def _get_swap_stats(self):
        '''this will return swap information'''
        swap = psutil.swap_memory()
        for i in range(0, len(swap)-1):
            if swap._fields[i] == 'percent':
                title = "Component/%s/%s[percent]" % (self.swap_title, swap._fields[i])
            else:
                title = "Component/%s/%s[bytes]" % (self.swap_title, swap._fields[i])

            self.metric_data[title] = swap[i]

    def _build_agent_stanza(self):
        '''this will build the 'agent' stanza of the new relic json call'''
        values = {}
        values['host'] = self.hostname
        values['pid'] = 1000
        values['version'] = self.version

        self.json_data['agent'] = values

    def _reset_json_data(self):
        '''this will 'reset' the json data structure and prepare for the next call. It does this by mimicing what happens in __init__'''
        self.json_data = {}
        self._build_agent_stanza()

    def _build_component_stanza(self):
        '''this will build the 'component' stanza for the new relic json call'''
        c_list = []
        c_dict = {}
        c_dict['name'] = self.hostname
        c_dict['guid'] = self.guid
        c_dict['duration'] = self.duration

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

        c_dict['metrics'] = self.metric_data
        c_list.append(c_dict)

        self.json_data['components'] = c_list

    def add_to_newrelic(self):
        '''this will glue it all together into a json request and execute'''
        self._build_component_stanza()  #get the data added up
        try:
            response = urllib2.urlopen(self.req, json.dumps(self.json_data))
            if self.debug:
                print response.getcode()
                print json.dumps(self.json_data)
            response.close()
        except urllib2.HTTPError, err:
            if self.debug:
                print err.code
                print json.dumps(self.json_data)
            pass    #i know, i don't like it either, but we don't want a single failed connection to break the loop.
        except urllib2.URLError, err:
            if self.debug:
                print err   #this error will kick if you lose DNS resolution briefly. We'll keep trying.
            pass
        self._reset_json_data()
