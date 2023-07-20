import functools
import click
import requests

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

def password_validation(ctx, param, password):
    # check if there is at least a captal letter in the password
    error_msg = ""
    if not any(x.isupper() for x in password):
        error_msg += "Password must contain at least a captal letter.\n"
    
    # check if there is at least a lowercase letter in the password
    if not any(x.islower() for x in password):
        error_msg += "Password must contain at least a lowercase letter.\n"

    # check if there is at least 6 digits in the password
    if not any(x.isdigit() for x in password):
        error_msg += "Password must contain at least 8 digits.\n"

    if not len(password) >= 8:
        error_msg += "The length of the password should greater then 8.\n"

    if len(error_msg) > 0:
        raise click.BadParameter(error_msg)
    else:
        return password 


@click.command('add-admin')
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, 
              type=click.UNPROCESSED, hide_input=True, 
              confirmation_prompt=True, callback=password_validation,
              help="""Password must contain at least a captal letter, 
              a lowercase letter, a digit and the length of the password should greater then 8."""
            )
def register_command(username, password):
    """Registers a new user."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        db.commit()
        click.echo('Register a admin user successfully')

    except db.IntegrityError:
        error = 'User {} is already registered.'.format(username)
        click.echo(error)
        click.echo('Register a admin user failed')
    

@click.command('change-password')
@click.option('--username', prompt=True)
@click.option('--newpassword', prompt=True, 
              hide_input=True, confirmation_prompt=True, 
              callback=password_validation,
              help="""Password must contain at least a captal letter, 
              a lowercase letter, a digit and the length of the password should greater then 8.""")
def change_password_command(username, newpassword):
    """Change password."""
    db = get_db()

    db.execute(
        "UPDATE users SET password = ? WHERE username = ?", (generate_password_hash(newpassword), username)
    )
    db.commit()

    click.echo('Change password successfully')


def recaptcha_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
            if request.method == 'POST':
                token = request.form['recaptcha_token']
                url = f'{current_app.config["reCAPTCHA_VERIFY_URL"]}?secret={current_app.config["reCAPTCHA_SECRET_KEY"]}&response={token}'
                verify_response = requests.post(url=url).json()
                print(verify_response)
                if verify_response['success'] == False or verify_response['score'] < 0.5:
                    return jsonify({
                        'message' : 'recaptcha failed',
                    }), 401
                else:
                    return view(**kwargs)
            else:
                return view(**kwargs) 
    return wrapped_view



@bp.route('/login', methods=['POST'])
@recaptcha_required
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # token = request.form['recaptcha_token']

        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return jsonify({'message' : 'successful'})
        else:
            return jsonify({'message' : 'failed'}), 403
     

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    db = get_db()

    if user_id is None:
        g.user = None
    else:
        g.user = db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('index'))
        
        return view(**kwargs)
    
    return wrapped_view


def init_auth(app):
    app.cli.add_command(register_command)
    app.cli.add_command(change_password_command)
