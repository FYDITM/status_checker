import sqlite3
from datetime import datetime, timedelta

# schemat tabeli chan_stats:
# id (autoinkrementowany klucz) | chan_name (text) | date (jako str)
# | ok (czy jeździ, 1 lub 0) | users (ile online) | posts_per_hour (real)

# schemat tabeli posts:
# id (autoinkrementowany klucz) | chan_name (text) | date (jako timestamp) | board (text) | post_id (integer)
dateformat = "%Y-%m-%d %H:%M:%S.%f"


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

    def get_stats(self, chan_name, date_from, date_to):
        self.cur.execute("SELECT * FROM chan_stats WHERE chan_name=? AND date BETWEEN ? and ?",
                         (chan_name, date_from, date_to))
        return self.cur.fetchall()  # [(id, chan_name, date, ok, users, posts_per_hour)]

    def parse_stats(self, stats):
        """
        Zwraca sparsowane dane w formacie [(date, chan_name, users, posts_per_hour)]
        """
        return list(map(lambda x: (datetime.strptime(x[2], dateformat), x[1], x[4], x[5]), stats))

    def calculate_average(self, chan_name, date_from, date_to):
        """
        Zwraca wyliczone średnie w formacie [(period, avg_users, avg_posts)],
        gdzie period to poszczególne okresy (dni lub miesiące)
        """
        stats_list = self.parse_stats(self.get_stats(chan_name, date_from, date_to))
        start_date = stats_list[0][0]
        end_date = stats_list[len(stats_list) - 1][0]
        period = end_date - start_date
        if period.days < 3:
            return list(map(lambda x: (x[0].strftime("%Y-%m-%d %H:%M"), x[2], x[3]), stats_list))
        result = []
        day = start_date.date()
        count = 0
        posts_total = 0
        users_total = 0
        for record in stats_list:
            if record[0].date() == day:
                users_total += record[2]
                posts_total += record[3]
                count += 1
            else:
                if count == 0:
                    continue
                result.append((day, users_total / count, posts_total / count))
                day = record[0].date()
                count = 1
                users_total = record[2]
                posts_total = record[3]
        if period.days >= 90:
            months_result = []
            month = start_date.month
            count = 0
            posts_total = 0
            users_total = 0
            for record in result:
                if record[0].month == month:
                    users_total += record[1]
                    posts_total += record[2]
                    count += 1
                else:
                    months_result.append((month, users_total / count, posts_total / count))
                    month = record[0].month
                    count = 1
                    users_total = record[1]
                    posts_total = record[2]
            result = months_result
        return result

    def dispose(self):
        self.conn.close()
