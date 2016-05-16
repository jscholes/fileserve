# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import os
import os.path

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


base_directory = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()


def create_app(config_path=os.environ.get('FILESERVE_CONFIG_FILE', None)):
    app = Flask(__name__)

    # Load the default config file
    app.config.from_pyfile(os.path.join(base_directory, 'config.cfg'))
    # Then try to load a config file for use in production
    if config_path is not None:
        app.config.from_pyfile(config_path)

    if not app.config.get('SQLALCHEMY_DATABASE_URI', None):
        # Last resort, use SQLite database for development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(os.path.join(base_directory, 'fileserve.db'))

    if app.config.get('PRODUCTION'):
        app.use_x_sendfile = True

    db.init_app(app)
    from . import routes
    routes.init_app(app)
    return app
