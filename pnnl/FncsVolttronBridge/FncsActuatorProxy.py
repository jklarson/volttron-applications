#!env/bin/python
# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2015, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}
import sys
import logging
from volttron.platform.messaging import headers as headers_mod, topics
from volttron.platform.vip.agent import Agent, PubSub, Core, RPC
from volttron.platform.agent import utils
import datetime
from . import common

utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = "0.1"

class FncsProxy(Agent):
    
    def __init__(self, **kwargs):
        super(FncsProxy,self).__init__(**kwargs)
        
    @Core.receiver('onstart')
    def start(self, sender, **kwargs):
        fncsDevicesTopic = common.FNCS_DEVICES()
        self.vip.pubsub.subscribe(peer = 'pubsub',
                                  prefix = fncsDevicesTopic,
                                  callback = self.onmessage).get(timeout=5)

    def onmessage(self, peer, sender, bus, topic, headers, message):
        # listen to fncs/output/devices
        # publish to devices
        devices_topic = topic.replace('fncs/output/devices/unit/',
                'devices/campus/building/unit/')
        self.vip.pubsub.publish('pubsub', devices_topic, headers, message).get(timeout=5)
        _log.debug('fncs/output/devices -> devices:\ntopic: %s\nmessage: %s'%(devices_topic, str(message)))
    
    @RPC.export
    def set_point(self, requester_id, topic, value, **kwargs):
        # publishes to the fncs/input/ subtopic for information
        # that goes to the bridge to pass to fncs message bus
        fncsInputTopic = common.FNCS_INPUT_PATH(path = topic)#this assumes topic starts with /devices/
        utcnow = datetime.datetime.utcnow()
        fncsHeaders = {}
        fncsHeaders['time'] = utils.format_timestamp(utcnow)
        if requester_id is not None:
            fncsHeaders['requesterID'] = requester_id
        self.vip.pubsub.publish('pubsub', fncsInputTopic, fncsHeaders, value).get(timeout=5)
        _log.debug('set_point -> fncs/input/topic:\ntopic: %s\nMessage: %s'%(fncsInputTopic, str(value)))
        return value
    
    @RPC.export
    def request_new_schedule(self, requester_id, task_id, priority, requests):
        # actuator stubb that needs to return success
        result = {'result' : 'SUCCESS',
                  'data' : {},
                  'info' : ''} 
        return result

    
    @RPC.export
    def request_cancel_schedule(self, requester_id, task_id):
        # actuator stub that needs to return success
        result = {'result' : 'SUCCESS',
                  'data' : {},
                  'info' : ''} 
        return result

    
def fncs_proxy(**kwargs): 
    return FncsProxy(identity='platform.actuator')


def main():
    '''Main method to start the agent'''
    utils.vip_main(fncs_proxy)
    
if  __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
