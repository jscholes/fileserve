# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Shell

from fileserve.app import base_directory, create_app, db
from fileserve.models import File, FileDownload


def make_shell_context():
    return dict(app=app, base_directory=base_directory, db=db, File=File, FileDownload=FileDownload)


app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()
