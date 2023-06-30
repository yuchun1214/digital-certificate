import os
import json
import hashlib
from datetime import datetime, timezone,timedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, send_file, current_app
)

from pdfrw import (
    PdfReader, PdfWriter, IndirectPdfDict, PdfName
)

from .db import get_db
from .auth import login_required


bp = Blueprint('admin', __name__)


@bp.route('/admin/upload', methods=['POST'])
@login_required
def upload():
    print(request.form)
    print(request.form['date'])
    
    # check date
    if len(request.form['date']) == 0:
       return jsonify({'status' : 'failed', 'message' : 'date is not set'}), 400

    #  add attributes
    attributes = json.loads(request.form['attributes'])
    meta = {}
    for i in range(len(attributes)):
        meta[PdfName(attributes[i]['name'])] = attributes[i]['value'] 

    meta = IndirectPdfDict(meta)

    activity_date = datetime.strptime(request.form['date'], "%Y-%m-%d")
    activity_date = "{0:%Y%m%d}".format(activity_date)
    upload_directory = os.path.join(current_app.config['UPLOAD_FOLDER'], activity_date)

    
    try:
        os.makedirs(upload_directory)
    except OSError:
        pass
    
    uploaded_files = request.files.getlist('files')
    db = get_db()
    for file in uploaded_files:
        filename = os.path.join(upload_directory, file.filename)
        file.save(filename)
        try:
            with open(filename, 'rb') as input_pdf_file:
                reader = PdfReader(input_pdf_file)

                # Modify PDF metadata
                reader.Info = meta
                dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
                dt2 = dt1.astimezone(timezone(timedelta(hours=8)))
                reader.Info.IssuedTime = f"{dt2:%Y-%m-%d}"

                # Write the modified PDF back to the file
                PdfWriter(filename, trailer=reader).write()

            with open(filename, 'rb') as pdf_file:
                sha256_hash = hashlib.sha256()
                for chunk in iter(lambda: pdf_file.read(4096), b''):
                    sha256_hash.update(chunk)
                file_hash = sha256_hash.hexdigest()
                print(file_hash)
                try:
                    db.execute("INSERT INTO hash_table (filename, upload_date, hash_value) VALUES ('%s', '%s', '%s')" % (file.filename, activity_date,file_hash))
                except db.IntegrityError:
                    print(filename + ' already exists in the database')
                db.commit()
        except Exception as e:
            return jsonify({'status' : 'failed', 'message' : str(e)}), 500
            
    return jsonify({'status': 'success'}), 200

@bp.route('/admin', methods=['GET'])
@login_required
def admin():
    db = get_db()
    result = db.execute("SELECT id, filename, upload_date FROM hash_table")
    data = result.fetchall()
    files = []
    for i in data:
        files.append({
            'id' : i['id'],
            'filename' : i['filename'],
            'upload_date' : i['upload_date']
        })
    print(files)
    return render_template('admin.html', uploaded_files=files)
