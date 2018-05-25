# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import ujson
import logging
import requests
import time
from iris.constants import PUSHOVER_SUPPORT
from iris.custom_import import import_custom_module
from http.client import HTTPSConnection
import urllib
import re

logger = logging.getLogger(__name__)


class iris_pushover(object):
    supports = frozenset([PUSHOVER_SUPPORT])

    def __init__(self, config):
        self.config = config
        # For now slack has only IM mode but we can expand it to send msg to a
        # channel  instead of a user
        self.modes = {
            PUSHOVER_SUPPORT: self.send_message
        }
        self.proxy = None
        if 'proxy' in self.config:
            host = self.config['proxy']['host']
            port = self.config['proxy']['port']
            self.proxy = {'http': 'http://%s:%s' % (host, port),
                          'https': 'https://%s:%s' % (host, port)}
        self.application_token = config.get('app_token')
        self.title = config.get('title')
        self.sound= config.get('sound')
        self.high_urgency_regex = config.get('high_urgency_regex')
        self.priority = 0

    def send_message(self, message):
        start = time.time()
        if re.match( self.high_urgency_regex, message['body'], re.DOTALL ):
            self.priority = 1
        else:
            self.priority = 0
        try:
            conn = HTTPSConnection("api.pushover.net:443")
            conn.request("POST", "/1/messages.json",
                         urllib.urlencode({
                             "token": self.application_token,
                             "user": message['destination'],
                             "message": message['body'],
                             "sound": self.sound,
                             "priority": self.priority,
                             "title": self.title
                         }), {"Content-type": "application/x-www-form-urlencoded"})
            response = conn.getresponse()
            if response.status == 200:
                return time.time() - start
            else:
                logger.error('Failed to send message to pushover: %d',
                             response.status_code)
        except Exception:
            logger.exception('pushover post request failed')

    def send(self, message, customizations=None):
        return self.modes[message['mode']](message)
