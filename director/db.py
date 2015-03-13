# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Models


class Database(object):

    def __init__(self, database='sqlite:////tmp/director.db', echo=False):
        self.database = database
        self.engine = create_engine(self.database, echo=echo)
        self.connector = None
        self.session = None

    def create(self):
        Models.metadata.create_all(self.engine)

    def bind(self):
        if not self.connector:
            self.connector = sessionmaker()
            self.connector.configure(bind=self.engine)

    def close(self):
        if self.connector:
            self.connector.close_all()
            self.connector = None

    def init_session(self):
        if not self.session:
            self.session = self.connector()

    def destroy_session(self):
        if self.session:
            self.session.close()
            self.session = None
