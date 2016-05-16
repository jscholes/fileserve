# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import os.path
import sys

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Shell
from flask.ext.script.commands import InvalidCommand

from fileserve.app import base_directory, create_app, db
from fileserve.models import File, FileDownload


def make_shell_context():
    return dict(app=app, base_directory=base_directory, db=db, File=File, FileDownload=FileDownload)


app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(make_context=make_shell_context))


@manager.command
def add_file(path):
    if not os.path.exists(path) or os.path.isdir(path):
        raise InvalidCommand('Path {0} does not exist or is a directory'.format(path))

    print('Adding file {0} to database'.format(path))
    new_file = File(path=path)
    db.session.add(new_file)
    db.session.commit()
    print('File added with ID: {0}'.format(new_file.id))


if __name__ == '__main__':
    try:
        manager.run()
    except InvalidCommand as e:
        print(e, file=sys.stderr)
        sys.exit(1)
