# -*- coding: utf-8 -*-

from xml.etree import ElementTree
from datetime import datetime
import os
import fnmatch
from sqlalchemy.exc import IntegrityError
from director.models import Show, Episode, Actor
from director.db import Database


class Utils(object):

    def __init__(self, path=None, database=None, verbose=False):
        self.verbose = verbose
        self.path = os.path.abspath(path)
        self.db = Database(database=database, verbose=verbose)
        self.db.bind()

    def __del__(self):
        self.db.unbind()

    def parse_nfo(self, nfo):
        try:
            et = ElementTree.parse(nfo)
        except ElementTree.ParseError as e:
            if self.verbose:
                print "(%s) %s" % (nfo, e)
            return None
        except IOError as e:
            if self.verbose:
                print "%s" % (e)
            return None
        else:
            return et.getroot()

    def find_nfos(self, path, pattern):
        nfos = list()
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, pattern):
                nfos.append(os.path.join(root, filename))
        return nfos

    def commit_entry(self, obj):
        self.db.session.add(obj)
        try:
            self.db.session.commit()
        except IntegrityError as e:
            if self.verbose:
                print "%s" % (e)
            self.db.session.rollback()
            return False
        else:
            return True

    def get_episode_video(self, nfo):
        for ext in ['.mp4', '.avi', '.mkv', '.m2ts', '.wmv']:
            video = nfo.replace('.nfo', ext)
            if os.path.exists(video):
                return (video, ext.lstrip('.'))
            video = nfo.replace('.nfo', ext.upper())
            if os.path.exists(video):
                return (video, ext.lstrip('.'))
        if self.verbose:
            print "No video found for '%s'" % (nfo)
        return (None, None)


class Importer(Utils):

    def actor(self, show_pk, root):
        actor = Actor()
        actor.show_pk = show_pk
        actor.name = root[0].text
        actor.role = root[1].text
        actor.thumb = root[2].text
        self.commit_entry(actor)

    def show(self, nfo, root):
        show = Show()
        show.nfo = nfo
        show.nfo_mtime = int(os.stat(nfo).st_mtime)
        show.title = root.find('title').text
        show.plot = root.find('plot').text
        show.tvdb = root.find('id').text
        show.genre = root.find('genre').text
        premiered = root.find('premiered').text
        if premiered is not None:
            show.premiered = datetime.strptime(premiered, '%Y-%m-%d') \
                    .date()
        show.studio = root.find('studio').text
        show.base = os.path.dirname(nfo)
        fanart = os.path.join(show.base, 'fanart.jpg')
        if os.path.exists(fanart):
            show.fanart = fanart
        if self.commit_entry(show):
            for branch in root.findall('actor'):
                self.actor(show.pk, branch)

    def shows(self):
        nfos = self.find_nfos(self.path, 'tvshow.nfo')
        if len(nfos) == 0:
            if self.verbose:
                print "(%s) no shows found" % (self.path)
            return

        _nfos = self.db.session.query(Show.nfo).all()
        _nfos = [nfo[0] for nfo in _nfos]

        for nfo in nfos:
            if nfo in _nfos:
                continue
            root = self.parse_nfo(nfo)
            if root is None:
                continue
            elif root.tag != 'tvshow':
                if self.verbose:
                    print "(%s) invalid root tag '%s'" % (nfo, root.tag)
                continue
            else:
                self.show(nfo, root)

    def episode(self, nfo, root, show):
        episode = Episode()
        episode.nfo = nfo
        episode.nfo_mtime = int(os.stat(nfo).st_mtime)
        episode.base = os.path.dirname(nfo)
        episode.show_pk = show.pk
        episode.title = root.find('title').text
        episode.season = root.find('season').text
        episode.episode = root.find('episode').text
        aired = root.find('aired').text
        if aired is not None:
            episode.aired = datetime. \
                strptime(aired, '%Y-%m-%d').date()
        episode.plot = root.find('plot').text
        episode.thumb = None
        thumb = nfo.replace('.nfo', '.tbn')
        if os.path.exists(thumb):
            episode.thumb = thumb
        if episode.thumb is None:
            thumb = nfo.replace('.nfo', '-thumb.jpg')
            if os.path.exists(thumb):
                episode.thumb = thumb
            else:
                episode.thumb = root.find('thumb').text
        poster = "season%02d.tbn" % (int(episode.season))
        poster = os.path.join(show.base, poster)
        if os.path.exists(poster):
            episode.poster = poster
        episode.video, episode.video_type = self. \
            get_episode_video(nfo)
        self.commit_entry(episode)

    def episodes(self):
        for show in self.db.session.query(Show).all():
            nfos = self.find_nfos(show.base, '*.nfo')
            for nfo in nfos:
                if nfo.endswith('tvshow.nfo'):
                    nfos.remove(nfo)

            _nfos = self.db.session.query(Episode.nfo). \
                filter(Episode.show_pk == "%d" % (show.pk)).all()
            _nfos = [nfo[0] for nfo in _nfos]

            for nfo in nfos:
                if nfo in _nfos:
                    continue

                root = self.parse_nfo(nfo)
                branches = list()
                if root is None:
                    continue
                elif root.tag == 'episodedetails':
                    branches.append(root)
                elif root.tag == 'xbmcmultiepisode':
                    for _root in root.findall('episodedetails'):
                        branches.append(_root)
                else:
                    if self.verbose:
                        print "(%s) invalid root tag '%s'" % (nfo, root.tag)
                    continue

                for root in branches:
                    self.episode(nfo, root, show)

    def run(self):
        self.shows()
        self.episodes()
