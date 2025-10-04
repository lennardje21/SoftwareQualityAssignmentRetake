import sqlite3
from models.db import open_connection, close_connection
from security.encryption import encrypt_message, decrypt_message, load_symmetric_key
from logs.log import log_instance

class Scooter:
    def __init__(self, id, brand, model, serial_number, top_speed, battery_capacity, soc, soc_range_min, soc_range_max, location_latitude, location_longitude, out_of_service, mileage, last_maintenance_date=None):
    
        self.id = id
        self.brand = brand
        self.model = model
        self.serial_number = serial_number
        self.top_speed = top_speed
        self.battery_capacity = battery_capacity
        self.soc = soc
        self.soc_range_min = soc_range_min
        self.soc_range_max = soc_range_max
        self.location_latitude = location_latitude
        self.location_longitude = location_longitude
        self.out_of_service = out_of_service
        self.mileage = mileage
        self.last_maintenance_date = last_maintenance_date

def create_scooter(brand, model, serial_number, top_speed, battery_capacity, soc, soc_range_min, soc_range_max, location_latitude, location_longitude, out_of_service, mileage, last_maintenance_date=None):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()  # Ensure the symmetric key is loaded for encryption
    try:
        # Encrypt all relevant fields as strings
        brand_enc = encrypt_message(str(brand), key)
        model_enc = encrypt_message(str(model), key)
        serial_number_enc = encrypt_message(str(serial_number), key)
        top_speed_enc = encrypt_message(str(top_speed), key)
        battery_capacity_enc = encrypt_message(str(battery_capacity), key)
        soc_enc = encrypt_message(str(soc), key)
        soc_range_min_enc = encrypt_message(str(soc_range_min), key)
        soc_range_max_enc = encrypt_message(str(soc_range_max), key)
        location_latitude_enc = encrypt_message(str(location_latitude), key)
        location_longitude_enc = encrypt_message(str(location_longitude), key)
        out_of_service_enc = encrypt_message(str(out_of_service), key)
        mileage_enc = encrypt_message(str(mileage), key)
        last_maintenance_date_enc = encrypt_message(str(last_maintenance_date), key) if last_maintenance_date else None

        cursor.execute('''
            INSERT INTO scooters (
                brand, model, serial_number, top_speed, battery_capacity, soc, soc_range_min, soc_range_max,
                location_latitude, location_longitude, out_of_service, mileage, last_maintenance_date
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            brand_enc, model_enc, serial_number_enc, top_speed_enc, battery_capacity_enc, soc_enc, soc_range_min_enc,
            soc_range_max_enc, location_latitude_enc, location_longitude_enc, out_of_service_enc, mileage_enc, last_maintenance_date_enc
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"An error occurred while creating scooter: {e}")
        return False
    finally:
        close_connection(conn)

def list_scooters():
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()
    try:
        cursor.execute('SELECT * FROM scooters')
        rows = cursor.fetchall()
        scooters = []
        for row in rows:
            id = row[0]
            brand = decrypt_message(row[1], key)
            model = decrypt_message(row[2], key)
            serial_number = decrypt_message(row[3], key)
            top_speed = decrypt_message(row[4], key)
            battery_capacity = decrypt_message(row[5], key)
            soc = decrypt_message(row[6], key)
            soc_range_min = decrypt_message(row[7], key)
            soc_range_max = decrypt_message(row[8], key)
            location_latitude = decrypt_message(row[9], key)
            location_longitude = decrypt_message(row[10], key)
            out_of_service = decrypt_message(row[11], key) == 'True'
            mileage = decrypt_message(row[12], key)
            last_maintenance_date = decrypt_message(row[13], key) if row[13] else None

            scooters.append(Scooter(
                id, brand, model, serial_number, top_speed, battery_capacity, soc,
                soc_range_min, soc_range_max, location_latitude, location_longitude,
                out_of_service, mileage, last_maintenance_date
            ))
        return scooters
    except sqlite3.Error as e:
        print(f"An error occurred while listing scooters: {e}")
        return []
    finally:
        close_connection(conn)


def delete_scooter(serial_number):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()
    
    try:
        # First find the scooter with the given serial_number
        cursor.execute('SELECT id FROM scooters')
        rows = cursor.fetchall()
        # scooter_id = None

        # First find all rows
        cursor.execute('SELECT id, serial_number FROM scooters')
        rows = cursor.fetchall()

        # Loop through all rows and decrypt to find the right one
        for row in rows:
            id = row[0]
            serial_number_dec = decrypt_message(row[1], key)
            
            if serial_number_dec == serial_number:
                # If we find a match, delete based on ID (primary key)
                cursor.execute('DELETE FROM scooters WHERE id = ?', (id,))
                conn.commit()
                print(f"Scooter met id {id} en serienummer {serial_number} is verwijderd.")
                return True
                
        print(f"Geen scooter gevonden met serienummer {serial_number} om te verwijderen.")
        return False
    except sqlite3.Error as e:
        print(f"An error occurred while deleting scooter: {e}")
        return False
    finally:
        close_connection(conn)

def update_scooter(scooter_id, fields: dict):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()

    try:
        encrypted_fields = {}

        for field_name, field_value in fields.items():
            if isinstance(field_value, str):
                encrypted_fields[field_name] = encrypt_message(field_value, key)
            else:
                # For non-string values like boolean or int, convert to string
                encrypted_fields[field_name] = encrypt_message(str(field_value), key)

        set_clause = ', '.join(f"{key} = ?" for key in encrypted_fields.keys())
        values = list(encrypted_fields.values())
        values.append(scooter_id)

        cursor.execute(f'''
            UPDATE scooters
            SET {set_clause}
            WHERE id = ?
        ''', values)
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"An error occurred while updating scooter: {e}")
        return False
    finally:
        close_connection(conn)

def get_scooter_by_serial_number(serial_number):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()
    try:
        # Step 1: only retrieve id + serial_number
        cursor.execute('SELECT id, serial_number FROM scooters')
        rows = cursor.fetchall()

        matched_id = None
        for row in rows:
            id = row[0]
            decrypted_serial = decrypt_message(row[1], key)
            if decrypted_serial == serial_number:
                matched_id = id
                break

        if not matched_id:
            return None  # No match found

        # Step 2: only retrieve this scooter
        cursor.execute('SELECT * FROM scooters WHERE id = ?', (matched_id,))
        row = cursor.fetchone()
        if not row:
            return None

        # Decrypt all fields only here
        brand = decrypt_message(row[1], key)
        model = decrypt_message(row[2], key)
        serial_number_dec = decrypt_message(row[3], key)
        top_speed = decrypt_message(row[4], key)
        battery_capacity = decrypt_message(row[5], key)
        soc = decrypt_message(row[6], key)
        soc_range_min = decrypt_message(row[7], key)
        soc_range_max = decrypt_message(row[8], key)
        location_latitude = decrypt_message(row[9], key)
        location_longitude = decrypt_message(row[10], key)
        out_of_service = decrypt_message(row[11], key) == 'True'
        mileage = decrypt_message(row[12], key)
        last_maintenance_date = decrypt_message(row[13], key) if row[13] else None

        return Scooter(
            matched_id, brand, model, serial_number_dec, top_speed, battery_capacity, soc,
            soc_range_min, soc_range_max, location_latitude, location_longitude,
            out_of_service, mileage, last_maintenance_date
        )

    except sqlite3.Error as e:
        log_instance.addlog("Scooter", "Get by serial number failed", f"Serial: {serial_number}", suspicious=True)
        print(f"An error occurred while fetching scooter by serial number: {e}")
        return None
    finally:
        close_connection(conn)
  

def search_scooters_partial(query):
    conn = open_connection()
    cursor = conn.cursor()
    key = load_symmetric_key()

    try:
        query = query.lower()
        results = []

        # Only retrieve fields that are needed for matching
        cursor.execute("SELECT id, brand, model, serial_number FROM scooters")
        basic_rows = cursor.fetchall()

        # First only decrypt and check the important fields
        for row in basic_rows:
            id = row[0]
            brand = decrypt_message(row[1], key)
            model = decrypt_message(row[2], key)
            serial = decrypt_message(row[3], key)

            if query in brand.lower() or query in model.lower() or query in serial.lower():
                # On a match, retrieve all fields for this scooter
                cursor.execute("SELECT * FROM scooters WHERE id = ?", (id,))
                full_row = cursor.fetchone()

                if full_row:
                    scooter = Scooter(
                        id=full_row[0],
                        brand=brand,
                        model=model,
                        serial_number=serial,
                        top_speed=decrypt_message(full_row[4], key),
                        battery_capacity=decrypt_message(full_row[5], key),
                        soc=decrypt_message(full_row[6], key),
                        soc_range_min=decrypt_message(full_row[7], key),
                        soc_range_max=decrypt_message(full_row[8], key),
                        location_latitude=decrypt_message(full_row[9], key),
                        location_longitude=decrypt_message(full_row[10], key),
                        out_of_service=(decrypt_message(full_row[11], key) == "True"),
                        mileage=decrypt_message(full_row[12], key),
                        last_maintenance_date=decrypt_message(full_row[13], key) if full_row[13] else None
                    )
                    results.append(scooter)

        return results

    except Exception as e:
        print("Error during scooter search:", e)
        return []
    finally:
        close_connection(conn)