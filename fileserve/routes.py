# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from base64 import urlsafe_b64decode
import datetime
import os
import os.path

from flask import abort, current_app, request, redirect, send_from_directory, url_for

from .app import db
from .models import File, FileDownload


def init_app(app):
    routes = [
        ('/', index),
        ('/file/<int:id>', get_file),
        ('/download/<token>/<int:id>', download_file),
    ]

    for url_rule, view_func in routes:
        app.add_url_rule(url_rule, view_func=view_func)


def index():
    abort(403)


def get_file(id):
    file = get_file_info(id)
    ip_address = get_ip_address()
    user_agent = get_user_agent()
    download_time = datetime.datetime.now()

    # Check for ignored user agents
    should_count = not any(agent in user_agent for agent in current_app.config.get('IGNORED_USER_AGENTS'))

    download = FileDownload(file_id=file.id, downloaded_at=download_time, ip_address=ip_address, user_agent=user_agent)
    if should_count:
        db.session.add(download)
        db.session.commit()

    return redirect_to_endpoint('download_file', token=download.get_token(), id=id)


def download_file(token, id):
    valid_token = False
    file = get_file_info(id)
    valid_token = verify_download_token(file.id, token)

    if valid_token:
        directory, filename = os.path.split(file.path)
        return send_from_directory(directory, filename, as_attachment=True, attachment_filename=filename)
    else:
        return redirect_to_endpoint('get_file', id=id, invalid_token=1)


def get_file_info(file_id):
    file = File.query.filter_by(id=file_id).first_or_404()
    return file


def get_ip_address():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def get_user_agent():
    return request.headers.get('User-Agent', 'Unknown-User-Agent/0.0')


def redirect_to_endpoint(endpoint, **kwargs):
    return redirect(url_for(endpoint, **kwargs), 303)


def verify_download_token(file_id, token):
    if len(token) > 128:
        return False
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
    if delta < 0 or delta > current_app.config.get('TOKEN_VALIDITY_PERIOD', 600):
        return False

    return True


def add_base64_padding(token):
    required_padding = 4 - len(token) % 4
    if required_padding:
        token += '=' * required_padding
    return token

