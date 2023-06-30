import os
import yaml

from flask import Flask

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

reCAPTCHA_SITE_KEY = config['SITE_KEY']
reCAPTCHA_SECRET_KEY = config['SECRET_KEY']

def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'digital-certificate.sqlite'),
    )
    app.config['reCAPTCHA_SITE_KEY'] = reCAPTCHA_SITE_KEY
    app.config['reCAPTCHA_SECRET_KEY'] = reCAPTCHA_SECRET_KEY
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    app.config['TEMP_FOLDER'] = os.path.join(app.instance_path, 'temp')
    app.config['reCAPTCHA_VERIFY_URL'] = 'https://www.google.com/recaptcha/api/siteverify'

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
        

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # create upload folder
    try:
        upload_folder_name = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder_name)
    except OSError:
        pass

    # create temp folder
    try:
        temp_folder_name = app.config['TEMP_FOLDER']
        os.makedirs(temp_folder_name)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    auth.init_auth(app)
    app.register_blueprint(auth.bp)

    from . import certificates
    app.register_blueprint(certificates.bp)
    app.add_url_rule('/', endpoint='index')

    from . import admin
    app.register_blueprint(admin.bp)
    app.add_url_rule('/admin', endpoint='admin')


    return app


