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
# Last Modified : Fri 08 Nov 2013 02:41:16 PM EST
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
        self.version = 0.1

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

            if self.enable_swap:
                self.swap_title = config.get('swap','title')
                self.swap_units = config.get('swap','units')

            self._build_agent_stanza()

        except:
            print "Cannot Open Config File", sys.exc_info()[0]
            raise

    def _get_net_stats(self):
        '''This will form network IO stats for the entire system'''
        io = psutil.network_io_counters()

        for i in range(0,len(io)-1):
            title = "%s/%s[%s]" % (self.mem_title, io._fields[i], self.mem_units)
            self.metric_data[title] = io[i]

    def _get_cpu_states(self):
        '''This will get CPU states as a percentage of time'''
        cpu_states = psutil.cpu_times_percent()

        for i in range(0, len(cpu_states)-1):
            title = "%s/%s[%s]" % (self.proc_cpu_time_title, cpu_states._fields[i], self.proc_cpu_units)
            self.metric_data[title] = cpu_states[i]

    def _get_cpu_utilization(self):
        '''This will return per-CPU utilization'''
        cpu_util = psutil.cpu_percent(interval=0, percpu=True)

        for i in range(0, len(cpu_util)-1):
            title = "%s/CPU%s[%s]" % (self.proc_util_title, i, self.proc_cpu_units)
            self.metric_data[title] = cpu_util[i]

    def _get_disk_utilization(self):
        '''This will return disk utilziation percentage for each mountpoint'''
        disks = psutil.disk_partitions() #all of the various partitions / volumes on a device
        for p in disks:
            title = "%s/%s[%s]" % (self.disk_title, p.mountpoint.replace('/','&frasl;'), self.disk_units)
            x = psutil.disk_usage(p.mountpoint)
            self.metric_data[title] = x.percent

    def _get_mem_stats(self):
        '''this will return memory utilization statistics'''
        mem = psutil.virtual_memory()
        for i in range(0, len(mem)-1):
            if mem._fields[i] == 'percent':
                title = "%s/%s[percent]" % (self.mem_title, mem._fields[i])
            else:
                title = "%s/%s[%s]" % (self.mem_title, mem._fields[i], self.mem_units)

            self.metric_data[title] = mem[i]

    def _get_swap_stats(self):
        '''this will return swap information'''
        swap = psutil.swap_memory()
        for i in range(0, len(swap)-1):
            if swap._fields[i] == 'percent':
                title = "%s/%s[percent]" % (self.swap_title, swap._fields[i])
            else:
                title = "%s/%s[%s]" % (self.swap_title, swap._fields[i], self.swap_units)

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
        if self.enable_proc:
            self._get_cpu_utilization()
            self._get_cpu_states()
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
        response = urllib2.urlopen(self.req, json.dumps(self.json_data))
        self._reset_json_data()

        return response.getcode()
