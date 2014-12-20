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
# Last Modified : Thu 12 Jun 2014 07:37:14 PM EDT
# Purpose : A RHEL/CentOS - specific OS plugin for New Relic

import json
import psutil
import urllib2
from httplib import BadStatusLine
from ssl import SSLError
import ConfigParser
import os
import sys
import time
from subprocess import Popen, PIPE
import logging
import socket
import _version

class NewRHELic:

    def __init__(self, conf='/etc/newrhelic.conf'):

        self.guid = 'com.rhel.os_statistics'
        self.name = 'OS Statistics'
        self.version = _version.__version__
        self.api_url = 'https://platform-api.newrelic.com/platform/v1/metrics'
        self.config_file = conf
        socket.setdefaulttimeout(5)

        # store some system info
        self.uname = os.uname()
        self.pid = os.getpid()
        self.hostname = self.uname[1]  # this will likely be Linux-specific, but I don't want to load a whole module to get a hostname another way
        self.kernel = self.uname[2]
        self.arch = self.uname[4]

        self.json_data = dict()     # a construct to hold the json call data as we build it
        self.metric_data = dict()   # a dictionary to append all of the component data pieces to
        self.first_run = True       # this is set to False after the first run function is called

        try:
            config = ConfigParser.RawConfigParser()
            config.read(self.config_file)
          
            logfilename = config.get('plugin','logfile')
            loglevel = config.get('plugin','loglevel').upper()
            logging.basicConfig(filename=logfilename,
                level=eval('logging.%s' % loglevel),
                format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s: %(message)s',
            )
            self.logger = logging.getLogger(__name__)

        except Exception, e:
            # Might be nice to properly catch this and emit a nice message?
            # Can't depend on "logger" here
            raise e

        try:
            # Before we do anything else, we look to make sure we have at least one 
            # plugin enabled
            try:
                raw_plugin_list = config.get('plugin', 'plugin_list')
                self.enabled_plugins_list = raw_plugin_list.split(',')

            except ConfigParser.NoOptionError, e:
                self.logger.exception("No Plugins Enabled: %s" % e)
                raise e

            self.plugins = self._load_plugins()

            self.license_key = config.get('site', 'key')
            self.pid_file = config.get('plugin', 'pidfile')
            self.interval = config.getint('plugin', 'interval')
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

            self._build_agent_stanza()

        except Exception, e:
            self.logger.exception(e)
            raise e

    def _import_plugins(self):
        ''' 
        an INCREDIBLY simple plugin loader 
        it looks in the plugins directory, and gives access to the submodules 
        that are listed out in the enabled_plugins entry in /etc/newrhelic.conf
        these are loaded with the _load_plugins() function
        '''
        try:
            p = __import__('plugins', globals(), locals(), self.enabled_plugins_list, -1)
            
            return p
                
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _load_plugins(self):
        '''
        This is the function that actually loads a plugin and makes it usable by the system
        Since this is an incredibly simplistic system, it has some strict requirements:
        location - all plugins must be located in the 'plugins' directory
        naming - using the core plugin as an example:
        this should be valid:

        from plugins import core
        x = core.core()
        x.run()
        
        The plugin architecture uses the above naming convention to load the plugin modules and create instances
        Each plugin has it's own class instance that is persisted as long as the daemon is running.
        That allows for counters and other things that require comparison to the previous values to occur within
        the plugin module
        '''
        try:
            #initiate some strings to hold things
            p_strings = list()
            data = list()

            # run through each of the enabled plugins
            for m in self.enabled_plugins_list:
                x = "plugin.%s.%s()" % (m,m)    # format it to something like "plugin.core.core"
                p_strings.append(x)

            plugin = self._import_plugins()     # we import the plugins module and its submodules
            for mod in p_strings:
                data.append(eval(mod))          # we create an instance of each module and create

            return data     # we return the list of all the instantiated plugins

        except AttributeError, e:
            self.logger.warning("Unable to load Plugin: %s" % mod)
            self.logger.exception(e)
            raise e

        except Exception, e:
            self.logger.exception(e)
            raise e

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
            self.metric_data = dict()
            self.json_data = dict()
            self._build_agent_stanza()
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _build_component_stanza(self):
        '''this will build the 'component' stanza for the new relic json call'''
        try:
            c_list = list()
            c_dict = dict()
            c_dict['name'] = self.hostname
            c_dict['guid'] = self.guid
            c_dict['duration'] = self.interval

            # This is where we run through our plugins and create the metric data that we want to upload
            for p in self.plugins:
                data = p.run()
                for x in data.keys():
                    self.metric_data[x] = data[x] 

            c_dict['metrics'] = self.metric_data
            c_list.append(c_dict)

            self.json_data['components'] = c_list
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _prep_first_run(self):
        '''this will prime the needed buffers to present valid data when math is needed'''
        try:
            for p in self.plugins:
                p.run()

            # Then we sleep so the math represents 1 minute intervals when we do it next
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

            self.logger.debug("%s (%s)" % (request.get_full_url(), response.getcode()))
            self.logger.debug(json.dumps(self.json_data))

            response.close()

        # We've tried to add the data. Now to account for any specific exceptions that could break the agent
        # that we would like to avoid.
        # The goal is to not let a single loss of a data point break the agent and force an service restart
        except urllib2.HTTPError, err:
            self.logger.error("HTTP Error: %s" % err)
            pass    #i know, i don't like it either, but we don't want a single failed connection to break the loop.

        except urllib2.URLError, err:
            self.logger.error("URL Error (DNS Error?): %s" % err)
            pass

        except BadStatusLine, err:
            # ran into this error on a test system 
            # I believe it was the ghost in the machine we never found last year.
            # fixed with #23
            self.logger.error("HTTP Connection Closed Prematurely: %s" % err)
            pass

        except SSLError, err:
            # another lower-level exception caught in a test system
            # fixed with #25
            self.logger.error("SSL Read Error: %s" % err)
            pass

        self._reset_json_data()
