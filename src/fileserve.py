# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import os
import os.path

from flask import abort, Flask, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy


base_directory = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

# Load the default config file
app.config.from_pyfile(os.path.join(base_directory, 'config.cfg'))
# Then try to load a config file for use in production
try:
    app.config.from_envvar('FILESERVE_CONFIG_FILE')
except RuntimeError:
    # Use default/development values
    pass

if not app.config.get('SQLALCHEMY_DATABASE_URI', None):
    # Last resort, use SQLite database for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(os.path.join(base_directory, 'fileserve.db'))

if app.config.get('PRODUCTION'):
    app.use_x_sendfile = True

db = SQLAlchemy(app)


@app.route('/')
def index():
    abort(403)


# Models
class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, nullable=False)
    downloads = db.relationship('FileDownload', backref='file', lazy='select')

    def __repr__(self):
        return '<File %d|%r>' % (self.id, self.path)


class FileDownload(db.Model):
    __tablename__ = 'downloads'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    downloaded_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<FileDownload %d|%r|%r>' % (self.file_id, self.ip_address, self.downloaded_at)


@app.route('/file/<int:id>')
def get_file(id):
    file = File.query.filter_by(id=id).first_or_404()
    # if not file:
        # abort(404)
    # else:
    directory, filename = os.path.split(file.path)
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
