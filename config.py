import mysql.connector
def connect():
    mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Naani@4127",
            database="transaction"
    )
    return mydb