from flask import Flask, request, render_template, send_file, jsonify, redirect
import sqlite3
import hashlib
import requests
from datetime import datetime
from os import path

import yaml

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

SITE_KEY = config['SITE_KEY']
SECRET_KEY = config['SECRET_KEY']



app = Flask(__name__)
con = sqlite3.connect('database.db', check_same_thread=False)
cursor = con.cursor()

VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_bytes = file.read()
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    file_hash = sha256_hash.hexdigest()

    print(file_hash)
    # 判斷該 hash 值是否在資料庫中
    result = cursor.execute("SELECT * FROM hash_table WHERE hash_value = '%s'" % file_hash)
    if result.fetchone() is not None:
        return jsonify({'message' : 'successful'})
    else:
        return jsonify({'message' : 'failed'})
    
@app.route('/api/search', methods=['POST'])
def search_file():
    print(request.form)
    recaptcha_response = request.form['recaptcha_token']

    verify_response = requests.post(url=f'{VERIFY_URL}?secret={SECRET_KEY}&response={recaptcha_response}').json()
    print(verify_response)

    if verify_response['success'] == False or verify_response['score'] < 0.5:
        return jsonify({
            'message' : 'recaptcha failed',
        })
        

    # check if id and date in the form
    if not request.form['id'] or not request.form['date']:
        return jsonify({
            'message' : 'id or date not found',
        })

    id = request.form['id']
    activity_date = datetime.strptime(request.form['date'], "%Y-%m-%d")
    print(activity_date)
    # search file in files with the filename id-activity_date.pdf
    file_path = path.join('files', '%d%02d%02d' %(activity_date.year, activity_date.month, activity_date.day), '%s.pdf' % (id))
    print(file_path)

    if path.exists(file_path):
        # generate a token
        sha256_hash = hashlib.sha256()
        sha256_hash.update((str(datetime.now().timestamp()) + id).encode())
        token = sha256_hash.hexdigest()
        print(token)

        # insert token into database
        cursor.execute("INSERT INTO tokens (token) VALUES ('%s')" % (token))
        con.commit()
        return jsonify({
            'message' : 'ok',
            'token': token
        })
    else:
        return jsonify({
            'message' : 'file not found',
        })
    

    
@app.route('/api/download', methods=['GET'])
def download_file():
    id = request.args.get('id')
    date = request.args.get('date')
    token = request.args.get('token')
    activity_date = activity_date = datetime.strptime(date, "%Y-%m-%d")
    
    # check if token is valid
    result = cursor.execute("SELECT * FROM tokens WHERE token = '%s'" % token)
    if result.fetchone() is None:
        return redirect('/expired') 

    # if token exist, delete it
    cursor.execute("DELETE FROM tokens WHERE token = '%s'" % token)
    con.commit() 

    file_path =  'files/%d%02d%02d/%s.pdf' % (activity_date.year, activity_date.month, activity_date.day, id)

    return send_file(file_path,  as_attachment=True)


@app.route('/', methods=['GET'])
def index_page(name=None):
    return render_template('index.html', site_key=SITE_KEY)

@app.route('/expired', methods=['GET'])
def expired_page(name=None):

    return render_template('expired.html')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
