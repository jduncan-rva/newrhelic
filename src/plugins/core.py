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

import psutil
import ConfigParser
import os
import sys
import time
from subprocess import Popen, PIPE
import logging
import socket

'''
newrhelic-core is a server plugin for New Relic that provides more granular reporting data than the default servers plugin
It has the following sections that can be enabled or disabled for inclusion in your New Relic Dashboards
disk    : Disk-usage statistics for each mountpoint
network : Network Statistics
memory  : Memory Statistics
proc    : CPU Statistics (per-cpu for some)
swap    : Swap Statistics (may be folded into memory down the road)
    
To enable: 
1) add 'core' to the plugin_list parameter in /etc/newrhelic.conf 
Example:

plugin_list = core,foo,bar

2) create a [core] config file section and tell the plugin which component you want enabled. 
Example:

[core]
enable_disk = True
enable_network = True
enable_memory = True
enable_proc = True
enable_swap = True
'''

class core:
    def __init__(self, conf='/etc/newrhelic.conf'):

        #store some system info
        self.uname = os.uname()
        self.pid = os.getpid()
        self.hostname = self.uname[1]  #this will likely be Linux-specific, but I don't want to load a whole module to get a hostname another way
        self.kernel = self.uname[2]
        self.arch = self.uname[4]
        self.config_file = conf

        self.first_run = True   #this is set to False after the first run function is called

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

        # adding in to solve the cpu percent time issue in RHEL 6
        self.cpu_buffers = dict()

        # Open the config and log files in their own try/except
        try:
            config = ConfigParser.RawConfigParser()
            config.read(self.config_file)

            logfilename = config.get('plugin','logfile')
            loglevel = 'logging.%s' % config.get('plugin','loglevel').upper()
            logging.basicConfig(filename=logfilename,
                level=eval(loglevel),
                format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s: %(message)s',
            )
            self.logger = logging.getLogger(__name__)
                  
        except Exception, e:
            # Might be nice to properly catch this and emit a nice message?
            # Can't depend on "logger" here
            raise e

        try:
            self.metric_data = dict()

            self.enable_disk = config.getboolean('core', 'enable_disk')            
            self.enable_net = config.getboolean('core', 'enable_network')
            self.enable_mem = config.getboolean('core', 'enable_memory')
            self.enable_proc = config.getboolean('core', 'enable_proc')
            self.enable_swap = config.getboolean('core', 'enable_swap')

        except Exception, e:
            self.logger.exception(e)
            raise e

        self._prep_first_run()

    def _prep_first_run(self):
        '''
        This will prime the pump for the initial run, so math looks good from the 
        outset. This is run as part of __init__()
        '''
        if self.enable_proc:    # we will prime the cpu buffers This can be refactored later to reuse code as part of _get_cpu_states
            t2 = psutil.cpu_times()._asdict()
            total_time = sum(t2.values())
            for field in t2.keys():
                try:
                    percentage = (100 * t2[field] / total_time)
                except ZeroDivisionError:
                    percentage = 0.0
                field_perc = round(percentage, 2)

                self.cpu_buffers[field] = t2[field]

            return True

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
            try:
                io = psutil.net_io_counters()
            except AttributeError:
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
        # This will get CPU states as a percentage of time
        # used to help calcuate percentage times in the cpu_times_percent function isn't available in psutil
        # due to the age of the version (affects RHEL 6 and older 
        # based on  https://github.com/giampaolo/psutil/blob/master/psutil/__init__.py#L1542-1609
        # since the math isn't too massive computationally, we'll use this universally for now
        # if this is rebased into RHEL 6 we may revisit it then - jduncan

        try:
            t2 = psutil.cpu_times()._asdict()
            all_delta = sum(t2.values()) - sum(self.cpu_buffers.values())
            for field in self.cpu_buffers.keys():
                field_delta = t2[field] - self.cpu_buffers[field]
                try:
                    field_perc = (100 * field_delta) / all_delta
                except ZeroDivisionError:
                    field_perc = 0.0
                field_perc = round(field_perc, 2)

                # now we add the rounded percentage data to the New Relic metrics for uploading
                title = "Component/CPU/State Time/%s[percent]" % field
                self.metric_data[title] =  field_perc

                # and finally set the buffer to the current values so the next time the math will be right
                self.cpu_buffers[field] = t2[field]
            
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

    def run(self):
        '''
        run() is the function called within the plugin to aggregate the data
        self.metric_data is the formatted JSON for the metrics stanza for a New Relic API POST.
        Each function called in run() should add a formatted entry into the self.metric_data dictionary.
        The primary app then aggregates those together and uploads them to New Relic
        '''
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

        return self.metric_data
