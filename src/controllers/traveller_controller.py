from security.validation import Validation
from models.traveller import create_traveller, list_travellers, find_travellers, update_traveller, delete_traveller
from logs.log import log_instance
from controllers.rolecheck import require_authorization
from helpers.general_methods import general_methods

import sys

def traveller_menu(current_user):
    while True:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + f"Traveller Management".center(75) + "|")
        print("----------------------------------------------------------------------------")

        print("1. Register new traveller")
        print("2. Search for a traveller")
        print("3. Delete a traveller")
        print("4. Update traveller information")
        print("5. List all travellers")
        print("0. Return to previous menu")


        choice = input("Choose an option: ").strip()

        if choice == '1':
            add_traveller(current_user)
        elif choice == '2':
            search_traveller(current_user)
        elif choice == '3':
            delete_traveller_controller(current_user)
        elif choice == '4':
            update_traveller_controller(current_user)
        elif choice == '5':
            show_travellers(current_user)
            return
        elif choice == '0':
            print("Returning to previous menu...")
            return
        else:
            print("Invalid choice. Please try again.")

def get_valid_input(prompt, validation_fn, username, field_name):
    attempts = 0
    while attempts < 3:
        value = input(prompt).strip()
        if validation_fn(value, username):
            return value
        attempts += 1
        log_instance.log_invalid_input(username, field_name, f"Invalid {field_name} input")
        print(f"Invalid {field_name}. Please try again.")
    print("Too many failed attempts. You have been logged out.")
    sys.exit()

def show_travellers(current_user):
    require_authorization(current_user, 'show_traveller')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Traveller list".center(75) + "|")
    print("----------------------------------------------------------------------------")

    travellers = list_travellers(current_user)
    if travellers:
        for t in travellers:
            print(f"ID: {t.id} | Name: {t.first_name} {t.last_name} | Email: {t.email}")
    else:
        print("No travellers found.")

    general_methods.hidden_input("\nPress Enter to return to the traveller menu...")

# TODO specify phone number format in prompt
def add_traveller(current_user):
    require_authorization(current_user, 'add_traveller')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Register New Traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")

    username = current_user.username

    first_name = get_valid_input("First Name: ", Validation.name_validation, username, "first name")
    last_name = get_valid_input("Last Name: ", Validation.name_validation, username, "last name")
    date_of_birth = get_valid_input("Date of Birth (YYYY-MM-DD): ", Validation.birthday_validation, username, "date of birth")
    gender = get_valid_input("Gender (male/female): ", Validation.gender_validation, username, "gender")
    street = get_valid_input("Street: ", Validation.street_validation, username, "street")
    house_number = get_valid_input("House Number: ", Validation.housenumber_validation, username, "house number")
    zip_code = get_valid_input("Zip Code (e.g., 1234AB): ", Validation.zipcode_validation, username, "zip code")
    city = get_valid_input("City: ", Validation.city_validation, username, "city")
    email = get_valid_input("Email: ", Validation.email_validation, username, "email")
    phone_number = get_valid_input("Phone Number (+31-6-xxxxxxxx): ", Validation.phone_validation, username, "phone number")
    license_number = get_valid_input("License Number (XX1234567 or X1234567): ", Validation.license_validation, username, "license number")

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
    else:
        print("Failed to register traveller.")
        log_instance.addlog(username, "Traveller registration failed", f"{first_name} {last_name}", True)

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

    if result:
        print("\n--- Search Results ---")
        for r in result:
            print(f"{r['first_name']} {r['last_name']} | ID: {r['id']} | Email: {r['email']}")
        log_instance.addlog(current_user.username, "Traveller search", query, False)
    else:
        print("No matching travellers found.")
        log_instance.addlog(current_user.username, "Traveller search - no results", query, False)
    general_methods.hidden_input("\nPress Enter to return to the traveller menu...")

def update_traveller_controller(current_user):
    require_authorization(current_user, 'update_traveller')

    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Update traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")

    try:
        customer_id = int(input("Enter traveller ID to update: ").strip())
    except ValueError:
        print("Invalid ID format.")
        log_instance.log_invalid_input(current_user.username, "traveller_id", "Invalid ID format", True)
        return

    print("\nWhich field do you want to update?")
    print("1. First Name")
    print("2. Last Name")
    print("3. Date of Birth")
    print("4. Gender")
    print("5. Street")
    print("6. House Number")
    print("7. Zip Code")
    print("8. City")
    print("9. Email")
    print("10. Phone Number")
    print("11. License Number")
    print("0. Cancel")

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
        return

    field_key, label, validator = field_map[choice]
    if field_key is None:
        print("Cancelled.")
        return

    # Input via get_valid_input()
    new_value = Validation.get_valid_input(
        prompt=f"Enter new value for {label}: ",
        validation_fn=validator,
        username=username,
        field_name=field_key
    )

    if update_traveller(customer_id, {field_key: new_value}):
        print("Traveller updated successfully.")
        log_instance.addlog(username, f"{field_key} updated", f"Traveller ID {customer_id}", False)
    else:
        print("Update failed.")
        log_instance.addlog(username, f"{field_key} update failed", f"Traveller ID {customer_id}", True)

def delete_traveller_controller(current_user):
    require_authorization(current_user, 'delete_traveller')

    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + f"Delete traveller".center(75) + "|")
    print("----------------------------------------------------------------------------")

    customer_id = input("Enter traveller ID to delete: ").strip()
    confirmation = input(f"Are you sure you want to delete traveller with ID {customer_id}? (yes/no): ").strip().lower()

    if confirmation == 'yes':
        try:
            # Assuming a function delete_traveller exists in the model
            delete_traveller(customer_id)
            print("Traveller deleted successfully.")
            log_instance.addlog(current_user.username, "Traveller deleted", customer_id, False)
        except Exception as e:
            print(f"Error while deleting traveller: {e}")
            log_instance.addlog(current_user.username, "Traveller deletion failed", str(e), True)
    else:
        print("Deletion cancelled.")
