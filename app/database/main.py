import os

import psycopg2


def create_users_table():
    connection = None
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone_number VARCHAR(15),
        address TEXT NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        connection = psycopg2.connect(os.getenv('POSTGRES_URL'))
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Checked and created 'users' table if not existed.")
    except psycopg2.DatabaseError as error:
        print(f"Error occurred: {error}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
