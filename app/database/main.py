import hashlib
import os

import psycopg2


def create_users_table():
    connection = None
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        email VARCHAR(255) UNIQUE NOT NULL,
        phone_number VARCHAR(15),
        address VARCHAR(100),
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


def insert_user(email, password):
    connection = None
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    insert_user_sql = """
       INSERT INTO users (email, password_hash) 
       VALUES (%s, %s);
       """

    try:
        connection = psycopg2.connect(os.getenv('POSTGRES_URL'))
        cursor = connection.cursor()
        cursor.execute(insert_user_sql, (email, password_hash))
        connection.commit()
        print(f"User {email} added successfully.")
    except psycopg2.DatabaseError as error:
        print(f"Error occurred: {error}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
