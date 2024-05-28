
# create a class sqlitebd using sqlite3 lib with the following methods:
#     - __init__(): Initialize the sqlitebd object with the database name.
#     - create_table(): Create a table with the name provided.
#     - insert_values(): Insert values into the table.
#     - fetch_values(): Fetch values from the table.
#     - update_values(): Update values in the table.
#     - delete_values(): Delete values from the table.

import sqlite3

class SqliteDB:
    def __init__(self, db_name="appointments.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        if not self.cursor:
            print("Error connecting to database")
        check_table = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dr_appointments'")
        if not check_table.fetchall():
            self.create_table()

    def create_table(self, table_name="dr_appointments", columns=["doctor_name","doctor_phone",
                                                                  "patient_email", "appointment_timeslot",
                                                                  "location"]):
        columns_str = ', '.join(columns)
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")
        self.conn.commit()
        print(f"table :{table_name} created with columns: {columns_str}")

    def insert_values(self, values, table_name="dr_appointments"):
        placeholders = ', '.join(['?' for _ in values])
        self.cursor.execute(f"INSERT INTO {table_name}(doctor_name, doctor_phone, patient_email, appointment_timeslot, location) VALUES ({placeholders})", values)
        self.conn.commit()

    def fetch_values(self,patient_email, table_name="dr_appointments"):
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE patient_email='{patient_email}'")
        return self.cursor.fetchall()

    def update_values(self, set_statement, where_statement, table_name="dr_appointments"):
        self.cursor.execute(f"UPDATE {table_name} SET {set_statement} WHERE {where_statement}")
        self.conn.commit()

    def delete_values(self,  where_statement, table_name="dr_appointments"):
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {where_statement}")
        self.conn.commit()