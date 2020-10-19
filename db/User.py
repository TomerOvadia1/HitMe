from HitMe import app, mysql
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
from collections import namedtuple


"""
A User container
"""
User = namedtuple('User',
                  ['id',
                   'username',
                   'email',
                   'birth_date',
                   'hashed_password'
                   ])


def create_user(form):
    """
    Creates a user on database
    :param form:
    :return:
    """
    with app.test_request_context():
        username = form.username.data
        # Encrypt password
        password = sha256_crypt.encrypt(str(form.password.data))
        birth_date = form.birth_date.data
        email = form.email.data
        # sql user exists query execution
        cur = mysql.connection.cursor()
        user = get_user(form.username.data)
        # if user with that name already exists
        if user:
            return 0
        # thwart is used to escape chars correctly
        cmd = f"INSERT INTO users (username,password,birth_date,email) VALUES ( '{thwart(username).decode()}'," \
            f"'{thwart(password).decode()}','{thwart(str(birth_date)).decode()}','{thwart(email).decode()}')"
        # print(cmd)
        cur.execute(cmd)
        mysql.connection.commit()
        cur.close()
        # TODO: IS THIS NECESSARY ?
        # mysql.connection.close()
        # gc.collect()
        return 1


def validate_login(form):
    """
    Validates user login
    :param form:
    :return:
    """
    # Check if username matches an existing account
    user = get_user(form.username.data)
    # if not return 0
    if not user:
        return None
    # Validates hashed password
    if sha256_crypt.verify(form.password.data, user.hashed_password):
        return user.username
    return None


def get_user(username):
    """
    Returns user info by username. usernames are unique.
    :param username:
    :return:
    """
    with app.test_request_context():
        c = mysql.connection.cursor()
        cmd = f"SELECT * FROM users WHERE username = '{thwart(username).decode()}'"
        # Query to db
        c.execute(cmd)
        user = c.fetchone()
        if not user:
            return 0
        mysql.connection.commit()
        c.close()
        return User(*user)


def get_user_playlists(username):
    """
    Get user playlist by user name
    :param username:
    :return:
    """
    from db.Playlist import Playlist

    with app.test_request_context():
        user = get_user(username)
        if not user:
            return []
        condition = f"user_id = '{thwart(str(user.id)).decode()}'"
        return Playlist.get_playlist_data_by(condition)
