# -*- coding: utf-8 -*-

import os
import werkzeug
import flask
from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
from models import Show, Episode


app = Flask(__name__)
db = SQLAlchemy(app)


def request_json():
    best = flask.request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        flask.request.accept_mimetypes[best] > \
        flask.request.accept_mimetypes['text/html']


def media_url(path):
    rel_path = os.path.relpath(path, app.config['media'])
    return os.path.join(os.path.sep, 'media', rel_path)


def obj_to_dict(obj, json=False):
    pickle = obj.__dict__
    pickle.pop('_sa_instance_state')

    if isinstance(obj, Show):
        fanart = pickle['fanart']
        if fanart is None:
            fanart = 'holder.js/1920x1080/gray/auto/text:%s' % (pickle['title'])
        else:
            fanart = media_url(fanart)
        pickle.update(fanart=fanart)
        pickle.pop('base')
        if json:
            pickle['premiered'] = str(pickle['premiered'])
    elif isinstance(obj, Episode):
        if json:
            pickle['aired'] = str(pickle['aired'])
        thumb = pickle['thumb']
        if thumb is None:
            thumb = 'holder.js/400x225/gray/auto/text:%s' % (pickle['title'])
        elif not thumb.startswith('http://'):
            thumb = media_url(thumb)
        pickle.update(thumb=thumb)
        video = media_url(pickle['video'])
        pickle.update(video=video)

    return pickle


@app.template_filter('date')
def date_filter(date, dateformat='%Y-%m-%d'):
    if date is None:
        return ''
    return date.strftime(dateformat)


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
            filter(Episode.title.like("%%%s%%" % (query)))
    else:
        _episodes = db.session.query(Episode)
    _episodes = _episodes.order_by(Episode.show_pk).order_by(Episode.season) \
        .order_by(Episode.episode).all()

    episodes = list()
    for _episode in _episodes:
        _show = _episode.show
        episode = obj_to_dict(_episode, json=request_json())
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

    episode = obj_to_dict(_episode, json=request_json())
    episode.update(show=_show.title)
    poster = _show.fanart
    if poster is None:
        poster = 'holder.js/1920x1080/gray/auto/text:%s' % (episode['title'])
    else:
        poster = media_url(poster)
    episode.update(poster=poster)


    if request_json():
        return flask.jsonify(episode=episode)

    return flask.render_template('episode.html', episode=episode)


@app.route('/show/<int:show_id>/', methods=['GET', 'POST'])
def get_show(show_id):
    _show = db.session.query(Show).get(show_id)
    if not _show:
        flask.abort(404)

    _actors = _show.actors

    _episodes = db.session.query(Episode).filter_by(show_pk=_show.pk)
    if flask.request.method == 'POST':
        query = unicode(flask.request.form['query'])
        _episodes = _episodes.filter(Episode.title.like('%%%s%%' % (query)))
    _episodes = _episodes.order_by(Episode.season).order_by(Episode.episode) \
        .all()

    show = obj_to_dict(_show, json=request_json())

    actors = list()
    for _actor in _actors:
        actor = obj_to_dict(_actor, json=request_json())
        actors.append(actor)
    show.update(actors=actors)

    episodes = list()
    for _episode in _episodes:
        episode = obj_to_dict(_episode, json=request_json())
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
        if len(_show.episodes) == 0:
            continue
        show = obj_to_dict(_show, json=request_json())
        show.pop('episodes')
        shows.append(show)

    if request_json():
        return flask.jsonify(shows=shows)

    return flask.render_template('shows.html', shows=shows)


class Service(object):

    def __init__(self, path=None, database=None, host=None, port=None):
        self.path = path
        self.database = database
        self.host = host
        self.port = port

    def run(self):
        media = Blueprint('media', __name__, static_url_path='/media',
                          static_folder=self.path)

        app.register_blueprint(media)
        app.config['SQLALCHEMY_DATABASE_URI'] = self.database
        app.config['media'] = self.path

        app.run(host=self.host, port=self.port, debug=True, threaded=True)
