import hashlib
import requests
from datetime import datetime
from os import path

import yaml
import glob
import sys

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, send_file, current_app,
    send_from_directory
)
from werkzeug.exceptions import abort
from .auth import recaptcha_required
from .db import get_db


bp = Blueprint('certificates', __name__)


@bp.route('/api/upload', methods=['POST'])
@recaptcha_required
def upload_file():
    file = request.files['file']
    
    file_bytes = file.read()
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    file_hash = sha256_hash.hexdigest()

    print(file_hash)
    # 判斷該 hash 值是否在資料庫中
    db = get_db()
    result = db.execute("SELECT * FROM hash_table WHERE hash_value = '%s'" % file_hash)
    if result.fetchone() is not None:
        return jsonify({'message' : 'successful'})
    else:
        return jsonify({'message' : 'failed'})
    
@bp.route('/api/search', methods=['POST'])
@recaptcha_required
def search_file():

    # check if id and date in the form
    if not request.form['name'] or not request.form['date']:
        return jsonify({
            'message' : 'name or activity date is not found',
        })

    name = request.form['name']
    # school = request.form['school']
    activity_date = datetime.strptime(request.form['date'], "%Y-%m-%d")
    # search file in files with the filename activity_date/id.pdf
    files = glob.glob(path.join(current_app.instance_path, path.join(current_app.config['UPLOAD_FOLDER'], '%d%02d%02d' % (activity_date.year,
                                                         activity_date.month,
                                                         activity_date.day),
                                '*%s*' % (name))))

    if len(files) > 0:
        tokens = []
        for file in files:
    
            # generate a token
            sha256_hash = hashlib.sha256()
            sha256_hash.update((str(datetime.now().timestamp()) + name).encode())
            token = sha256_hash.hexdigest()
            print(token)
            tokens.append(token)

            # insert token into database
            db = get_db()
            db.execute("INSERT INTO tokens (token, filename) VALUES ('%s', '%s')" % (token, file))
        db.commit()
        return jsonify({
            'message' : 'ok',
            'tokens': tokens,
            'filenames' : [path.basename(file) for file in files]
        })
    else:
        return jsonify({
            'message' : 'file not found',
        })
    

    
@bp.route('/api/download', methods=['GET'])
def download_file():
    token = request.args.get('token')
    db = get_db() 
    # check if token is valid
    result = db.execute("SELECT token, filename FROM tokens WHERE token = '%s'" % token)
    entry = result.fetchone()
    if entry is None:
        return redirect('/expired') 

    # if token exist, delete it
    filename = entry[1]
    print(filename)
    db.execute("DELETE FROM tokens WHERE token = '%s'" % token)
    db.commit() 

    return send_file(filename,  as_attachment=True)


@bp.route('/', methods=['GET'])
def index_page(name=None):
    SITE_KEY = current_app.config['reCAPTCHA_SITE_KEY']
    return render_template('index.html', site_key=SITE_KEY)

@bp.route('/expired', methods=['GET'])
def expired_page(name=None):

    return render_template('expired.html')


@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(path.join(current_app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.mircrosoft.icon')
