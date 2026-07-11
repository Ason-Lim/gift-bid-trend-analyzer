#!/usr/bin/env python3
import os
import sqlite3
import re

# We read from the local SQLite DB inside the existing project
SQLITE_DB_PATH = "/Users/mom/anti_online/data/smallbiz_programs.db"
DATABASE_URL = os.environ.get('DATABASE_URL')

def migrate():
    if not DATABASE_URL or not (DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')):
        print("Error: DATABASE_URL environment variable is missing or invalid.")
        print("Please set it before running this script.")
        print("Example: DATABASE_URL='postgresql://user:pass@host/gift_trend_db' python3 migrate_db.py")
        return

    # Check if local SQLite DB exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Error: Local SQLite DB not found at {SQLITE_DB_PATH}")
        return

    print("Connecting to local SQLite database...")
    lite_conn = sqlite3.connect(SQLITE_DB_PATH)
    lite_cur = lite_conn.cursor()

    try:
        lite_cur.execute("SELECT * FROM gift_bids")
        rows = lite_cur.fetchall()
        colnames = [desc[0] for desc in lite_cur.description]
        print(f"Found {len(rows)} records in SQLite gift_bids table.")
    except Exception as e:
        print(f"Error reading SQLite: {e}")
        lite_conn.close()
        return

    print("Connecting to target PostgreSQL database...")
    import psycopg2
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
        
    try:
        pg_conn = psycopg2.connect(url)
        pg_cur = pg_conn.cursor()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        lite_conn.close()
        return

    # Ensure tables exist in target PostgreSQL
    print("Ensuring tables are initialized in PostgreSQL...")
    try:
        # Create table query equivalent to database.py
        pg_cur.execute('''
            CREATE TABLE IF NOT EXISTS gift_bids (
                id SERIAL PRIMARY KEY,
                institution VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                announcement_date VARCHAR(50) NOT NULL,
                deadline VARCHAR(50) NOT NULL,
                department VARCHAR(255) NOT NULL,
                manager VARCHAR(255) NOT NULL,
                contact VARCHAR(255) NOT NULL,
                budget VARCHAR(255) NOT NULL,
                link TEXT NOT NULL,
                hwpx_parsed_text TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT '입찰중',
                institution_type VARCHAR(50) NOT NULL
            )
        ''')
        pg_conn.commit()
    except Exception as e:
        print(f"Error creating PostgreSQL table: {e}")
        pg_conn.close()
        lite_conn.close()
        return

    # Migrate data
    migrated_count = 0
    skipped_count = 0

    print("Migrating records...")
    for row in rows:
        # Map tuple to dict using column names
        data = dict(zip(colnames, row))
        
        # Check if record already exists in Postgres
        pg_cur.execute("SELECT id FROM gift_bids WHERE title = %s AND institution = %s", (data['title'], data['institution']))
        exists = pg_cur.fetchone()
        
        if exists:
            skipped_count += 1
            continue
            
        try:
            pg_cur.execute('''
                INSERT INTO gift_bids (
                    institution, title, announcement_date, deadline, department, manager,
                    contact, budget, link, hwpx_parsed_text, status, institution_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                data['institution'], data['title'], data['announcement_date'], data['deadline'],
                data['department'], data['manager'], data['contact'], data['budget'], data['link'],
                data['hwpx_parsed_text'], data.get('status', '입찰중'), data['institution_type']
            ))
            migrated_count += 1
        except Exception as e:
            print(f"Error migrating record '{data['title']}': {e}")
            pg_conn.rollback()
            pg_conn.close()
            lite_conn.close()
            return

    pg_conn.commit()
    print(f"Migration completed successfully.")
    print(f"-> Migrated: {migrated_count} records")
    print(f"-> Skipped (already exists): {skipped_count} records")

    pg_conn.close()
    lite_conn.close()

if __name__ == '__main__':
    migrate()
