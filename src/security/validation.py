import re
from logs.log import log_instance
from datetime import datetime

class Validation:

    @staticmethod
    def get_valid_id_input(id: str, username: str):
        if re.fullmatch(r"[1-9]\d{0,7}", id):  # 1 t/m 99999999 (max 8 numbers, no leading zero)
            return True

        print("ID is not valid (must be a positive number ≤ 99999999 without leading zeros).")
        log_instance.log_invalid_input(username, "id", f"Invalid ID input: {id}")
        return False

    @staticmethod
    def get_valid_input(prompt, validation_fn, username, field_name):
        while True:
            value = input(prompt).strip()
            if value == "cancel":
                print("Operation cancelled by user.")
                return None
            if validation_fn(value, username):
                return value
            log_instance.log_invalid_input(username, field_name, f"Invalid {field_name} input")
            print(f"Invalid {field_name}. Please try again.")

    @staticmethod
    def get_valid_range_input(prompt_min, prompt_max, validation_fn, username, field_name):
        while True:
            min_value = input(prompt_min).strip()
            max_value = input(prompt_max).strip()
            if validation_fn(min_value, max_value, username):
                return min_value, max_value
            log_instance.log_invalid_input(username, field_name, f"Invalid {field_name} input: {min_value}-{max_value}")
            print(f"Invalid {field_name}. Please try again.")

    @staticmethod
    def is_valid_search_input(query: str, username) -> bool:
        if re.fullmatch(r"[A-Za-z0-9]{3,20}", query):
            return True
        print("Invalid search query (3-20 characters)")
        log_instance.log_invalid_input(username, "search", "Search query must be 3-20 alphanumeric characters")
        return False
    
    @staticmethod
    def get_valid_coordinates(prompt_lat, prompt_lon, validation_fn, username):
        while True:
            lat_input = input(prompt_lat).strip()
            lon_input = input(prompt_lon).strip()
            if validation_fn(lat_input, lon_input, username):
                return lat_input, lon_input
            log_instance.log_invalid_input(username, "location", f"Invalid coordinates: {lat_input}, {lon_input}")
            print("Invalid location. Please try again.")

    @staticmethod
    def get_valid_id_input(id: str, username: str):
        if re.fullmatch(r"[1-9]\d{0,7}", id):  # 1 t/m 99999999 (max 8 numbers, no leading zero)
            return True

        # print("ID is not valid (must be a positive number ≤ 99999999 without leading zeros).")
        log_instance.log_invalid_input(username, "id", f"Invalid ID input: {id}")
        return False


    @staticmethod
    def name_validation(name, username):
        if re.fullmatch(r"[A-Za-z]{2,30}", name):
            return True
        # print("Name is not valid")
        log_instance.log_invalid_input(username, "name","Name must only contain letters (1–30 characters)")
        return False
    
    @staticmethod
    def username_validation(username):
        if re.fullmatch(r"^[a-zA-Z_][a-zA-Z0-9_'.]{7,9}$", username):
            return True
        print("Username is not valid")
        log_instance.log_invalid_input(username, "username", "Username must be 8–10 characters, start with a letter or underscore, and may contain letters, numbers, underscores, apostrophes, and periods.")
        return False
    
    @staticmethod
    def password_validation(password, username):
        if re.fullmatch(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/])[A-Za-z\d~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/]{12,30}$", password):
            return True
        # print("Password is not valid")
        log_instance.log_invalid_input(username, "password", "Password does not meet complexity requirements")
        return False

    @staticmethod
    def birthday_validation(date: str, username: str) -> bool:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            try:
                date_of_birth = datetime.strptime(date, "%Y-%m-%d")
                now = datetime.now()

                # At least 0 days old, at most 120 years back
                min_age = now.replace(year=now.year - 16)
                max_age = now.replace(year=now.year - 120)
                if max_age <= date_of_birth <= min_age:
                    return True
            except Exception as e:
                log_instance.log_invalid_input(username, "date_of_birth", f"Invalid date object: {e}")

        print("Invalid birthday (format: YYYY-MM-DD, age: 16-120)")
        log_instance.log_invalid_input(username, "date_of_birth", "Invalid format or out of range")
        return False
        
    @staticmethod
    def gender_validation(gender, username):
        if gender.lower() in {'male', 'female'}:
            return True
        print("Gender must be 'male' or 'female'")
        log_instance.log_invalid_input(username, "gender", "Gender must be 'male' or 'female'")
        return False

    #NOTE: DEZE Functie doet nu niks -> controleer waar streetname aan moet voldoen
    # Geen rare tekens @#$, begin met hoofdletter, geen lege string, geef het een max size
    @staticmethod
    def street_validation(street, username):
        if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9\s\-\.']{1,49}", street):
            return True
        print("Street name is not valid")
        log_instance.log_invalid_input(username, "street", "Street name is empty or invalid")
        return False
    
    
    @staticmethod
    def housenumber_validation(housenumber, username):
        if re.fullmatch(r"^[1-9]\d*(?:[ -]?(?:[a-zA-Z]+|[1-9]\d*))?$", housenumber):
            return True
        print("House number is not valid")
        log_instance.log_invalid_input(username, "house", "House number must be a valid numeric format")
        return False
    
    @staticmethod
    def zipcode_validation(zipcode, username):
        if re.fullmatch(r"^\d{4}[A-Z]{2}$", zipcode):
            return True
        print("Zipcode is not valid")
        log_instance.log_invalid_input(username, "zipcode", "Zipcode format is incorrect")
        return False
    
    @staticmethod
    def phone_validation(phone, username):
        if re.fullmatch(r"\d{8}", phone):
            return True
        print("Phone number is not valid (enter only the 8 digits)")
        log_instance.log_invalid_input(username, "phone", "Phone number must be 8 digits")
        return False
    
    @staticmethod
    def email_validation(email, username):
        if re.fullmatch(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email):
            return True
        print("Email is not valid")
        log_instance.log_invalid_input(username, "email", "Email format is invalid")
        return False
    
    #NOTE: Maak er een SET van
    @staticmethod
    def city_validation(city, username):
        valid_cities = {'Amsterdam', 'Rotterdam', 'Utrecht', 'Groningen', 'Maastricht', 'Den Haag', 'Eindhoven', 'Tilburg', 'Breda', 'Arnhem'}
        if city in valid_cities:
            return True
        print("City is not valid. Choose from:", ', '.join(valid_cities))
        log_instance.log_invalid_input(username, "city", "City not in predefined list")
        return False
    
    @staticmethod
    def license_validation(license_number, username):
        if re.fullmatch(r"[A-Z]{1,2}\d{7}", license_number):
            return True
        print("Invalid license number (format: X1234567 or XX1234567)")
        log_instance.log_invalid_input(username, "license", "License number format is incorrect")
        return False

    @staticmethod
    def brand_validation(brand, username):
        if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9\- ]{1,29}", brand):
            return True
        print("Brand name is not valid")
        log_instance.log_invalid_input(username, "brand", "Brand name is empty or invalid")
        return False
    
    @staticmethod
    def model_validation(model, username):
        if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9\-\s]{1,29}", model):
            return True
        print("Model name is not valid")
        log_instance.log_invalid_input(username, "model", "Model name is empty or invalid")
        return False
    
    @staticmethod
    def serial_number_validation(serial_number, username):
        if re.fullmatch(r"[A-Za-z0-9]{10,17}$", serial_number):
            return True
        print("Invalid serial number (10-17 characters)")
        log_instance.log_invalid_input(username, "serial number", "Serial number must be 10-17 alphanumeric characters")
        return False
    
    #NOTE: kan korter
    @staticmethod
    def top_speed_validation(top_speed, username):
        if re.fullmatch(r"[1-9][0-9]{0,2}", top_speed):  # 1 t/m 999 zonder leading zero
            value = int(top_speed)
            if 1 <= value <= 300:
                return True
        print("Invalid top speed (1-300 km/h)")
        log_instance.log_invalid_input(username, "top speed", "Invalid format or range (1–300, no leading zeros)", False)
        return False
    
    @staticmethod
    def battery_capacity_validation(battery_capacity, username):
        if re.fullmatch(r"[1-9][0-9]{1,3}", battery_capacity):
            value = int(battery_capacity)
            if 50 <= value <= 2000:
                return True
        print("Invalid battery capacity (50-2000)")
        log_instance.log_invalid_input(username, "battery capacity", "Battery capacity must be a positive integer between 50 and 2000", False)
        return False
    

    @staticmethod
    def soc_single_value(value, username):
        if re.fullmatch(r"[0-9]{1,3}", value):
            val = int(value)
            if 0 <= val <= 100:
                return True
        print("Invalid SOC value (0-100%)")
        log_instance.log_invalid_input(username, "SOC", "Invalid SOC value", False)
        return False

    @staticmethod
    def soc_range_validation(min, max, username):
        if re.fullmatch(r"[0-9]{1,3}", min) and re.fullmatch(r"[0-9]{1,3}", max):
            min_val = int(min)
            max_val = int(max)
            if 0 <= min_val <= 100 and 0 <= max_val <= 100 and min_val < max_val:
                return True
        print("Invalid SOC range (min-max, 0-100%)")
        log_instance.log_invalid_input(username, "SOC range", "SOC range must be two numbers between 0 and 100 with min < max", False)
        return False
        

    @staticmethod
    def location_validation(latitude, longitude, username):
        if re.fullmatch(r"\d{2}\.\d{5}", latitude) and re.fullmatch(r"\d\.\d{5}", longitude):
            try:
                lat_val = float(latitude)
                lng_val = float(longitude)

                if 51.85000 <= lat_val <= 52.05000 and 4.40000 <= lng_val <= 4.55000:
                    return True
            except ValueError:
                pass

        print("Invalid coordinates (lat: 51.85000-52.05000, lng: 4.40000-4.55000, exactly 5 decimal places)")
        log_instance.log_invalid_input(username, "location", "Invalid GPS coordinates for Rotterdam with required precision")
        return False
        
    @staticmethod
    def mileage_validation(mileage, username):
        if re.fullmatch(r"[1-9]\d*|0", mileage):  # 0 of positief geheel getal zonder leading zeros
            return True
        print("Mileage must be a non-negative integer without leading zeros.")
        log_instance.log_invalid_input(username, "mileage", "Invalid mileage format")
        return False
    
    @staticmethod
    def last_maintenance_date_validation(last_maintenance_date, username):
        if re.fullmatch(r"^\d{4}-\d{2}-\d{2}$", last_maintenance_date):
            return True
        print("Invalid maintenance date (format: YYYY-MM-DD)")
        log_instance.log_invalid_input(username, "last maintenance date", "Use format YYYY-MM-DD")
        return False
    
    @staticmethod
    def yes_no_validation(choice, username):
        if choice.lower() in {'yes', 'no'}:
            return True
        print("Choice must be 'yes' or 'no'")
        log_instance.log_invalid_input(username, "yes/no choice", "Invalid yes/no input")
        return False