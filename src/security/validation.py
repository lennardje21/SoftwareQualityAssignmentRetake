import re
from logs.log import log_instance
from datetime import datetime

class Validation:

    @staticmethod
    def contains_null_byte(value: str) -> bool:
        """Check if input contains null bytes (security check)."""
        return '\x00' in value or '\0' in value

    @staticmethod
    def get_valid_input(prompt, validation_fn, username, field_name):
        while True:
            value = input(prompt).strip()
            
            # Check for null bytes first (security critical)
            if Validation.contains_null_byte(value):
                print(f"Invalid input: contains forbidden characters.")
                log_instance.log_invalid_input(username, field_name, "Null byte detected", suspicious=True)
                continue
            
            if value == "cancel":
                print("Operation cancelled by user.")
                return None
            if validation_fn(value, username):
                return value
            log_instance.log_invalid_input(username, field_name, f"Invalid {field_name} input")

    @staticmethod
    def get_valid_range_input(prompt_min, prompt_max, validation_fn, username, field_name):
        while True:
            min_val = input(prompt_min).strip()
            
            # Check for null bytes
            if Validation.contains_null_byte(min_val):
                print(f"Invalid input: contains forbidden characters.")
                log_instance.log_invalid_input(username, field_name, "Null byte detected in min value", suspicious=True)
                continue
            
            if min_val.lower() == "cancel":
                return None, None

            max_val = input(prompt_max).strip()
            
            # Check for null bytes
            if Validation.contains_null_byte(max_val):
                print(f"Invalid input: contains forbidden characters.")
                log_instance.log_invalid_input(username, field_name, "Null byte detected in max value", suspicious=True)
                continue
            
            if max_val.lower() == "cancel":
                return None, None

            if validation_fn(min_val, max_val, username):
                return min_val, max_val

            print(f"Invalid range: {min_val}-{max_val}. Please try again or type 'cancel'.")


    @staticmethod
    def is_valid_search_input(query: str, username) -> bool:
        # Null byte check
        if Validation.contains_null_byte(query):
            print("Invalid search query: contains forbidden characters.")
            log_instance.log_invalid_input(username, "search", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[A-Za-z0-9]{3,20}", query):
            return True
        print(f"Invalid search query: {query}. Must be 3-20 alphanumeric characters.")
        log_instance.log_invalid_input(username, "search", "Search query must be 3-20 alphanumeric characters")
        return False
    
    @staticmethod
    def get_valid_coordinates(prompt_lat, prompt_lon, validation_fn, username):
        while True:
            lat = input(prompt_lat).strip()
            
            # Check for null bytes
            if Validation.contains_null_byte(lat):
                print(f"Invalid input: contains forbidden characters.")
                log_instance.log_invalid_input(username, "latitude", "Null byte detected", suspicious=True)
                continue
            
            if lat.lower() == "cancel":
                return None, None

            lon = input(prompt_lon).strip()
            
            # Check for null bytes
            if Validation.contains_null_byte(lon):
                print(f"Invalid input: contains forbidden characters.")
                log_instance.log_invalid_input(username, "longitude", "Null byte detected", suspicious=True)
                continue
            
            if lon.lower() == "cancel":
                return None, None

            if validation_fn(lat, lon, username):
                return lat, lon

            print(f"Invalid coordinates: {lat}, {lon}. Please try again or type 'cancel'.")


    @staticmethod
    def get_valid_id_input(id: str, username: str):
        # Null byte check
        if Validation.contains_null_byte(id):
            print("Invalid ID: contains forbidden characters.")
            log_instance.log_invalid_input(username, "id", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[1-9]\d{0,7}", id):  # 1 t/m 99999999 (max 8 numbers, no leading zero)
            return True

        print(f"Invalid ID: {id}. Must be a positive number <= 99999999 without leading zeros.")
        log_instance.log_invalid_input(username, "id", f"Invalid ID input: {id}")
        return False

    @staticmethod
    def name_validation(name, username):
        # Null byte check
        if Validation.contains_null_byte(name):
            print("Invalid name: contains forbidden characters.")
            log_instance.log_invalid_input(username, "name", "Null byte detected", suspicious=True)
            return False
        # Must start and end with a letter, can contain letters, spaces, hyphens, apostrophes in between
        # No consecutive special characters, 2-30 characters total
        if len(name) < 2 or len(name) > 30:
            print(f"Invalid name: {name}. Name must be 2-30 characters.")
            log_instance.log_invalid_input(username, "name", "Invalid length")
            return False
        
        if not re.fullmatch(r"^[A-Za-z]((?![\s\-']{2})[A-Za-z\s\-'])*[A-Za-z]$|^[A-Za-z]{2}$", name):
            print(f"Invalid name: {name}. Name must be 2-30 characters, start and end with a letter, contain only letters, spaces, hyphens, and apostrophes, and not have consecutive special characters (spaces, hyphens, apostrophes).")
            log_instance.log_invalid_input(username, "name", "Invalid format")
            return False
        
        return True

    @staticmethod
    def username_validation(username):
        # Null byte check
        if Validation.contains_null_byte(username):
            print("Invalid username: contains forbidden characters.")
            log_instance.log_invalid_input(username, "username", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"^[a-zA-Z_][a-zA-Z0-9_'.]{7,9}$", username):
            return True
        print(f"Invalid username: {username}. Must be 8-10 characters, start with a letter or underscore, and may contain letters, numbers, underscores, apostrophes, and periods.")
        log_instance.log_invalid_input(username, "username", "Invalid format")
        return False

    @staticmethod
    def password_validation(password, username):
        # Null byte check
        if Validation.contains_null_byte(password):
            print("Invalid password: contains forbidden characters.")
            log_instance.log_invalid_input(username, "password", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/])[A-Za-z\d~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/]{12,30}$", password):
            return True
        print("Invalid password. Password does not meet complexity requirements.")
        log_instance.log_invalid_input(username, "password", "Invalid format")
        return False

    @staticmethod
    def birthday_validation(date: str, username: str) -> bool:
        # Null byte check
        if Validation.contains_null_byte(date):
            print("Invalid birthday: contains forbidden characters.")
            log_instance.log_invalid_input(username, "date_of_birth", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            try:
                date_of_birth = datetime.strptime(date, "%Y-%m-%d")
                now = datetime.now()
                min_age = now.replace(year=now.year - 16)
                max_age = now.replace(year=now.year - 120)
                if max_age <= date_of_birth <= min_age:
                    return True
            except Exception:
                pass
        print(f"Invalid birthday: {date}. Format: YYYY-MM-DD, age: 16-120")
        log_instance.log_invalid_input(username, "date_of_birth", "Invalid format or out of range")
        return False

    @staticmethod
    def gender_validation(gender, username):
        # Null byte check
        if Validation.contains_null_byte(gender):
            print("Invalid gender: contains forbidden characters.")
            log_instance.log_invalid_input(username, "gender", "Null byte detected", suspicious=True)
            return False
        if gender.lower() in {'male', 'female'}:
            return True
        print(f"Invalid gender: {gender}. Must be 'male' or 'female'.")
        log_instance.log_invalid_input(username, "gender", "Invalid value")
        return False

    @staticmethod
    def street_validation(street, username):
        # Null byte check
        if Validation.contains_null_byte(street):
            print("Invalid street: contains forbidden characters.")
            log_instance.log_invalid_input(username, "street", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9\s\-\.']{1,49}", street):
            return True
        print(f"Invalid street: {street}. Must be non-empty and valid format.")
        log_instance.log_invalid_input(username, "street", "Invalid format")
        return False

    @staticmethod
    def housenumber_validation(housenumber, username):
        # Null byte check
        if Validation.contains_null_byte(housenumber):
            print("Invalid house number: contains forbidden characters.")
            log_instance.log_invalid_input(username, "house", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"^[1-9]\d*(?:[ -]?(?:[a-zA-Z]+|[1-9]\d*))?$", housenumber):
            return True
        print(f"Invalid house number: {housenumber}. Must be a valid numeric format.")
        log_instance.log_invalid_input(username, "house", "Invalid format")
        return False

    @staticmethod
    def zipcode_validation(zipcode, username):
        # Null byte check
        if Validation.contains_null_byte(zipcode):
            print("Invalid zipcode: contains forbidden characters.")
            log_instance.log_invalid_input(username, "zipcode", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"^\d{4}[A-Z]{2}$", zipcode):
            return True
        print(f"Invalid zipcode: {zipcode}. Format is incorrect.")
        log_instance.log_invalid_input(username, "zipcode", "Invalid format")
        return False

    @staticmethod
    def phone_validation(phone, username):
        # Null byte check
        if Validation.contains_null_byte(phone):
            print("Invalid phone number: contains forbidden characters.")
            log_instance.log_invalid_input(username, "phone", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"\d{8}", phone):
            return True
        print(f"Invalid phone number: {phone}. Must be 8 digits.")
        log_instance.log_invalid_input(username, "phone", "Invalid format")
        return False

    @staticmethod
    def email_validation(email, username):
        # Null byte check
        if Validation.contains_null_byte(email):
            print("Invalid email: contains forbidden characters.")
            log_instance.log_invalid_input(username, "email", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email):
            return True
        print(f"Invalid email: {email}. Format is invalid.")
        log_instance.log_invalid_input(username, "email", "Invalid format")
        return False

    @staticmethod
    def get_valid_cities():
        """Return the list of valid cities in a consistent order."""
        return ['Amsterdam', 'Rotterdam', 'Utrecht', 'Groningen', 'Maastricht', 
                'Den Haag', 'Eindhoven', 'Tilburg', 'Breda', 'Arnhem']

    @staticmethod
    def city_validation(city, username):
        # Null byte check
        if Validation.contains_null_byte(city):
            print("Invalid city: contains forbidden characters.")
            log_instance.log_invalid_input(username, "city", "Null byte detected", suspicious=True)
            return False
        valid_cities = {'Amsterdam', 'Rotterdam', 'Utrecht', 'Groningen', 'Maastricht', 'Den Haag', 'Eindhoven', 'Tilburg', 'Breda', 'Arnhem'}
        if city in valid_cities:
            return True
        print(f"Invalid city: {city}. Choose from: {', '.join(valid_cities)}")
        log_instance.log_invalid_input(username, "city", "Not in predefined list")
        return False
    
    @staticmethod
    def get_city_by_selection(username):
        """
        Display city options and get user selection.
        Returns the selected city name or None if cancelled.
        """
        valid_cities = Validation.get_valid_cities()
        
        print("\nSelect a city (or type 'cancel' to stop):")
        for idx, c in enumerate(valid_cities, start=1):
            print(f"{idx}. {c}")
        
        while True:
            city_choice = input("Enter number: ").strip()
            
            # Check for null bytes
            if Validation.contains_null_byte(city_choice):
                print(f"Invalid input: contains forbidden characters.")
                log_instance.log_invalid_input(username, "city selection", "Null byte detected", suspicious=True)
                continue
            
            if city_choice.lower() == "cancel":
                return None
            
            if city_choice.isdigit() and 1 <= int(city_choice) <= len(valid_cities):
                selected_city = valid_cities[int(city_choice) - 1]
                # Validate the selected city (should always pass, but for consistency)
                if Validation.city_validation(selected_city, username):
                    return selected_city
            
            print("Invalid selection. Please enter a valid number or 'cancel'.")
            log_instance.log_invalid_input(username, "city selection", f"Invalid choice: {city_choice}")

    @staticmethod
    def license_validation(license_number, username):
        # Null byte check
        if Validation.contains_null_byte(license_number):
            print("Invalid license number: contains forbidden characters.")
            log_instance.log_invalid_input(username, "license", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[A-Z]{1,2}\d{7}", license_number):
            return True
        print(f"Invalid license number: {license_number}. Format: X1234567 or XX1234567.")
        log_instance.log_invalid_input(username, "license", "Invalid format")
        return False

    @staticmethod
    def brand_validation(brand, username):
        # Null byte check
        if Validation.contains_null_byte(brand):
            print("Invalid brand: contains forbidden characters.")
            log_instance.log_invalid_input(username, "brand", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9\- ]{1,29}", brand):
            return True
        print(f"Invalid brand: {brand}. Must be non-empty and valid format.")
        log_instance.log_invalid_input(username, "brand", "Invalid format")
        return False

    @staticmethod
    def model_validation(model, username):
        # Null byte check
        if Validation.contains_null_byte(model):
            print("Invalid model: contains forbidden characters.")
            log_instance.log_invalid_input(username, "model", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9\-\s]{1,29}", model):
            return True
        print(f"Invalid model: {model}. Must be non-empty and valid format.")
        log_instance.log_invalid_input(username, "model", "Invalid format")
        return False

    @staticmethod
    def serial_number_validation(serial_number, username):
        # Null byte check
        if Validation.contains_null_byte(serial_number):
            print("Invalid serial number: contains forbidden characters.")
            log_instance.log_invalid_input(username, "serial number", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[A-Za-z0-9]{10,17}$", serial_number):
            return True
        print(f"Invalid serial number: {serial_number}. Must be 10-17 alphanumeric characters.")
        log_instance.log_invalid_input(username, "serial number", "Invalid format")
        return False

    @staticmethod
    def top_speed_validation(top_speed, username):
        # Null byte check
        if Validation.contains_null_byte(top_speed):
            print("Invalid top speed: contains forbidden characters.")
            log_instance.log_invalid_input(username, "top speed", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[1-9][0-9]{0,2}", top_speed):
            value = int(top_speed)
            if 1 <= value <= 300:
                return True
        print(f"Invalid top speed: {top_speed}. Must be 1-300 km/h.")
        log_instance.log_invalid_input(username, "top speed", "Invalid format or range")
        return False

    @staticmethod
    def battery_capacity_validation(battery_capacity, username):
        # Null byte check
        if Validation.contains_null_byte(battery_capacity):
            print("Invalid battery capacity: contains forbidden characters.")
            log_instance.log_invalid_input(username, "battery capacity", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[1-9][0-9]{1,3}", battery_capacity):
            value = int(battery_capacity)
            if 50 <= value <= 2000:
                return True
        print(f"Invalid battery capacity: {battery_capacity}. Must be 50-2000.")
        log_instance.log_invalid_input(username, "battery capacity", "Invalid format or range")
        return False

    @staticmethod
    def soc_single_value(value, username):
        # Null byte check
        if Validation.contains_null_byte(value):
            print("Invalid SOC value: contains forbidden characters.")
            log_instance.log_invalid_input(username, "SOC", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[0-9]{1,3}", value):
            val = int(value)
            if 0 <= val <= 100:
                return True
        print(f"Invalid SOC value: {value}. Must be 0-100%.")
        log_instance.log_invalid_input(username, "SOC", "Invalid value")
        return False

    @staticmethod
    def soc_range_validation(min, max, username):
        # Null byte check
        if Validation.contains_null_byte(min) or Validation.contains_null_byte(max):
            print("Invalid SOC range: contains forbidden characters.")
            log_instance.log_invalid_input(username, "SOC range", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[0-9]{1,3}", min) and re.fullmatch(r"[0-9]{1,3}", max):
            min_val = int(min)
            max_val = int(max)
            if 0 <= min_val <= 100 and 0 <= max_val <= 100 and min_val < max_val:
                return True
        print(f"Invalid SOC range: {min}-{max}. Must be two numbers between 0 and 100 with min < max.")
        log_instance.log_invalid_input(username, "SOC range", "Invalid range")
        return False

    @staticmethod
    def location_validation(latitude, longitude, username):
        # Null byte check
        if Validation.contains_null_byte(latitude) or Validation.contains_null_byte(longitude):
            print("Invalid coordinates: contains forbidden characters.")
            log_instance.log_invalid_input(username, "location", "Null byte detected", suspicious=True)
            return False
        # Enforce exactly 5 decimal places as per Rotterdam coordinate spec
        if re.fullmatch(r"\d{2}\.\d{5}", latitude) and re.fullmatch(r"\d\.\d{5}", longitude):
            try:
                lat_val = float(latitude)
                lng_val = float(longitude)
                # Rotterdam bounds
                if 51.85000 <= lat_val <= 52.05000 and 4.40000 <= lng_val <= 4.55000:
                    return True
            except ValueError:
                pass

        print(f"Invalid coordinates: lat={latitude}, lng={longitude}. "
            f"Must be within lat 51.85000-52.05000 and lng 4.40000-4.55000, with exactly 5 decimal places.")
        log_instance.log_invalid_input(username, "location", "Invalid coordinates")
        return False


    @staticmethod
    def mileage_validation(mileage, username):
        # Null byte check
        if Validation.contains_null_byte(mileage):
            print("Invalid mileage: contains forbidden characters.")
            log_instance.log_invalid_input(username, "mileage", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[1-9]\d*|0", mileage):
            return True
        print(f"Invalid mileage: {mileage}. Must be a non-negative integer without leading zeros.")
        log_instance.log_invalid_input(username, "mileage", "Invalid format")
        return False

    @staticmethod
    def last_maintenance_date_validation(last_maintenance_date, username):
        # Null byte check
        if Validation.contains_null_byte(last_maintenance_date):
            print("Invalid maintenance date: contains forbidden characters.")
            log_instance.log_invalid_input(username, "last maintenance date", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"^\d{4}-\d{2}-\d{2}$", last_maintenance_date):
            return True
        print(f"Invalid maintenance date: {last_maintenance_date}. Use format YYYY-MM-DD.")
        log_instance.log_invalid_input(username, "last maintenance date", "Invalid format")
        return False

    @staticmethod
    def yes_no_validation(choice, username):
        # Null byte check
        if Validation.contains_null_byte(choice):
            print("Invalid yes/no choice: contains forbidden characters.")
            log_instance.log_invalid_input(username, "yes/no choice", "Null byte detected", suspicious=True)
            return False
        if choice.lower() in {'yes', 'no'}:
            return True
        print(f"Invalid yes/no choice: {choice}. Must be 'yes' or 'no'.")
        log_instance.log_invalid_input(username, "yes/no choice", "Invalid value")
        return False

    @staticmethod
    def restore_code_validation(code: str, username: str) -> bool:
        """Validate a one-use restore code: 8 alphanumeric characters."""
        # Null byte check
        if Validation.contains_null_byte(code):
            print("Invalid restore code: contains forbidden characters.")
            log_instance.log_invalid_input(username, "restore code", "Null byte detected", suspicious=True)
            return False
        if re.fullmatch(r"[A-Za-z0-9]{8}", code):
            return True
        print(f"Invalid restore code: {code}. Code must be exactly 8 letters/digits.")
        log_instance.log_invalid_input(username, "restore code", "Invalid format")
        return False