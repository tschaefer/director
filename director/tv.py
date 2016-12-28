# -*- coding: utf-8 -*-

import requests
import urlparse

class TV(object):

    def __init__(self, url):
        self.url = url
        self.chan = None
        self.stream = None

    def _post(self, endpoint, json):
        url = urlparse.urljoin(self.url, endpoint)
        try:
            requests.post(url, json=json)
        except:
            pass

    def _json(self, action, data=''):
        return {
            'action':  action,
            'data':    data,
            'options': 'live'
        }

    def start(self, chan, stream):
        self.chan = chan
        self.stream = stream

        json = self._json('start', data=stream)
        self._post('playback', json)

    def stop(self):
        self.chan = None
        self.stream = None

        json = self._json('stop')
        self._post('playback', json)

    def play(self):
        json = self._json('play')
        self._post('playback', json)

    def pause(self):
        json = self._json('pause')
        self._post('playback', json)

    def vol(self, action):
        json = self._json(action)
        self._post('volume', json)
