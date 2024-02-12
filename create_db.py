import sqlite3

# Подключение к базе данных (файлу). Если файла нет, он будет создан.
conn = sqlite3.connect('fakel_data.db')

# Создание объекта cursor, который позволяет вам выполнять SQL команды
cursor = conn.cursor()

# Создание таблицы
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    product_name TEXT NOT NULL,
    specifications TEXT,
    description TEXT,
    size_and_price TEXT
)
''')

# Закрытие подключения к БД
conn.close()
