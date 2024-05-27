import sqlite3

class Connect():
    def __init__(self, name) -> None:
        self.connection = sqlite3.connect(name)
        self.cursor = self.connection.cursor()
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                   user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username VARCHAR(30) NOT NULL UNIQUE,
                   password VARCHAR(255) NOT NULL,
                   telegram_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS musics (
                   music_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   req_user TEXT NOT NULL,
                   url_music TEXT,
                   name_music TEXT,
                   FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')
        self.connection.commit()
        
    def get_all(self):
        self.cursor = self.connection.cursor()
        sql = f'SELECT * FROM users'
        self.cursor.execute(sql)
        users = self.cursor.fetchall()
        return users
        
    def insert(self, username, password, telegram_id):
        self.cursor = self.connection.cursor()
        self.cursor.execute('INSERT INTO Users (username, password, telegram_id) VALUES (?, ?, ?)', (username, password, telegram_id))
        self.connection.commit()
        return 'Ok'
    
    def insert_search(self, user_id, username, url, name_music):
        self.cursor = self.connection.cursor()
        self.cursor.execute('INSERT INTO musics (user_id, req_user, url_music, name_music) VALUES (?, ?, ?, ?)', (user_id, username, url, name_music))
        self.connection.commit()
        return 'Ok'
    
    def get_user_telegram_id(self, telegram_id):
        self.cursor = self.connection.cursor()
        sql = f'SELECT * FROM users WHERE telegram_id = {telegram_id}'
        self.cursor.execute(sql)
        user = self.cursor.fetchone()
        return user
    
    def get_user_username(self, username):
        self.cursor = self.connection.cursor()
        sql = f'SELECT * FROM users WHERE username = "{username}"'
        self.cursor.execute(sql)
        user = self.cursor.fetchone()
        return user
    
    def update_user(self, username, telegram_id):
        user_id = self.get_user_username(username)[0]
        self.cursor = self.connection.cursor()
        sql = f'UPDATE users SET telegram_id = {telegram_id} WHERE user_id = {user_id}'
        self.cursor.execute(sql)
        self.connection.commit()
        
            
    def get_tracks(self, user_id):
        self.cursor = self.connection.cursor()
        sql = f'SELECT url_music, name_music FROM musics WHERE user_id = {user_id}'
        self.cursor.execute(sql)
        tracks = self.cursor.fetchall()
        """ search_tracks:list = []
        for track in tracks:
            search_tracks.append(tracks)
        return search_tracks """
        return tracks

    def __del__(self):
        self.connection.close()