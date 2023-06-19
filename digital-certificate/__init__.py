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

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
        

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import certificates
    app.register_blueprint(certificates.bp)
    app.add_url_rule('/', endpoint='index')


    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    


    return app


