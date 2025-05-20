import sqlite3
import numpy as np

def view_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('face_auth.db')
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()
        
        print("\n=== Registered Users ===")
        print("Total users:", len(users))
        print("\nUser Details:")
        print("-" * 50)
        
        for user in users:
            user_id, username = user
            print(f"ID: {user_id}")
            print(f"Username: {username}")
            print("-" * 50)
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_database() 