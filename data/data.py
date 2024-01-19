import sqlite3 as sq


class Database(object):

    def __init__(self, path):
        self.connection = sq.connect(path)
        self.connection.execute('pragma foreign_keys = on')
        self.connection.commit()
        self.cur = self.connection.cursor()

    def create_tables(self):
        self.query(
            'CREATE TABLE IF NOT EXISTS users ('
            'id INTEGER PRIMARY KEY,'
            'telegram_id INTEGER,'
            'mt5_login TEXT,'
            'mt5_password TEXT,'
            'mt5_server TEXT,'
            'initial_deposit INTEGER)')
        self.query(
            'CREATE TABLE IF NOT EXISTS session_results ('
            'id INTEGER PRIMARY KEY,'
            'user_id INTEGER,'
            'session_start_time TEXT,'
            'total_profit_percentage REAL)')
        self.query(
            'CREATE TABLE IF NOT EXISTS deals ('
            'id INTEGER PRIMARY KEY,'
            'user_id INTEGER,'
            'open_time TEXT,'
            'close_time TEXT,'
            'symbol TEXT,'
            'volume INTEGER,'
            'profit_percentage REAL,'
            'session_id INTEGER,'
            'FOREIGN KEY (session_id) REFERENCES session_results(id))')

    def query(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.connection.commit()

    def fetchone(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()

    def __del__(self):
        self.connection.close()