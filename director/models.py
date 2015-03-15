# -*- coding: utf-8 -*-

from sqlalchemy import (Column, Unicode, Integer, ForeignKey, Date,
                        SmallInteger, UniqueConstraint)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base


Models = declarative_base()


class Show(Models):
    __tablename__ = 'show'

    pk = Column(Integer, primary_key=True)
    title = Column(Unicode, nullable=False)
    tvdb = Column(Integer, nullable=False, unique=True)
    plot = Column(Unicode, nullable=True)
    genre = Column(Unicode, nullable=True)
    premiered = Column(Date, nullable=True)
    studio = Column(Unicode, nullable=True)
    base = Column(Unicode, nullable=False)
    thumb = Column(Unicode, nullable=True)


class Episode(Models):
    __tablename__ = 'episode'

    pk = Column(Integer, primary_key=True)
    show_pk = Column(Integer, ForeignKey('show.pk'), nullable=False)
    title = Column(Unicode, nullable=False)
    season = Column(SmallInteger, nullable=False)
    episode = Column(SmallInteger, nullable=False)
    aired = Column(Date, nullable=True)
    plot = Column(Unicode, nullable=True)
    thumb = Column(Unicode, nullable=True)
    video = Column(Unicode, nullable=False)
    type = Column(Unicode, nullable=False)

    show = relationship(Show, backref=backref('episodes', uselist=True,
                        cascade='delete,all'))

    __table_args__ = (UniqueConstraint('show_pk', 'season', 'episode'),)


class Actor(Models):
    __tablename__ = 'actor'

    pk = Column(Integer, primary_key=True)
    show_pk = Column(Integer, ForeignKey('show.pk'), nullable=False)
    name = Column(Unicode, nullable=False)
    role = Column(Unicode, nullable=False)
    thumb = Column(Unicode, nullable=True)

    show = relationship(Show, backref=backref('actors', uselist=True,
                        cascade='delete,all'))

    __table_args__ = (UniqueConstraint('show_pk', 'name', 'role'),)
