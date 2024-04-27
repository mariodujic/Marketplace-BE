import psycopg2
from psycopg2.extras import RealDictCursor


def insert_user(first_name, last_name, email, phone_number, address, password):
    conn = psycopg2.connect(
        dbname='your_dbname',
        user='your_user',
        password='your_password',
        host='localhost'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Insert data into the database
    cursor.execute(
        """
        INSERT INTO users (first_name, last_name, email, phone_number, address, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, phone_number, address, password)
    )
    conn.commit()
    cursor.close()
    conn.close()
