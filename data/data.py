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
            'ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
            'login TEXT, '
            'password TEXT, '
            'server TEXT, '
            'deposite INTEGER, '
            'connect BOOL)')

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