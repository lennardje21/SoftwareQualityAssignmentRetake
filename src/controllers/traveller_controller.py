from security.validation import Validation
from models.traveller import create_traveller, list_travellers, find_travellers, update_traveller, delete_traveller
from logs.log import log_instance
from controllers.rolecheck import require_authorization
from helpers.general_methods import general_methods
import sys
import time

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

def get_valid_input(prompt, validation_fn, username, field_name):
    attempts = 0
    while attempts < 3:
        value = input(prompt).strip()
        if validation_fn(value, username):
            return value
        attempts += 1
        log_instance.log_invalid_input(username, field_name, f"Invalid {field_name} input")
        print(f"Invalid {field_name}. Please try again.")
    print("Too many failed attempts. Returning to menu...")
    time.sleep(2)
    return None

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
            print(f"Phone Number: {t.phone_number}")
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
    print("|" + f"Register New Traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")
    
    username = current_user.username
    
    first_name = get_valid_input("First Name: ", Validation.name_validation, username, "first name")
    if first_name is None:
        return
    
    last_name = get_valid_input("Last Name: ", Validation.name_validation, username, "last name")
    if last_name is None:
        return
    
    date_of_birth = get_valid_input("Date of Birth (YYYY-MM-DD): ", Validation.birthday_validation, username, "date of birth")
    if date_of_birth is None:
        return
    
    gender = get_valid_input("Gender (male/female): ", Validation.gender_validation, username, "gender")
    if gender is None:
        return
    
    street = get_valid_input("Street: ", Validation.street_validation, username, "street")
    if street is None:
        return
    
    house_number = get_valid_input("House Number: ", Validation.housenumber_validation, username, "house number")
    if house_number is None:
        return
    
    zip_code = get_valid_input("Zip Code (e.g., 1234AB): ", Validation.zipcode_validation, username, "zip code")
    if zip_code is None:
        return
    
    city = get_valid_input("City: ", Validation.city_validation, username, "city")
    if city is None:
        return
    
    email = get_valid_input("Email: ", Validation.email_validation, username, "email")
    if email is None:
        return
    
    phone_number = get_valid_input("Phone Number (+31-6-xxxxxxxx): ", Validation.phone_validation, username, "phone number")
    if phone_number is None:
        return
    
    license_number = get_valid_input("License Number (XX1234567 or X1234567): ", Validation.license_validation, username, "license number")
    if license_number is None:
        return

    result = create_traveller(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        street=street,
        house_number=house_number,
        zip_code=zip_code,
        city=city,
        email=email,
        phone_number=phone_number,
        license_number=license_number
    )
    
    if result:
        print("Traveller registered successfully.")
        log_instance.addlog(username, "Traveller registration", f"{first_name} {last_name}", False)
        time.sleep(1)
    else:
        print("Failed to register traveller.")
        log_instance.addlog(username, "Traveller registration failed", f"{first_name} {last_name}", True)
        time.sleep(1)

    general_methods.hidden_input("\nPress Enter to return to the traveller menu...")

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
            print(f"Phone Number: {t['phone_number']}")
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
            print(f"Phone Number: {t.phone_number}")
            print(f"License Number: {t.license_number}")
            print(f"Registration Date: {t.registration_date}")
            print("----------------------------------------------------------------------------")
    else:
        print("No travellers found.")
    try:
        customer_id = int(input("Enter traveller ID to update: ").strip())
    except ValueError:
        print("No ID entered. Returning to menu.")
        log_instance.log_invalid_input(current_user.username, "traveller_id", "Invalid ID format", True)
        time.sleep(1)
        return
    general_methods.clear_console()
    print("\nWhich field do you want to update?")
    print("[1] First Name")
    print("[2] Last Name")
    print("[3] Date of Birth")
    print("[4] Gender")
    print("[5] Street")
    print("[6] House Number")
    print("[7] Zip Code")
    print("[8] City")
    print("[9] Email")
    print("[10] Phone Number")
    print("[11] License Number")
    print("[0] Cancel")

    choice = input("Choose a number: ").strip()
    username = current_user.username

    field_map = {
        '1': ('first_name', "First Name", Validation.name_validation),
        '2': ('last_name', "Last Name", Validation.name_validation),
        '3': ('date_of_birth', "Date of Birth (YYYY-MM-DD)", Validation.birthday_validation),
        '4': ('gender', "Gender (male/female)", Validation.gender_validation),
        '5': ('streetname', "Street", Validation.street_validation),
        '6': ('house_number', "House Number", Validation.housenumber_validation),
        '7': ('zip_code', "Zip Code (e.g., 1234 AB)", Validation.zipcode_validation),
        '8': ('city', "City", Validation.city_validation),
        '9': ('email', "Email", Validation.email_validation),
        '10': ('phone_number', "Phone Number (+31-6-xxxxxxxx)", Validation.phone_validation),
        '11': ('license_number', "License Number (X1234567 or XX1234567)", Validation.license_validation),
        '0': (None, None, None)
    }

    if choice not in field_map:
        print("Invalid choice.")
        time.sleep(1)
        return

    field_key, label, validator = field_map[choice]
    if field_key is None:
        print("Cancelled.")
        time.sleep(1)
        return

    # Input via get_valid_input()
    new_value = Validation.get_valid_input(
        prompt=f"Enter new value for {label}: ",
        validation_fn=validator,
        username=username,
        field_name=field_key
    )

    if new_value is None:
        print("Update cancelled.")
        return

    if update_traveller(customer_id, {field_key: new_value}):
        print("Traveller updated successfully.")
        log_instance.addlog(username, f"{field_key} updated", f"Traveller ID {customer_id}", False)
        time.sleep(1)
    else:
        print("Update failed.")
        log_instance.addlog(username, f"{field_key} update failed", f"Traveller ID {customer_id}", True)
        time.sleep(1)

def delete_traveller_controller(current_user):
    require_authorization(current_user, 'delete_traveller')

    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Delete traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")
    
    # List all travellers first
    travellers = list_travellers(current_user)
    if not travellers:
        print("No travellers found.")
        time.sleep(1)
        return
        
    for t in travellers:
        print(f"ID: {t.id}")
        print(f"First Name: {t.first_name}")
        print(f"Last Name: {t.last_name}")
        print(f"Email: {t.email}")
        print("----------------------------------------------------------------------------")

    try:
        customer_id = int(input("\nEnter traveller ID to delete: ").strip())
    except ValueError:
        print("Invalid ID format. Returning to menu.")
        log_instance.log_invalid_input(current_user.username, "traveller_id", "Invalid ID format for deletion", True)
        time.sleep(1)
        return
    
    # Check if the traveller exists
    target_traveller = next((t for t in travellers if t.id == customer_id), None)
    if not target_traveller:
        print(f"Traveller with ID {customer_id} not found.")
        time.sleep(1)
        return
    
    # Show the traveller details and ask for confirmation
    print(f"\nYou are about to delete:")
    print(f"Name: {target_traveller.first_name} {target_traveller.last_name}")
    print(f"Email: {target_traveller.email}")
    
    confirmation = input(f"\nAre you sure you want to delete this traveller? (yes/no): ").strip().lower()
    
    if confirmation == 'yes':
        if delete_traveller(customer_id):
            print("Traveller deleted successfully.")
            log_instance.addlog(current_user.username, "Traveller deleted", str(customer_id), False)
            time.sleep(1)
        else:
            print("Failed to delete traveller.")
            log_instance.addlog(current_user.username, "Traveller deletion failed", str(customer_id), True)
            time.sleep(1)
    else:
        print("Deletion cancelled.")
        time.sleep(1)
