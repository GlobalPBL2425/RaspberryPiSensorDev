import pymysql

def connect_to_mysql():
    try:
        # Database connection configuration
        connection = pymysql.connect(
            host="gpbl2425.cbpgnvn281xt.us-east-1.rds.amazonaws.com",
            port=3306,
            user="root",
            passwd="GPBL2425",  # Ensure the database name is correct
            db="GPBL2425",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )

        print("Connected to MySQL database!")

        # Example query to check the current database
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            if record and record['DATABASE()']:
                print(f"You are connected to database: {record['DATABASE()']}")
            else:
                print("No database is currently selected.")

        # Close the connection
        connection.close()
        print("MySQL connection is closed.")

    except pymysql.MySQLError as e:
        print(f"Error while connecting to MySQL: {e}")

if __name__ == "__main__":
    connect_to_mysql()
