# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import os.path
import sys

from flask import current_app, url_for
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, prompt_bool, Shell
from flask.ext.script.commands import InvalidCommand

from fileserve import __version__
from fileserve.app import base_directory, create_app, db
from fileserve.models import File, FileDownload
from fileserve.utils import get_file_model


def make_shell_context():
    return dict(app=app, base_directory=base_directory, db=db, File=File, FileDownload=FileDownload)


app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(banner='fileserve v{0} shell'.format(__version__), make_context=make_shell_context))


@manager.command
def add_file(path):
    if not os.path.exists(path) or os.path.isdir(path):
        raise InvalidCommand('Path {0} does not exist or is a directory'.format(path))

    print('Adding file {0} to database'.format(path))
    new_file = File(path=path)
    db.session.add(new_file)
    db.session.commit()
    print('File added with ID: {0}\nDownload URL: {1}{2}'.format(new_file.id, current_app.config['BASE_URL'], url_for('get_file', id=new_file.id)))


@manager.command
def remove_file(id):
    file = get_file_or_raise(id)
    confirmation = prompt_bool('Are you sure you want to remove this file?\nPath: {0}\nID: {1}\n(y/n)'.format(file.path, file.id), default=False, yes_choices=['y'], no_choices='n')
    if confirmation:
        db.session.delete(file)
        db.session.commit()
        print('File removed')
    else:
        print('File not removed')


@manager.command
def file_stats(id):
    file = get_file_or_raise(id)
    downloads = file.downloads.order_by(FileDownload.downloaded_at).all()
    print('File path: {0}\nID: {1}\nNumber of downloads: {2}'.format(file.path, file.id, len(downloads)))
    try:
        print('Last download: {0}'.format(downloads[-1].downloaded_at))
    except IndexError:
        pass


def get_file_or_raise(id):
    file = get_file_model(id)
    if file is None:
        raise InvalidCommand('File with ID {0} does not exist'.format(id))
    else:
        return file


if __name__ == '__main__':
    try:
        manager.run()
    except InvalidCommand as e:
        print('Error: {0}'.format(e), file=sys.stderr)
        sys.exit(1)
