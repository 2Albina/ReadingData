import sqlite3


def create_tables():
    conn = sqlite3.connect('ReadingData.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS currency_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        currency TEXT,
        rate REAL,
        UNIQUE(date, currency)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relative_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cur_date TEXT,
        currency TEXT,
        relative_change REAL,
        UNIQUE(cur_date, currency)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parameters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        base_date TEXT
    )
    ''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_tables()
