# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Models


class Database(object):

    def __init__(self, database=None, verbose=False):
        self.database = database
        self.engine = create_engine(self.database, echo=verbose)
        self.connector = None
        self.session = None
        Models.metadata.create_all(self.engine)

    def bind(self):
        self.connector = sessionmaker()
        self.connector.configure(bind=self.engine)
        self.session = self.connector()

    def unbind(self):
        self.session.close()
        self.connector.close_all()
        self.connector = None
        self.session = None
