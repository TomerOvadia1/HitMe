from flask_mysqldb import MySQL
from HitMe import app, mysql
from collections import namedtuple
from db import Moods, Types
from MySQLdb import escape_string as thwart

"""
Song container
"""
Song = namedtuple('Song',
                  ['id',
                   'title',
                   'tempo',
                   'hotness',
                   'loudness',
                   'album_name',
                   'year',
                   'artist_name'
                   ])


class Playlist:
    def __init__(self, ptype, mood, name=None, songs=None, pid=None):
        # just a sanity check
        if mood not in Moods.available_moods():
            raise Exception("Unrecognized Playlist Mood")
        if ptype not in Types.available_types():
            raise Exception("Unrecognized Playlist Type")

        self.mood = mood
        self.ptype = ptype
        self.name = name if name else 'Your Playlist'
        self.songs = songs if songs else []
        self.id = pid

    def generate_from_db(self):
        """
        Generates playlist's songs from the database.
        :return: None
        """
        with app.test_request_context():
            cur = mysql.connection.cursor()
            # We first set the required parameters for the query
            cur.execute(f"SET @type_rows = 0, @mood_rows = 0, @hot1 = 0, @hot2=0, @hot3 = 0, @hot4 = 0;")
            # Filter songs by params , get their IDs
            mf = Moods.mood_from_string(self.mood)
            tf = Types.type_from_string(self.ptype)
            query = Playlist.filter_query(mf, tf)
            # Query to db
            cur.execute(query)
            mysql.connection.commit()
            res = cur.fetchall()
            cur.close()
            # Get all the songs data
            cur = mysql.connection.cursor()
            songs = []
            # Generate song object from IDs
            for row in res:
                query = f"SELECT songs.song_id," \
                    f" songs.title," \
                    f" songs.tempo," \
                    f" songs.hotness," \
                    f" songs.loudness," \
                    f" songs.album_name," \
                    f" songs.year," \
                    f"artists.name" \
                    f" FROM songs,artists " \
                    f"WHERE songs.artist_id = artists.artist_id " \
                    f"AND songs.song_id='{row[3]}';"
                cur.execute(query)
                mysql.connection.commit()
                song = cur.fetchone()
                songs.append((Song(*song)))
            cur.close()
            self.songs = songs

    @staticmethod
    def filter_query(mood_filter, type_filter):
        return f"WITH hotness_table AS (WITH mood_table AS(WITH type_table AS " \
            f"(SELECT (@type_rows := @type_rows+1) AS num, " \
            f"song_id, artist_id ,title, tempo, loudness, hotness, " \
            f" tempo * {type_filter.tempo_weight} + loudness * {type_filter.loudness_weight} AS myfunc  " \
            f"FROM songs  " \
            f"WHERE tempo > {type_filter.tempo_lower} AND tempo < {type_filter.tempo_upper} " \
            f"AND loudness < {type_filter.loudness_upper} AND  " \
            f"loudness > {type_filter.loudness_lower}  " \
            f"ORDER BY myfunc) " \
            f"(SELECT *, @type_rows FROM type_table)) " \
            f"SELECT (@mood_rows := @mood_rows+1) AS num2 ,num, " \
            f"song_id, artist_id ,title, tempo, loudness, hotness, myfunc, @row_number_running FROM mood_table " \
            f"WHERE num between ((({mood_filter.lower_bound})*@type_rows)) and " \
            f" (({mood_filter.upper_bound})*@type_rows) ORDER BY rand()) " \
            f"(SELECT * FROM (SELECT (@hot1 := @hot1+1) AS num3, num2, num,song_id, artist_id ,title, tempo, " \
            f"loudness, hotness, myfunc, @type_rows, @mood_rows, @hot1 " \
            f"FROM hotness_table  " \
            f"WHERE hotness = 0 ORDER BY num3) AS T1 " \
            f"WHERE num3 BETWEEN 1 and (@hot1/@mood_rows)*15) " \
            f"UNION " \
            f"(SELECT * FROM (SELECT (@hot2 := @hot2+1) AS num3, num2, num, song_id, artist_id ,title, tempo, " \
            f"loudness, hotness, myfunc, @type_rows, @mood_rows, @hot2 " \
            f"FROM hotness_table  " \
            f"WHERE hotness BETWEEN 0.18 and 0.4 ORDER BY num3) AS T2 " \
            f"WHERE num3 BETWEEN 1 and (@hot2/@mood_rows)*15) " \
            f"UNION " \
            f"(SELECT * FROM (SELECT (@hot3 := @hot3+1) AS num3, num2, num, song_id, artist_id ,title, tempo, " \
            f"loudness, hotness, myfunc, @type_rows, @mood_rows, @hot3 " \
            f"FROM hotness_table  " \
            f"WHERE hotness BETWEEN 0.4 and 0.7 ORDER BY num3) AS T3 " \
            f"WHERE num3 BETWEEN 1 and (@hot3/@mood_rows)*15) " \
            f"UNION " \
            f"(SELECT * FROM (SELECT (@hot4 := @hot4+1) AS num3, num2, num, song_id, artist_id ,title, tempo, " \
            f"loudness, hotness, myfunc, @type_rows, @mood_rows, @hot4 " \
            f"FROM hotness_table  " \
            f"WHERE hotness BETWEEN 0.7 and 1 ORDER BY num3) AS T4 " \
            f"WHERE num3 BETWEEN 1 and 5)"

    @staticmethod
    def json_to_playlist(playlistJson):
        """
        Generates a playlist object , from an existing HTML page , containing the required data.
        :param playlistJson:
        :return: Playlist object
        """

        with app.test_request_context():
            i = 1
            ids = []
            # Get parameters from json object
            playlist_name = playlistJson['name']
            mood = playlistJson['mood']
            ptype = playlistJson['ptype']
            songs = []
            # Get all songs ids
            for _id in playlistJson['songs']:
                ids.append(_id)
                cur = mysql.connection.cursor()
                cmd = f"SELECT songs.song_id," \
                    f" songs.title," \
                    f" songs.tempo," \
                    f" songs.hotness," \
                    f" songs.loudness," \
                    f" songs.album_name," \
                    f" songs.year," \
                    f"artists.name" \
                    f" FROM songs,artists " \
                    f"WHERE songs.artist_id = artists.artist_id " \
                    f"AND songs.song_id='{thwart(_id).decode()}';"
                # Query to db
                cur.execute(cmd)
                mysql.connection.commit()
                res = cur.fetchone()
                cur.close()
                song = Song(*res)
                songs.append(song)
                i += 1
            return Playlist(ptype, mood, playlist_name, songs)

    def save_playlist(self, username):
        """
        Save current playlist to database
        :param username:
        :return:
        """
        from db.User import get_user

        with app.test_request_context():
            # get User object by username
            user = get_user(username)
            if not user:
                raise KeyError('User does not exist')
            playlist_id = self._new_db_playlist(user)
            self._insert_playlist_songs(playlist_id)

    def _new_db_playlist(self, user):
        """
        Create a new playlist on database
        :param user:
        :return: Playlist ID on database
        """
        with app.test_request_context():
            # Insert a new playlist
            cur = mysql.connection.cursor()
            cmd = f"INSERT INTO playlists(user_id,name,mood,type)" \
                f" VALUES('{thwart(str(user.id)).decode()}'," \
                f"'{thwart(self.name).decode()}'," \
                f"'{thwart(self.mood).decode()}'," \
                f"'{thwart(self.ptype).decode()}'" \
                f");"
            # print(cmd)
            cur.execute(cmd)
            mysql.connection.commit()
            # Get created playlist's ID
            cmd = "SELECT LAST_INSERT_ID();"
            cur.execute(cmd)
            mysql.connection.commit()
            id = cur.fetchone()[0]
            # print(id)
            cur.close()
            return id

    def _insert_playlist_songs(self, playlist_id):
        """
        Save playlist's songs on database
        :param playlist_id:
        :return: None
        """
        with app.test_request_context():
            cur = mysql.connection.cursor()
            for song in self.songs:
                cmd = f"INSERT INTO playlists_songs " \
                    f"VALUES('{thwart(str(playlist_id)).decode()}'," \
                    f"'{thwart(song.id).decode()}')"
                print(cmd)
                cur.execute(cmd)
                mysql.connection.commit()
            cur.close()

    @staticmethod
    def get_playlists_songs(playlist_id):
        """

        :param playlist_id:
        :return: Returns a list of Song objects related to given playlist_id
        """
        with app.test_request_context():
            cur = mysql.connection.cursor()
            cmd = f"SELECT" \
                f"    song_list.song_id," \
                f"    song_list.title," \
                f"    song_list.tempo," \
                f"    song_list.hotness," \
                f"    song_list.loudness," \
                f"    song_list.album_name," \
                f"    song_list.year," \
                f"    artists.name" \
                f" FROM (" \
                f" 	SELECT distinct songs.*" \
                f" 	FROM playlists_songs,songs" \
                f" 	WHERE playlists_playlist_id = '{thwart(str(playlist_id)).decode()}'" \
                f"     AND songs.song_id = playlists_songs.songs_song_id" \
                f" ) as song_list , artists" \
                f" WHERE song_list.artist_id = artists.artist_id"
            # print(cmd)
            cur.execute(cmd)
            mysql.connection.commit()
            songs = cur.fetchall()
            songs = [Song(*s) for s in songs]
            # print(songs[1])
            cur.close()
            return songs

    @staticmethod
    def get_playlist_by_pid(playlist_id):
        """
        :param playlist_id:
        :return: Returns Playlist Object by playlist_id
        """
        with app.test_request_context():
            cur = mysql.connection.cursor()
            condition = f"playlist_id = '{thwart(str(playlist_id)).decode()}'"
            # Get playlist object by ID
            playlist = Playlist.get_playlist_data_by(condition)[0]
            # fill playlist's songs
            playlist.songs = Playlist.get_playlists_songs(playlist_id)
            return playlist

    @staticmethod
    def get_playlist_data_by(condition):
        """
        :param condition:
        :return: Returns all of the playlist data by given condition
        """
        with app.test_request_context():
            c = mysql.connection.cursor()
            cmd = f"SELECT * FROM playlists WHERE {condition}"
            # print(cmd)
            c.execute(cmd)
            playlists = c.fetchall()
            if not playlists:
                return []
            mysql.connection.commit()
            c.close()
            playlists = [Playlist(playlist[4], playlist[3], name=playlist[2], pid=playlist[0]) for playlist in
                         playlists]
            return playlists

    def jsonify(self):
        temp = Playlist(self.ptype, self.mood, self.name, [song.id for song in self.songs])
        return temp.__dict__
