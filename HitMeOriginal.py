from flask import Flask, render_template, url_for, flash, redirect, request, session
from forms import RegistrationForm, LoginForm
from flask_mysqldb import MySQL
import concurrent.futures
from functools import wraps
import json

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'tomero222'
app.config['MYSQL_DB'] = 'hitmedb'

mysql = MySQL(app)

app.config['SECRET_KEY'] = '6fdc4c8ab35e140b3a70b3e5ca924e86'

TIMEOUT = 5
executers = concurrent.futures.ThreadPoolExecutor(max_workers=5)

from db import User, Moods, Types
import db.Playlist

# Template folder is for HTML files
# render_template is for rendering html static pages
# it can take html files with special python commands wrappers ,
# render it with python commands and its output is an html file

def login_required(f):
    '''
    Wrapper function to check if user is logged in
    :param f: function to wrap
    :return: login page with a flashed msg if user is not logged in
            else - the required page
    '''

    @wraps(f)
    def is_logged(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Log in is required', category='danger')
            return redirect(url_for('login'))

    return is_logged


@app.route('/', methods=['GET'])
@app.route('/home/', methods=['GET'])
def home():
    '''
    Home page
    :return:
    '''
    return render_template('home.html')


@app.route('/playlist_create/', methods=['GET', 'POST'])
@login_required
def playlist_create():
    """
    Create a playlist and display it by user request
    :return:
    """
    try:
        view_mode = False
        # user posted a save request
        if request.method == 'POST':
            # Get json representation of playlist
            playlistJson = json.loads(request.form.get('jsonPlaylist'))
            # Convert into playlist Object on thread-pool
            future = executers.submit(db.Playlist.Playlist.json_to_playlist, playlistJson)
            playlist = future.result(timeout=TIMEOUT)
            playlist.name = request.form.get('playlist_name')
            # Save playlist to db on thread-pool
            future = executers.submit(playlist.save_playlist, session['username'])
            future.result(timeout=TIMEOUT)
            view_mode = True
            return render_template('playlists.html', playlist=playlist,
                                   view_mode=view_mode)
        # Get args
        ptype = request.args.get('type').lower()
        mood = request.args.get('mood').lower()
        # If entered the required data
        if ptype and mood:
            # User polluted HTTP request with wrong type or mood
            if (mood not in Moods.available_moods() or
                    ptype not in Types.available_types()):
                flash('Mood/Type Error', category='danger')
                return render_template('home.html')
            playlist = db.Playlist.Playlist(ptype, mood)
            # Execute on thread-pool
            future = executers.submit(playlist.generate_from_db)
            future.result(timeout=TIMEOUT)
            return render_template('playlists.html', playlist=playlist,
                                   view_mode=view_mode)
        else:
            if not ptype:
                flash('A Type must be selected!', category='danger')
            if not mood:
                flash('A Mood must be selected!', category='danger')
            return render_template('home.html')
    except Exception as e:
        print(e)
        flash('Unexpected error occurred. Please try again', category='danger')
        return render_template('home.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    '''
    Login page
    :return:
    '''
    form = LoginForm()
    try:
        # Create a form for login
        # if user tries to login while already logged in
        if 'logged_in' in session:
            flash(f"Your'e already logged in!", category='success')
            return render_template('login.html', title='Register', form=form)

        if form.validate_on_submit():
            future = executers.submit(User.validate_login, form)
            username = future.result(timeout=TIMEOUT)
            if not username:
                flash('Login Unsuccessful. Please check username and password', category='danger')
                return redirect(url_for('login'))
            # session data
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
    except Exception as e:
        flash('Unexpected error occurred on login', category='danger')
        print(e)
    return render_template('login.html', title='Login', form=form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    '''
    Register page
    :return:
    '''
    form = RegistrationForm()
    try:
        # if user tries to register while already logged in
        if 'logged_in' in session:
            flash(f"Your'e already logged in!", category='success')
            return render_template('register.html', title='Register', form=form)

        # If form validates , and user submitted a post request
        if form.validate_on_submit():
            future = executers.submit(User.create_user, form)
            created = future.result(timeout=TIMEOUT)
            # Check the status for user creation
            if not created:
                flash("Username is already taken", category='danger')
                return render_template('register.html', title='Register', form=form)
            flash(f'Account created for {form.username.data}!', category='success')
            # session data
            session['logged_in'] = True
            session['username'] = form.username.data
            return redirect(url_for('home'))
    except Exception as e:
        print(e)
        flash('Unexpected error occurred on registration', category='danger')
    return render_template('register.html', title='Register', form=form)


@app.route('/user/', methods=['GET', 'POST'])
@login_required
def user():
    try:
        if request.method == 'POST':
            p_id = request.form.get('selected_playlist')
            future = executers.submit(db.Playlist.Playlist.get_playlist_by_pid, p_id)
            playlist = future.result(timeout=TIMEOUT)
            return render_template('playlists.html', playlist=playlist, playlist_name=playlist.name, view_mode=True)
        playlists = User.get_user_playlists(session['username'])
        return render_template('user.html', playlists=playlists)
    except Exception as e:
        print(e)
        flash('Unexpected error occurred.', category='danger')
    return redirect(url_for('home'))


# @app.route('/about')
# def about():
#     return render_template('about.html', title='About')
#

@app.route('/logout/')
@login_required
def logout():
    try:
        session.clear()
        flash('You have been logged out!', category='info')
        return redirect(url_for('login'))
    except Exception as e:
        flash('Unexpected error occurred.', category='danger')
        return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
