# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from base64 import urlsafe_b64encode

from .app import db


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, nullable=False)
    downloads = db.relationship('FileDownload', backref='file', lazy='dynamic')

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

