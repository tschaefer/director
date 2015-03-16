# -*- coding: utf-8 -*-

from xml.etree import ElementTree
from datetime import datetime
import os
import fnmatch
from sqlalchemy.exc import IntegrityError
from models import Show, Episode, Actor
from db import Database


class Importer(object):

    def __init__(self, path=None, database=None, verbose=False):
        self.path = os.path.abspath(path)
        self.db = Database(database=database, verbose=verbose)
        self.db.bind()

    def __del__(self):
        self.db.unbind()

    def shows(self):
        nfos = list()
        for root, dirnames, filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, 'tvshow.nfo'):
                nfos.append(os.path.join(root, filename))

        for nfo in nfos:
            et = ElementTree.parse(nfo)
            root = et.getroot()
            if root.tag != 'tvshow':
                continue

            show = Show()
            show.title = root.find('title').text
            show.plot = root.find('plot').text
            show.tvdb = int(root.find('id').text)
            show.genre = root.find('genre').text
            premiered = root.find('premiered').text
            show.premiered = datetime.strptime(premiered, '%Y-%m-%d').date()
            show.studio = root.find('studio').text
            show.base = os.path.dirname(nfo)
            thumb = os.path.join(show.base, 'fanart.jpg')
            if os.path.exists(thumb):
                show.thumb = thumb
            else:
                show.thumb = None
            self.db.session.add(show)
            try:
                self.db.session.commit()
            except IntegrityError:
                self.db.session.rollback()

    def actors(self):
        for show in self.db.session.query(Show).all():
            et = ElementTree.parse(os.path.join(show.base, 'tvshow.nfo'))
            root = et.getroot()
            if root.tag != 'tvshow':
                continue

            for _actor in root.findall('actor'):
                actor = Actor()
                actor.show_pk = show.pk
                actor.name = _actor[0].text
                actor.role = _actor[1].text
                actor.thumb = _actor[2].text
                self.db.session.add(actor)
                try:
                    self.db.session.commit()
                except IntegrityError:
                    self.db.session.rollback()

    def _video(self, nfo):
        for ext in ['.mp4', '.avi', '.mkv']:
            video = nfo.replace('.nfo', ext)
            if os.path.exists(video):
                return (video, ext.lstrip('.'))
        return (None, None)

    def _thumb(self, nfo):
        thumb = nfo.replace('.nfo', '.tbn')
        if os.path.exists(thumb):
            return thumb
        return None

    def _episode(self, root, show, nfo):
        episode = Episode()
        episode.show_pk = show.pk
        episode.title = root.find('title').text
        episode.season = root.find('season').text
        episode.episode = root.find('episode').text
        aired = root.find('aired').text
        episode.aired = datetime.strptime(aired, '%Y-%m-%d')
        episode.plot = root.find('plot').text
        thumb = self._thumb(nfo)
        if thumb is not None:
            episode.thumb = thumb
        else:
            episode.thumb = root.find('thumb').text
        episode.video, episode.type = self._video(nfo)
        self.db.session.add(episode)
        try:
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()

    def episodes(self):
        for show in self.db.session.query(Show).all():
            episode_nfos = list()
            for root, dirnames, filenames in os.walk(show.base):
                for filename in fnmatch.filter(filenames, '*.nfo'):
                    if filename == 'tvshow.nfo':
                        continue
                    episode_nfos.append(os.path.join(root, filename))
            for nfo in episode_nfos:
                et = ElementTree.parse(nfo)
                root = et.getroot()
                if root.tag == 'episodedetails':
                    self._episode(root, show, nfo)
                elif root.tag == 'xbmcmultiepisode':
                    for _root in root.findall('episodedetails'):
                        self._episode(_root, show, nfo)
                else:
                    continue

    def run(self):
        self.shows()
        self.episodes()
        self.actors()
