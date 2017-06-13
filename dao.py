import sqlite3
from datetime import datetime, timedelta

# schemat tabeli chan_stats:
# id (autoinkrementowany klucz) | chan_name (text) | date (jako timestamp) | ok (czy jeździ, 1 lub 0) | users (ile online) | posts_per_hour (real)

# schemat tabeli posts:
# id (autoinkrementowany klucz) | chan_name (text) | date (jako str) | board (text) | post_id (integer)


class DatabaseConnector():
    FILENAME = "rowerek.db"

    def __init__(self):
        self.conn = sqlite3.connect(self.FILENAME)
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chan_stats'")
        i = self.cur.fetchall()
        if len(i) < 1:
            self.setup_database()

    def setup_database(self):
        self.cur.execute(
            "CREATE TABLE chan_stats (id INTEGER PRIMARY KEY, chan_name TEXT, date TEXT, ok INTEGER, users INTEGER, posts_per_hour REAL)")
        self.cur.execute(
            "CREATE TABLE posts (id INTEGER PRIMARY KEY, chan_name TEXT, date REAL, board TEXT, post_id INTEGER)")
        self.conn.commit()

    def insert_stats_record(self, chan_name, date, ok, users, posts_per_hour):
        self.cur.execute("INSERT INTO chan_stats (chan_name, date, ok, users, posts_per_hour) VALUES (?, ?, ?, ?, ?)",
                         (chan_name, date, ok, users, posts_per_hour))
        self.conn.commit()

    def insert_posts_record(self, chan_name, date, board, post_id):
        self.cur.execute("INSERT INTO posts (chan_name, date, board, post_id) VALUES (?,?,?,?)",
                         (chan_name, date, board, post_id))
        self.conn.commit()

    def get_post_number_hour_ago(self, chan_name, board):
        lower_time = datetime.now() - timedelta(hours=1, minutes=15)
        greater_time = datetime.now() - timedelta(minutes=45)
        lower_timestamp = lower_time.timestamp()
        greater_timestamp = greater_time.timestamp()
        self.cur.execute("SELECT post_id FROM posts WHERE chan_name=? AND board=? AND date BETWEEN ? AND ?",
                         (chan_name, board, lower_timestamp, greater_timestamp))
        postId = self.cur.fetchone()  # nawet jeśli więcej niż jeden to i tak wystarczająco blisko
        if postId:
            return postId[0]
        else:
            return None

    #def get_stats(self, chan_name, date_from, date_to)

    def dispose(self):
        self.conn.close()
