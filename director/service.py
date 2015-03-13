# -*- coding: utf-8 -*-

import os
import werkzeug
import flask
from flask import Flask, Blueprint
from models import Show, Episode, Actor
from db import Database

db = Database()
db.bind()
db.init_session()

media = Blueprint('media', __name__, static_url_path='/media',
                  static_folder='/mnt/storage/media/video/series')
app = Flask(__name__)
app.register_blueprint(media)


def request_json():
    best = flask.request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        flask.request.accept_mimetypes[best] > \
        flask.request.accept_mimetypes['text/html']


def media_url(path):
    rel_path = os.path.relpath(path, '/mnt/storage/media/video/series')
    return os.path.join(os.path.sep, 'media', rel_path)


@app.errorhandler(405)
@app.errorhandler(404)
def page_not_found(e):
    if isinstance(e, werkzeug.exceptions.NotFound):
        if request_json():
            error = "Oops! The Page you requested was not found!"
            return flask.jsonify(error=error), 404
        return flask.render_template('http_error.html', error=404), 404
    if isinstance(e, werkzeug.exceptions.MethodNotAllowed):
        if request_json():
            error = "Oops! The requested method is not allowed!"
            return flask.jsonify(error=error), 405
        return flask.render_template('http_error.html', error=405), 405


@app.route('/episodes/', methods=['GET', 'POST'])
def get_episodes():
    if flask.request.method == 'POST':
        query = unicode(flask.request.form['query'])
        _episodes = db.session.query(Episode). \
                    filter(Episode.title.like("%%%s%%" % (query))).all()
    else:
        _episodes = db.session.query(Episode).all()

    episodes = list()
    for _episode in _episodes:
        _show = _episode.show
        episode = _episode.__dict__
        episode.pop('_sa_instance_state')
        if request_json():
            episode['aired'] = str(episode['aired'])
        episode['video'] = media_url(episode['video'])
        episode.update(show=_show.title)
        episodes.append(episode)

    if request_json():
        return flask.jsonify(episodes=episodes)

    return flask.render_template('episodes.html', episodes=episodes)


@app.route('/episode/<int:episode_id>/file')
def get_episode_file(episode_id):
    episode = db.session.query(Episode).get(episode_id)
    if not episode:
        flask.abort(404)
    path = episode.video
    filename = os.path.basename(path)
    response = flask.send_file(path, as_attachment=True,
                               attachment_filename=filename)
    response.headers['Content-Length'] = os.path.getsize(path)

    return response


@app.route('/episode/<int:episode_id>/')
def get_episode(episode_id):
    _episode = db.session.query(Episode).get(episode_id)
    if not _episode:
        flask.abort(404)
    _show = _episode.show

    episode = _episode.__dict__
    episode.pop('_sa_instance_state')
    if request_json():
        episode['aired'] = str(episode['aired'])
    video = media_url(episode['video'])
    episode.update(video=video)
    thumb = episode['thumb']
    if not thumb.startswith('http'):
        thumb = media_url(thumb)
        episode.update(thumb=thumb)
    episode.update(show=_show.title)
    poster = _show.thumb
    if poster is None:
        poster = '/mnt/storage/media/video/series/no-fanart.png'
    poster = media_url(poster)
    episode.update(poster=poster)
    episode.update(poster=poster)

    if request_json():
        return flask.jsonify(episode=episode)

    return flask.render_template('episode.html', episode=episode)


@app.route('/show/<int:show_id>/')
def get_show(show_id):
    _show = db.session.query(Show).get(show_id)
    if not _show:
        flask.abort(404)

    _actors = _show.actors
    _episodes = _show.episodes

    show = _show.__dict__
    show.pop('_sa_instance_state')
    thumb = show['thumb']
    if thumb is None:
        thumb = '/mnt/storage/media/video/series/no-fanart.png'
    thumb = media_url(thumb)
    show.update(thumb=thumb)
    show.pop('base')
    if request_json():
        show['premiered'] = str(show['premiered'])

    actors = list()
    for _actor in _actors:
        actor = _actor.__dict__
        actor.pop('_sa_instance_state')
        actors.append(actor)
    show.update(actors=actors)

    episodes = list()
    for _episode in _episodes:
        episode = _episode.__dict__
        episode.pop('_sa_instance_state')
        if request_json():
            episode['aired'] = str(episode['aired'])
        thumb = episode['thumb']
        if not thumb.startswith('http'):
            thumb = media_url(thumb)
            episode.update(thumb=thumb)
        video = media_url(episode['video'])
        episode.update(video=video)
        episodes.append(episode)
    show.update(episodes=episodes)

    if request_json():
        return flask.jsonify(show=show)

    return flask.render_template('show.html', show=show)


@app.route('/', methods=['GET', 'POST'])
@app.route('/shows/', methods=['GET', 'POST'])
def get_shows():
    if flask.request.method == 'POST':
        query = unicode(flask.request.form['query'])
        _shows = db.session.query(Show). \
                 filter(Show.title.like("%%%s%%" % (query))).all()
    else:
        _shows = db.session.query(Show).all()

    shows = list()
    for _show in _shows:
        show = _show.__dict__
        show.pop('_sa_instance_state')
        thumb = show['thumb']
        if thumb is None:
            thumb = '/mnt/storage/media/video/series/no-fanart.png'
        thumb = media_url(thumb)
        show.update(thumb=thumb)
        show.pop('base')
        if request_json():
            show['premiered'] = str(show['premiered'])
        shows.append(show)

    if request_json():
        return flask.jsonify(shows=shows)

    return flask.render_template('shows.html', shows=shows)


class Service(object):

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port

    def run(self):
        app.run(host=self.host, port=self.port, debug=True, threaded=False)
