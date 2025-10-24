from security.validation import Validation
from models.traveller import create_traveller, get_traveller_by_email, get_traveller_by_license, get_traveller_by_phone, list_travellers, find_travellers, update_traveller, delete_traveller
from logs.log import log_instance
from controllers.rolecheck import require_authorization
from helpers.general_methods import general_methods
import sys
import time

# Unique validation functions for traveller fields
def unique_email_validation(email, username, exclude_id=None):
    """Validate email format and check for uniqueness."""
    if not Validation.email_validation(email, username):
        return False
    existing = get_traveller_by_email(email)
    if existing and (exclude_id is None or existing.id != exclude_id):
        print("A traveller with this email already exists.")
        log_instance.log_invalid_input(username, "email", "Duplicate traveller email")
        return False
    return True

def unique_phone_validation(phone, username, exclude_id=None):
    """Validate phone format and check for uniqueness."""
    if not Validation.phone_validation(phone, username):
        return False
    existing = get_traveller_by_phone(phone)
    if existing and (exclude_id is None or existing.id != exclude_id):
        print("A traveller with this phone number already exists.")
        log_instance.log_invalid_input(username, "phone_number", "Duplicate traveller phone")
        return False
    return True

def unique_license_validation(license_number, username, exclude_id=None):
    """Validate license format and check for uniqueness."""
    if not Validation.license_validation(license_number, username):
        return False
    existing = get_traveller_by_license(license_number)
    if existing and (exclude_id is None or existing.id != exclude_id):
        print("A traveller with this license number already exists.")
        log_instance.log_invalid_input(username, "license_number", "Duplicate traveller license")
        return False
    return True

def traveller_menu(current_user):
    while True:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + f"Traveller Management".center(75) + "|")
        print("----------------------------------------------------------------------------")

        print("[1] Register new traveller")
        print("[2] List all travellers")
        print("[3] Search for a traveller")
        print("[4] Delete a traveller")
        print("[5] Update traveller information")
        print("[0] Return to previous menu")


        choice = input("Choose an option: ").strip()

        if choice == '1':
            add_traveller(current_user)
        elif choice == '2':
            show_travellers(current_user)
        elif choice == '3':
            search_traveller(current_user)
        elif choice == '4':
            delete_traveller_controller(current_user)
        elif choice == '5':
            update_traveller_controller(current_user)

        elif choice == '0':
            print("Returning to previous menu...")
            return
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1)

def show_travellers(current_user):
    require_authorization(current_user, 'show_traveller')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Traveller list".center(75) + "|")
    print("----------------------------------------------------------------------------")

    travellers = list_travellers(current_user)
    if travellers:
        for t in travellers:
            print(f"ID: {t.id}")
            print(f"First Name: {t.first_name}")
            print(f"Last Name: {t.last_name}")
            print(f"Date of Birth: {t.date_of_birth}")
            print(f"Gender: {t.gender}")
            print(f"Street: {t.streetname}")
            print(f"House Number: {t.house_number}")
            print(f"Zip Code: {t.zip_code}")
            print(f"City: {t.city}")
            print(f"Email: {t.email}")
            print(f"Phone Number: +31-6-{t.phone_number}")
            print(f"License Number: {t.license_number}")
            print(f"Registration Date: {t.registration_date}")
            print("----------------------------------------------------------------------------")
    else:
        print("No travellers found.")

    general_methods.hidden_input("\nPress Enter to return to the traveller menu...")

def add_traveller(current_user):
    require_authorization(current_user, 'add_traveller')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Add Traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")

    username = current_user.username  # for logging in validation

    # FIRST NAME
    first_name = Validation.get_valid_input("First Name (or 'cancel' to stop): ",
                                            Validation.name_validation, username, "first name")
    if first_name is None:
        return
    
    # LAST NAME
    last_name = Validation.get_valid_input("Last Name (or 'cancel' to stop): ",
                                           Validation.name_validation, username, "last name")
    if last_name is None:
        return

    # DATE OF BIRTH
    date_of_birth = Validation.get_valid_input("Date of Birth (YYYY-MM-DD, or 'cancel' to stop): ",
                                               Validation.birthday_validation, username, "date of birth")
    if date_of_birth is None:
        return

    # GENDER
    gender = Validation.get_valid_input("Gender (male/female, or 'cancel' to stop): ",
                                        Validation.gender_validation, username, "gender")
    if gender is None:
        return

    # STREET
    street = Validation.get_valid_input("Street (or 'cancel' to stop): ",
                                        Validation.street_validation, username, "street")
    if street is None:
        return

    # HOUSE NUMBER
    house_number = Validation.get_valid_input("House Number (or 'cancel' to stop): ",
                                              Validation.housenumber_validation, username, "house number")
    if house_number is None:
        return

    # ZIP CODE
    zip_code = Validation.get_valid_input("Zip Code (e.g., 1234AB, or 'cancel' to stop): ",
                                          Validation.zipcode_validation, username, "zip code")
    if zip_code is None:
        return

    # CITY
    city = Validation.get_city_by_selection(username)
    if city is None:
        print("Traveller creation cancelled.")
        return

    # EMAIL with UNIQUE CHECK
    email = Validation.get_valid_input(
        "Email (or 'cancel' to stop): ",
        lambda email, un: unique_email_validation(email, username),
        username, 
        "email"
    )
    if email is None:
        return

    # PHONE NUMBER
    phone_number = Validation.get_valid_input(
        "Phone Number (+31-6-xxxxxxxx, or 'cancel' to stop): ",
        lambda phone, un: unique_phone_validation(phone, username),
        username, 
        "phone number"
    )
    if phone_number is None:
        return

    # LICENSE NUMBER
    license_number = Validation.get_valid_input(
        "License Number (XX1234567 or X1234567, or 'cancel' to stop): ",
        lambda license, un: unique_license_validation(license, username),
        username, 
        "license number"
    )
    if license_number is None:
        return

    # DATABASE SAVE
    success = create_traveller(first_name.title(), last_name.title(), date_of_birth, gender.lower(),
                               street.title(), house_number, zip_code.upper(), city,
                               email.lower(), phone_number, license_number.upper())

    if success:
        print(f"\nTraveller '{first_name} {last_name}' created successfully.")
        log_instance.addlog(username, "Traveller created", f"{first_name} {last_name}", False)
    else:
        print("\nFailed to create traveller.")
        log_instance.addlog(username, "Traveller creation failed", f"{first_name} {last_name}", True)

    general_methods.hidden_input("\nPress Enter to return...")

def search_traveller(current_user):
    require_authorization(current_user, 'search_traveller')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Search Traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")

    query = Validation.get_valid_input(
        prompt = "Enter information you would like to search for (name, email, etc.): ",
        validation_fn = Validation.is_valid_search_input,
        username = current_user.username,
        field_name = "search traveller"
    )
    result = find_travellers(query)
    number_of_results = len(result) if result else 0
    general_methods.clear_console()
    if result:
        print(f"\n--- {number_of_results} Traveller(s) Found ---")
        for t in result:
            print(f"ID: {t['id']}")
            print(f"First Name: {t['first_name']}")
            print(f"Last Name: {t['last_name']}")
            print(f"Date of Birth: {t['date_of_birth']}")
            print(f"Gender: {t['gender']}")
            print(f"Street: {t['street']}")
            print(f"House Number: {t['house_number']}")
            print(f"Zip Code: {t['zip_code']}")
            print(f"City: {t['city']}")
            print(f"Email: {t['email']}")
            print(f"Phone Number: +31-6-{t['phone_number']}")
            print(f"License Number: {t['license_number']}")
            print(f"Registration Date: {t['registration_date']}")
            print("----------------------------------------------------------------------------")
        log_instance.addlog(current_user.username, "Traveller search", query, False)
    else:
        print("No matching travellers found.")
        log_instance.addlog(current_user.username, "Traveller search - no results", query, False)
    general_methods.hidden_input("\nPress Enter to return to the traveller menu...")

def update_traveller_controller(current_user):
    require_authorization(current_user, 'update_traveller')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + f"Available Travellers".center(75) + "|")
    print("----------------------------------------------------------------------------")
    travellers = list_travellers(current_user)
    if not travellers:
        print("No travellers found.")
        general_methods.hidden_input("Press Enter to return...")
        return

    for t in travellers:
        print(f"ID: {t.id} | {t.first_name} {t.last_name} | {t.email}")

    # --- SELECT TRAVELLER ---
    while True:
        target_id_str = Validation.get_valid_input(
            prompt="\nEnter traveller ID to update (or 'cancel' to stop): ",
            validation_fn=Validation.get_valid_id_input,
            username=current_user.username,
            field_name="traveller_id"
        )
        if target_id_str is None:
            print("Update cancelled.")
            return

        target_id = int(target_id_str)
        target = next((x for x in travellers if x.id == target_id), None)
        if not target:
            print("Invalid selection. Please try again.")
            continue
        break

    # --- FIELD SELECTION MENU ---
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Update Traveller: {target.first_name} {target.last_name}".center(75) + "|")
    print("----------------------------------------------------------------------------")
    print("\nWhich field do you want to update?")
    print(f"[1] First name: {target.first_name}")
    print(f"[2] Last name: {target.last_name}")
    print(f"[3] Date of birth: {target.date_of_birth}")
    print(f"[4] Gender: {target.gender}")
    print(f"[5] Street: {target.streetname}")
    print(f"[6] House Number: {target.house_number}")
    print(f"[7] Zip Code: {target.zip_code}")
    print(f"[8] City: {target.city}")
    print(f"[9] Email: {target.email}")
    print(f"[10] Phone Number: +31-6-{target.phone_number}")
    print(f"[11] License Number: {target.license_number}")
    print("[0] Cancel")

    choice = input("Choose a number: ").strip()

    field_map = {
        '1': ('first_name', "First name", Validation.name_validation),
        '2': ('last_name', "Last name", Validation.name_validation),
        '3': ('date_of_birth', "Date of Birth (YYYY-MM-DD)", Validation.birthday_validation),
        '4': ('gender', "Gender (male/female)", Validation.gender_validation),
        '5': ('street', "Street", Validation.street_validation),
        '6': ('house_number', "House Number", Validation.housenumber_validation),
        '7': ('zip_code', "Zip Code (e.g. 1234AB)", Validation.zipcode_validation),
        '8': ('city', None, None),  # <-- city handled separately
        '9': ('email', "Email", Validation.email_validation),
        '10': ('phone_number', "Phone Number (+31-6-xxxxxxxx)", Validation.phone_validation),
        '11': ('license_number', "License Number", Validation.license_validation),
        '0': (None, None, None)
    }

    if choice not in field_map:
        print("Invalid choice.")
        return

    field_key, label, validator = field_map[choice]
    username = current_user.username

    if field_key is None:  # cancel
        print("Update cancelled.")
        return

    update_data = {}

    # --- SPECIAL CASE: CITY (NUMBER SELECTION) ---
    if choice == '8':
        selected_city = Validation.get_city_by_selection(username)
        if selected_city is None:
            print("Update cancelled.")
            return
        update_data["city"] = selected_city

    # --- SPECIAL CASE: EMAIL (UNIQUE + UE-1 rule) ---
    elif choice == '9':
        new_email = Validation.get_valid_input(
            prompt="Enter new email (or 'cancel' to stop): ",
            validation_fn=lambda email, un: unique_email_validation(email, username, target.id),
            username=username,
            field_name="email"
        )
        if new_email is None:
            print("Update cancelled.")
            return
        update_data["email"] = new_email.lower()

    elif choice == '10':
        new_phone = Validation.get_valid_input(
            prompt="Enter new phone number (or 'cancel' to stop): ",
            validation_fn=lambda phone, un: unique_phone_validation(phone, username, target.id),
            username=username,
            field_name="phone_number"
        )
        if new_phone is None:
            print("Update cancelled.")
            return
        update_data["phone_number"] = new_phone
        
    elif choice == '11':
        new_license = Validation.get_valid_input(
            prompt="Enter new license number (or 'cancel' to stop): ",
            validation_fn=lambda license, un: unique_license_validation(license, username, target.id),
            username=username,
            field_name="license_number"
        )
        if new_license is None:
            print("Update cancelled.")
            return
        update_data["license_number"] = new_license.upper()

    # --- NORMAL CASE (ALL OTHER FIELDS) ---
    else:
        new_value = Validation.get_valid_input(
            prompt=f"Enter new value for {label} (or 'cancel' to stop): ",
            validation_fn=validator,
            username=username,
            field_name=field_key
        )
        if new_value is None:
            print("Update cancelled.")
            return
        update_data[field_key] = new_value

    # --- APPLY UPDATE ---
    if update_traveller(target_id, update_data):
        print("\nTraveller updated successfully.")
        log_instance.addlog(username, "Traveller updated", str(update_data), False)
    else:
        print("\nUpdate failed.")
        log_instance.addlog(username, "Traveller update failed", str(update_data), True)

    general_methods.hidden_input("\nPress Enter to return...")

def delete_traveller_controller(current_user):
    require_authorization(current_user, 'delete_traveller')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + f"Delete Traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")

    travellers = list_travellers(current_user)
    if not travellers:
        print("No travellers found.")
        general_methods.hidden_input("\nPress Enter to return...")
        return

    for t in travellers:
        print(f"ID: {t.id} | {t.first_name} {t.last_name} | {t.email}")

    # --- SELECT TRAVELLER ---
    while True:
        target_id_str = Validation.get_valid_input(
            prompt="\nEnter traveller ID to delete (or 'cancel' to stop): ",
            validation_fn=Validation.get_valid_id_input,
            username=current_user.username,
            field_name="traveller_id"
        )
        if target_id_str is None:
            print("Deletion cancelled.")
            return

        target_id = int(target_id_str)
        target = next((x for x in travellers if x.id == target_id), None)
        if not target:
            print("Invalid selection. Please try again.")
            continue
        break

    # --- CONFIRM DELETION ---
    while True:
        confirm = input("Are you sure you want to delete this traveller? (yes/no): ").strip().lower()
        if Validation.contains_null_byte(confirm):
            print("Invalid input: null bytes are not allowed.")
            log_instance.log_invalid_input(current_user.username, "confirmation", "Null byte detected", suspicious=True)
            continue
        if confirm != "yes":
            print("Deletion cancelled.")
            return
        break

    # --- DELETE ---
    if delete_traveller(target_id):
        print("\nTraveller deleted successfully.")
        log_instance.addlog(current_user.username, "Traveller deleted", f"Traveller ID {target_id}", False)
    else:
        print("\nFailed to delete traveller.")
        log_instance.addlog(current_user.username, "Traveller delete failed", f"Traveller ID {target_id}", True)

    general_methods.hidden_input("\nPress Enter to return...")
