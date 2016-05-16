# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import datetime
import os
import os.path

from flask import abort, current_app, send_from_directory

from .app import db
from .models import FileDownload
from .utils import get_file_model, get_ip_address, get_user_agent, redirect_to_endpoint, verify_download_token


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
    file = get_file_model(id)
    if file is None:
        abort(404)
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
    file = get_file_model(id)
    if file is None:
        abort(404)
    valid_token = verify_download_token(file.id, token)

    if valid_token:
        directory, filename = os.path.split(file.path)
        return send_from_directory(directory, filename, as_attachment=True, attachment_filename=filename)
    else:
        return redirect_to_endpoint('get_file', id=id, invalid_token=1)

