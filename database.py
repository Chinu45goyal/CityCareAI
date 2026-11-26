import mysql.connector

def get_connection():

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="ai_city_intelligence"
    )

    return connection


if __name__ == "__main__":

    try:
        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("SELECT DATABASE()")
        print("Connected Database:", cursor.fetchone())

        cursor.execute("SELECT COUNT(*) FROM complaints")
        print("Total Complaints:", cursor.fetchone())

        cursor.execute("SELECT COUNT(*) FROM complaint_history")
        print("History Records:", cursor.fetchone())

        cursor.close()
        conn.close()

    except Exception as e:
        print("ERROR:", e)