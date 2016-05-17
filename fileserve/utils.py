# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from base64 import urlsafe_b64decode
import datetime
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

from flask import current_app, request, redirect, url_for

from .models import File


def get_file_model_from_id(id):
    file = File.query.filter_by(id=id).first()
    return file


def get_file_model_from_slug(slug):
    file = File.query.filter_by(url_slug=urlparse.unquote(slug)).first()
    return file


def get_ip_address():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip is None:
        return '0.0.0.0'
    else:
        return ip


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

