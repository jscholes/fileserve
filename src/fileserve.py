# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from base64 import urlsafe_b64decode, urlsafe_b64encode
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

    def get_token(self):
        token = '|'.join([
            str(self.file_id),
            str(self.downloaded_at.timestamp()),
            self.ip_address
        ])
        token = urlsafe_b64encode(token.encode('ascii', errors='ignore')).rstrip(b'=')
        return token


@app.route('/')
def index():
    abort(403)


@app.route('/file/<int:id>')
def get_file(id):
    file = get_file_info(id)
    ip_address = get_ip_address()
    user_agent = get_user_agent()
    download_time = datetime.datetime.now()

    # Check for ignored user agents
    should_count = not any(agent in user_agent for agent in app.config.get('IGNORED_USER_AGENTS'))

    download = FileDownload(file_id=file.id, downloaded_at=download_time, ip_address=ip_address, user_agent=user_agent)
    if should_count:
        db.session.add(download)
        db.session.commit()

    response = make_response(redirect(url_for('download_file', id=id), 303))
    response.set_cookie(get_token_cookie_name(file.id), download.get_token(), max_age=app.config.get('TOKEN_VALIDITY_PERIOD', 600))
    return response


@app.route('/download/<int:id>')
def download_file(id):
    valid_token = False
    file = get_file_info(id)
    cookies = request.cookies
    cookie_name = get_token_cookie_name(file.id)
    if cookie_name in cookies:
        valid_token = verify_download_token(file.id, cookies[cookie_name])

    if valid_token:
        directory, filename = os.path.split(file.path)
        return send_from_directory(directory, filename, as_attachment=True, attachment_filename=filename)
    else:
        abort(403)


def get_file_info(file_id):
    file = File.query.filter_by(id=file_id).first_or_404()
    return file


def get_ip_address():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def get_user_agent():
    return request.headers.get('User-Agent', 'Unknown-User-Agent/0.0')


def get_token_cookie_name(file_id):
    return 'download_token{0}'.format(file_id)


def verify_download_token(file_id, token):
    token = urlsafe_b64decode(add_base64_padding(token)).decode('ascii', errors='ignore')
    try:
        token_file_id, timestamp, token_ip_address = token.split('|')
    except ValueError:
        return False

    if token_file_id != str(file_id) or token_ip_address != get_ip_address():
        return False

    token_creation_time = float(timestamp)
    access_time = datetime.datetime.now().timestamp()
    delta = access_time - token_creation_time
    if delta < 0 or delta > app.config.get('TOKEN_VALIDITY_PERIOD', 600):
        return False

    return True


def add_base64_padding(token):
    required_padding = 4 - len(token) % 4
    if required_padding:
        token += '=' * required_padding
    return token


if __name__ == '__main__':
    app.run(debug=True)
