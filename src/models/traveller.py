import sqlite3
import os
from models.db import open_connection, close_connection
from security.encryption import encrypt_message, decrypt_message, load_symmetric_key
from controllers.rolecheck import is_authorized
from datetime import datetime


class Traveller:
    def __init__(self, id, first_name, last_name, date_of_birth, gender, streetname, house_number, zipcode,  city, email, phone_number, license_number, registration_date):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.streetname = streetname
        self.house_number = house_number
        self.zip_code = zipcode
        self.city = city
        self.email = email
        self.phone_number = phone_number
        self.license_number = license_number
        self.registration_date = registration_date


def create_traveller(first_name, last_name, date_of_birth, gender, street, house_number, zip_code, city, email, phone_number, license_number):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key() 
    
    date_time_now1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Format the date as needed
       # Ensure the symmetric key is loaded for encryption

    first_name_enc = encrypt_message(first_name, key)
    last_name_enc = encrypt_message(last_name, key)
    date_of_birth_enc = encrypt_message(date_of_birth, key)
    gender_enc = encrypt_message(gender, key)
    street_enc = encrypt_message(street, key)
    house_number_enc = encrypt_message(house_number, key)
    zip_code_enc = encrypt_message(zip_code, key)
    city_enc = encrypt_message(city, key)
    email_enc = encrypt_message(email, key)
    phone_number_enc = encrypt_message(phone_number, key)
    license_number_enc = encrypt_message(license_number, key)
    registration_date_enc = encrypt_message(date_time_now1, key) # Use the encrypted registration date


    try:
        cursor.execute('''
                    INSERT INTO travellers (first_name, last_name, date_of_birth, gender, street, house_number, zip_code, city, email, phone_number, license_number, registration_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name_enc, last_name_enc, date_of_birth_enc, gender_enc, street_enc, house_number_enc, zip_code_enc, city_enc, email_enc, phone_number_enc, license_number_enc, registration_date_enc))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"An error occurred while creating traveller: {e}")
        return False
    finally:
        close_connection(conn)


def list_travellers(current_user):
        if not is_authorized(current_user.role, 'list_travellers'):
            print("You do not have permission to view travellers.")
            return

        conn = open_connection()
        cursor = conn.cursor()
        key = load_symmetric_key()  # Ensure the symmetric key is loaded for decryption

        try:
            cursor.execute('SELECT * FROM travellers')
            rows = cursor.fetchall()
            travellers = []

            for row in rows:
                id = row[0]
                first_name = decrypt_message(row[1], key)
                last_name = decrypt_message(row[2], key)
                date_of_birth = decrypt_message(row[3], key)
                gender = decrypt_message(row[4], key)
                streetname = decrypt_message(row[5], key)
                house_number = decrypt_message(row[6], key)
                zipcode = decrypt_message(row[7], key)
                city = decrypt_message(row[8], key)
                email = decrypt_message(row[9], key)
                phone_number = decrypt_message(row[10], key)
                license_number = decrypt_message(row[11], key)
                registration_date = decrypt_message(row[12], key)

                traveller = Traveller(
                id, first_name, last_name, date_of_birth, gender, 
                streetname, house_number, zipcode, city, 
                email, phone_number, license_number, registration_date
                )
                travellers.append(traveller)
              
            return travellers
        except sqlite3.Error as e:
            print(f"An error occurred while listing travellers: {e}")
            return []
        finally:
            close_connection(conn)

def find_travellers(query):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()

    try:
        # Step 1: only retrieve the necessary fields for searching
        cursor.execute("""
            SELECT id, first_name, last_name, street, email, license_number
            FROM travellers
        """)
        rows = cursor.fetchall()
        query = query.lower()
        matched_ids = []

        for row in rows:
            decrypted = {
                "id": str(row[0]),
                "first_name": decrypt_message(row[1], key),
                "last_name": decrypt_message(row[2], key),
                "street": decrypt_message(row[3], key),
                "email": decrypt_message(row[4], key),
                "license_number": decrypt_message(row[5], key)
            }

            searchable_values = [
                decrypted['id'], 
                decrypted['first_name'], 
                decrypted['last_name'], 
                decrypted['street'], 
                decrypted['email'], 
                decrypted['license_number']
            ]

            if any(query in str(value).lower() for value in searchable_values):
                matched_ids.append(row[0])

        # Step 2: only retrieve details of matches
        results = []
        for traveller_id in matched_ids:
            cursor.execute("""
                SELECT id, first_name, last_name, date_of_birth, gender,
                       street, house_number, zip_code, city,
                       email, phone_number, license_number, registration_date
                FROM travellers WHERE id = ?
            """, (traveller_id,))
            row = cursor.fetchone()
            if not row:
                continue
            traveller = {
                'id': str(row[0]),
                'first_name': decrypt_message(row[1], key),
                'last_name': decrypt_message(row[2], key),
                'date_of_birth': decrypt_message(row[3], key),
                'gender': decrypt_message(row[4], key),
                'street': decrypt_message(row[5], key),
                'house_number': decrypt_message(row[6], key),
                'zip_code': decrypt_message(row[7], key),
                'city': decrypt_message(row[8], key),
                'email': decrypt_message(row[9], key),
                'phone_number': decrypt_message(row[10], key),
                'license_number': decrypt_message(row[11], key),
                'registration_date': decrypt_message(row[12], key)
            }
            results.append(traveller)

        return results
    except Exception as e:
        print("DB Error (find_travellers):", e)
        return []
    finally:
        close_connection(conn)

def update_traveller(customer_id, fields: dict):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()

    try:
        encrypted_fields = {}

        for field_name, field_value in fields.items():
            if isinstance(field_value, str):
                encrypted_fields[field_name] = encrypt_message(field_value, key)
            else:
                encrypted_fields[field_name] = field_value

        set_clause = ', '.join(f"{key} = ?" for key in fields.keys())
        values = list(encrypted_fields.values())
        values.append(customer_id)

        cursor.execute(f'''
            UPDATE travellers
            SET {set_clause}
            WHERE id = ?
        ''', values)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"An error occurred while updating traveller: {e}")
        return False
    finally:
        close_connection(conn)

def delete_traveller(customer_id):
    conn = open_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            DELETE FROM travellers WHERE id = ?
        ''', (customer_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"An error occurred while deleting traveller: {e}")
        return False
    finally:
        close_connection(conn)

