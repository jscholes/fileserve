# fileserve
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import os.path

from flask import abort, Flask


base_directory = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config.from_pyfile(os.path.join(base_directory, 'config.cfg'))


@app.route('/')
def index():
    abort(403)


if __name__ == '__main__':
    app.run(debug=True)
