import sqlite3
import os
current_path = os.path.dirname(os.path.abspath(__file__))

class MainDB():
    def __init__(self):
        self.db_path = current_path+'/db/blfxl.db'
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            connection = sqlite3.connect(self.db_path)
            self.connection = connection
            self.cursor = connection.cursor()
        except:
            print('error with connect to db')
        try:
            self.create_tables()
        except:
            pass

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE connected_invoices
                     (id integer PRIMARY KEY, bl_inv_id TEXT, fxl_inv_id TEXT, connect_date TEXT, file_changed_in_bl INTEGER)''')

    def get_single_row(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    def insert(self, sql):
        self.cursor.execute(sql)
        self.save()

    def update(self, sql):
        self.cursor.execute(sql)
        self.save()

    def save(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

