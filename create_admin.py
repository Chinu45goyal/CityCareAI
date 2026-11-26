
from werkzeug.security import generate_password_hash
from getpass import getpass
from database import get_connection

print("===== CREATE ADMIN ACCOUNT =====")

username = input("Enter admin username: ").strip()
password = getpass("Enter admin password: ")
confirm_password = getpass("Confirm admin password: ")

if not username or not password:
    print("Username and password cannot be empty.")

elif password != confirm_password:
    print("Passwords do not match.")

else:
    connection = None
    cursor = None

    try:
        password_hash = generate_password_hash(password)

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO admins (username, password_hash)
            VALUES (%s, %s)
            """,
            (username, password_hash)
        )

        connection.commit()

        print("\nAdmin account created successfully!")
        print("Username:", username)
        print("Password stored securely as a hash.")

    except Exception as error:
        if connection:
            connection.rollback()

        print("Error creating admin:", error)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
