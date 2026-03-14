import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
    
    def init_db(self):
        # Existing table creation code ...
        
        # New table for event registrations
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, event_id)
            )
        ''')
        self.conn.commit()

    def register_for_event(self, user_id, event_id):
        try:
            self.cursor.execute('''
                INSERT INTO event_registrations (user_id, event_id)
                VALUES (?, ?)
            ''', (user_id, event_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def is_registered_for_event(self, user_id, event_id):
        self.cursor.execute('''
            SELECT COUNT(*) FROM event_registrations
            WHERE user_id = ? AND event_id = ?
        ''', (user_id, event_id))
        return self.cursor.fetchone()[0] > 0
