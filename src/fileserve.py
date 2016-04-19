# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import datetime
import os
import os.path

from flask import abort, Flask, make_response, request, redirect, send_from_directory, url_for
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
db.create_all()


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
    file = get_file(id)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown-User-Agent/0.0')
    download_time = datetime.datetime.now()

    # If we have a Referer or Range header, this is probably a multisegmented or resumed download
    should_count = request.headers.get('Referer') is None and request.range is None

    # Check for ignored user agents
    should_count = not any(agent in user_agent for agent in app.config.get('IGNORED_USER_AGENTS'))

    if should_count:
        download = FileDownload(file_id=file.id, downloaded_at=download_time, ip_address=ip_address, user_agent=user_agent)
        db.session.add(download)
        db.session.commit()

    response = make_response(redirect(url_for('download_file', id=id), 303))
    return response


@app.route('/download/<int:id>')
def download_file(id):
    file = get_file(id)
    directory, filename = os.path.split(file.path)
    return send_from_directory(directory, filename, as_attachment=True, attachment_filename=filename)


def get_file(file_id):
    file = File.query.filter_by(id=file_id).first_or_404()
    return file


if __name__ == '__main__':
    app.run(debug=True)
