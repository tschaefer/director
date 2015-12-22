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
        return et.getroot()

    def find_nfos(self, path, pattern):
        nfos = list()
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, pattern):
                nfos.append(os.path.join(root, filename))
        return nfos

    def commit_entry(self, values, obj, cls):
        if isinstance(obj, Actor):
            self.db.session.add(obj)
        else:
            self.db.session.query(cls).filter(cls.pk == obj.pk).update(values)
        try:
            self.db.session.commit()
        except IntegrityError as e:
            if self.verbose:
                print "%s" % (e)
            self.db.session.rollback()
            return False
        else:
            return True


class Updater(Utils):

    def actor(self, show_pk, root):
        actor = Actor()
        actor.show_pk = show_pk
        actor.name = root[0].text
        actor.role = root[1].text
        actor.thumb = root[2].text
        self.commit_entry(None, actor, Actor)

    def show(self, root, old):
        show = dict()
        show.update(nfo_mtime=int(os.stat(old.nfo).st_mtime))
        show.update(plot=root.find('plot').text)
        show.update(genre=root.find('genre').text)
        premiered = root.find('premiered').text
        if premiered is not None:
            show.update(premiered=datetime.strptime(premiered, '%Y-%m-%d')
                        .date())
        show.update(studio=root.find('studio').text)
        fanart = os.path.join(old.base, 'fanart.jpg')
        if os.path.exists(fanart):
            show.update(fanart=fanart)
        if self.commit_entry(show, old, Show):
            for actor in old.actors:
                self.db.session.query(Actor).filter(Actor.show_pk == old.pk). \
                    delete()
            for branch in root.findall('actor'):
                self.actor(old.pk, branch)

    def shows(self):
        shows = self.db.session.query(Show).all()

        for show in shows:
            mtime = int(os.stat(show.nfo).st_mtime)
            if mtime != int(show.nfo_mtime) or not show.fanart:
                root = self.parse_nfo(show.nfo)
                if root is None:
                    continue
                elif root.tag != 'tvshow':
                    if self.verbose:
                        print "(%s) invalid root tag '%s'" % (show.nfo,
                                                              root.tag)
                    continue
                self.show(root, show)
            else:
                continue

    def episode(self, root, old, show):
        episode = dict()
        episode.update(nfo_mtime=int(os.stat(old.nfo).st_mtime))
        aired = root.find('aired').text
        if aired is not None:
            episode.update(aired=datetime.
                           strptime(aired, '%Y-%m-%d').date())
        episode.update(plot=root.find('plot').text)
        thumb = old.nfo.replace('.nfo', '.tbn')
        if os.path.exists(thumb):
            episode.update(thumb=thumb)
        else:
            thumb = old.nfo.replace('.nfo', '-thumb.jpg')
            if os.path.exists(thumb):
                episode.update(thumb=thumb)
            else:
                episode.update(thumb=root.find('thumb').text)
        poster = "season%02d.tbn" % (int(old.season))
        poster = os.path.join(show.base, poster)
        if os.path.exists(poster):
            episode.update(poster=poster)
        self.commit_entry(episode, old, Episode)

    def episodes(self):
        for show in self.db.session.query(Show).all():
            episodes = self.db.session.query(Episode). \
                filter(Episode.show_pk == show.pk).all()

            for episode in episodes:
                mtime = int(os.stat(episode.nfo).st_mtime)
                if mtime != int(episode.nfo_mtime) or not episode.thumb \
                        or not episode.poster:
                    root = self.parse_nfo(episode.nfo)
                    branches = list()
                    if root is None:
                        continue
                    if root.tag == 'episodedetails':
                        branches.append(root)
                    elif root.tag == 'xbmcmultiepisode':
                        for branch in root.findall('episodedetails'):
                            branches.append(branch)
                    else:
                        if self.verbose:
                            print "(%s) invalid root tag '%s'" % (episode.nfo,
                                                                  root.tag)
                        continue
                else:
                    continue

                for root in branches:
                    self.episode(root, episode, show)

    def run(self):
        self.shows()
        self.episodes()
