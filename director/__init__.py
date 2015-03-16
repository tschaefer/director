# -*- coding: utf-8 -*-

import sys
import os
import argparse
from importer import Importer
from service import Service


def stype(bytestring):
    unicode_string = bytestring.decode(sys.getfilesystemencoding())
    return unicode_string


def parse_options():
    db = os.path.join(os.path.expanduser('~'), 'director.db')
    db = 'sqlite:///%s' % db

    parser = argparse.ArgumentParser(description='Director')
    parser.add_argument('-d', '--database',
                        type=unicode,
                        default=db,
                        help='database url')
    subparsers = parser.add_subparsers()

    parser_import = subparsers.add_parser('import')
    parser_import.set_defaults(importer=True)
    parser_import.add_argument('path',
                               type=stype,
                               help='media path')
    parser_import.add_argument('-v', '--verbose',
                               action='store_true',
                               help='verbose putput')

    parser_service = subparsers.add_parser('service')
    parser_service.set_defaults(service=True)
    parser_service.add_argument('path',
                                type=stype,
                                help='media path')
    parser_service.add_argument('-H', '--host',
                                type=unicode,
                                default='localhost',
                                help='bind to address')
    parser_service.add_argument('-p', '--port',
                                type=int,
                                default=8888,
                                help='listen to port')

    return parser.parse_args()


def run(args):
    if hasattr(args, 'importer'):
        importer = Importer(path=args.path, database=args.database,
                            verbose=args.verbose)
        importer.run()
    elif hasattr(args, 'service'):
        service = Service(host=args.host, port=args.port,
                          database=args.database, path=args.path)
        service.run()


def main():
    args = parse_options()
    run(args)


if __name__ == '__main__':
    main()
