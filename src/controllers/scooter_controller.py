import sys
from models.scooter import create_scooter, list_scooters , get_scooter_by_serial_number, delete_scooter, update_scooter, search_scooters_partial
from security.validation import Validation
from logs.log import log_instance
from controllers.rolecheck import is_authorized, require_authorization
from security.encryption import load_symmetric_key

def scooter_menu(current_user):
   while True:
        print("\n--- Scooter Management ---")
        options = {}

        number = 1

        if is_authorized(current_user.role, 'add_scooter'):
            print(f"{number}. Add a new scooter")
            options[str(number)] = add_scooter
            number += 1

        if is_authorized(current_user.role, 'show_scooter'):
            print(f"{number}. View all scooters")
            options[str(number)] = show_scooters
            number += 1

        if is_authorized(current_user.role, 'search_scooter'):
            print(f"{number}. Search for a scooter")
            options[str(number)] = search_scooter
            number += 1

        if is_authorized(current_user.role, 'delete_scooter'):
            print(f"{number}. Delete a scooter")
            options[str(number)] = deleting_scooter
            number += 1

        if is_authorized(current_user.role, 'update_scooter'):
            print(f"{number}. Update a scooter")
            options[str(number)] = update_scooter_controller
            number += 1

        print(f"{number}. Return to previous menu")
        return_option = str(number)

        choice = input("Choose an option: ").strip()

        if choice in options:
            options[choice](current_user)
        elif choice == return_option:
            print("Returning to the previous menu...")
            return
        else:
            print("Invalid choice. Please try again.")




def add_scooter(current_user):
    print("\n--- Add a New Scooter ---")
    require_authorization(current_user, 'add_scooter')
    
    username = current_user.username
    
    brand = Validation.get_valid_input("Brand: ", Validation.brand_validation, username, "brand")
    model = Validation.get_valid_input("Model: ", Validation.model_validation, username, "model")
    for attempt in range(3):
        serial_number = input("Serial Number (10–17 alphanumeric): ").strip()
        if not Validation.serial_number_validation(serial_number, username):
            continue
        if get_scooter_by_serial_number(serial_number):
            print("Serial number already exists. Please try again.")
            log_instance.log_invalid_input(username, "serial_number", "Attempt to create duplicate serial number")
            continue
        break
    else:
        print("Too many failed serial number attempts.")
        log_instance.log_invalid_input(username, "scooter adding", "Too many failed serial number attempts")
        sys.exit()
    top_speed = Validation.get_valid_input("Top Speed (1–300): ", Validation.top_speed_validation, username, "top speed")
    battery_capacity = Validation.get_valid_input("Battery Capacity (50–2000): ", Validation.battery_capacity_validation, username, "battery capacity")
    soc = Validation.get_valid_input("State of Charge (0–100): ", Validation.soc_single_value, username, "state of charge")
    soc_range_min, soc_range_max = Validation.get_valid_range_input(
        "Target SOC Range MIN (0–100): ",
        "Target SOC Range MAX (0–100): ",
        Validation.soc_range_validation,
        username,
        "Target SOC Range"
    )

    # Locatie (exact 5 decimalen, binnen Rotterdam)
    location_latitude, location_longitude = Validation.get_valid_coordinates(
        "Latitude (format XX.XXXXX): ",
        "Longitude (format X.XXXXX): ",
        Validation.location_validation,
        username
    )

    # TODO: controleer voor inputvalidation boolean
    out_of_service = Validation.get_valid_input(
        "Out of Service? (yes/no): ",
        Validation.yes_no_validation,
        username,
        "out_of_service"
    )
    mileage = Validation.get_valid_input("Mileage: ", Validation.mileage_validation, username, "mileage")
    last_maintenance_date = Validation.get_valid_input("Last Maintenance Date (YYYY-MM-DD): ", Validation.last_maintenance_date_validation, username, "maintenance date")

    #Proberen scooter aan te maken
    try:
        result = create_scooter(
            brand=brand,
            model=model,
            serial_number=serial_number,
            top_speed=int(top_speed),
            battery_capacity=int(battery_capacity),
            soc=int(soc),
            soc_range_min=int(soc_range_min),
            soc_range_max=int(soc_range_max),
            location_latitude=float(location_latitude),
            location_longitude=float(location_longitude),
            out_of_service=out_of_service,
            mileage=int(mileage),
            last_maintenance_date=last_maintenance_date
        )
        if result:
            log_instance.addlog(username, "Scooter created", serial_number, False)
            print(" Scooter registered successfully.")
        else:
            log_instance.addlog(username, "Scooter creation failed", serial_number, True)
            print("Failed to register scooter.")
    except Exception as e:
        log_instance.addlog(username, "Scooter creation exception", str(e), True)
        print("An error occurred while registering the scooter.")


def show_scooters(current_user):
    require_authorization(current_user, 'show_scooter')

    scooters = list_scooters()
    if scooters:
        print("\n--- Scooter List ---")
        for s in scooters:
            lat = float(s.location_latitude)
            lon = float(s.location_longitude)
            print(f"{s.brand} {s.model} - Serial: {s.serial_number}, Location: ({s.location_latitude}, {s.location_longitude})")
    else:
        print("No scooters found.")


def deleting_scooter(current_user):
    require_authorization(current_user, 'delete_scooter')
    
    print("\n--- Delete a Scooter ---")
    key = load_symmetric_key()
    
    serial_number = Validation.get_valid_input(
        "Enter the serial number of the scooter to delete: ",
        Validation.serial_number_validation,
        current_user.username,
        "serial_number"
    )

    scooter = get_scooter_by_serial_number(serial_number)
    
    if scooter:
        confirmation = input(f"Are you sure you want to delete scooter {scooter.serial_number}? (yes/no): ").strip().lower()
        if confirmation == 'yes':
            delete_scooter(serial_number)
            print(f"Scooter {scooter.serial_number} deleted successfully.")
            log_instance.addlog(current_user.username, "Scooter deleted", serial_number, False)
        else:
            print("Deletion cancelled.")
    else:
        print("Scooter not found.")

def update_scooter_controller(current_user):
    require_authorization(current_user, 'update_scooter')

    # Show scooters
    scooters = list_scooters()
    if not scooters:
        print("No scooters available to update.")
        return

    print("\n--- Available Scooters ---")
    for s in scooters:
        print(f"ID: {s.id} | Brand: {s.brand} | Model: {s.model} | Serial: {s.serial_number}")

    try:
        scooter_id = int(input("\nEnter the ID of the scooter to update: ").strip())
    except ValueError:
        print("Invalid ID.")
        return

    # Search the scooter
    target_scooter = next((s for s in scooters if s.id == scooter_id), None)
    if not target_scooter:
        print("Scooter not found.")
        return

    username = current_user.username

    allowed_fields_per_role = {
        'super_administrator': [str(i) for i in range(1, 14)],
        'system_administrator': [str(i) for i in range(1, 14)],
        'service_engineer': ['3', '4','5', '6', '7', '8', '9', '10', '11', '12'],
    }

    field_map = {
        '1': ('brand', "Brand", Validation.brand_validation),
        '2': ('model', "Model", Validation.model_validation),
        '3': ('top_speed', "Top Speed (1–300)", Validation.top_speed_validation),
        '4': ('battery_capacity', "Battery Capacity (200–3000)", Validation.battery_capacity_validation),
        '5': ('soc', "State of Charge (0–100)", Validation.soc_single_value),
        '6': ('soc_range_min', "SOC Range Min (0–100)", lambda v, u: True),
        '7': ('soc_range_max', "SOC Range Max (0–100)", lambda v, u: True),
        '8': ('location_latitude', "Latitude (format XX.XXXXX)", lambda v, u: True),
        '9': ('location_longitude', "Longitude (format X.XXXXX)", lambda v, u: True),
        '10': ('out_of_service', "Out of Service (yes/no)", lambda v, u: v.lower() in ['yes', 'no']),
        '11': ('mileage', "Mileage", Validation.mileage_validation),
        '12': ('last_maintenance_date', "Last Maintenance Date (YYYY-MM-DD)", Validation.last_maintenance_date_validation),
        '13' : ('serial_number', "Serial Number (10–17 alphanumeric)", Validation.serial_number_validation),
    }

    # give the user a choice of fields to update
    allowed = allowed_fields_per_role.get(current_user.role, [])
    print("\nWhich field do you want to update?")
    for key in allowed:
        label = field_map[key][1]
        print(f"{key}. {label}")
    print("0. Cancel")

    choice = input("Choose a number: ").strip()

    if choice == '0':
        print("Update cancelled.")
        return

    if choice not in allowed:
        print("You are not authorized to update this field.")
        log_instance.addlog(username, "Unauthorized scooter field update", f"Field {choice}", True)
        return

    field_key, label, validator = field_map[choice]
   
    if choice == '13':
        MAX_SERIAL_ATTEMPTS = 3
        serial_attempts = 0
        valid_serial = False
        
        while not valid_serial and serial_attempts < MAX_SERIAL_ATTEMPTS:
            new_value = input(f"Enter new value for {label}: ").strip()
            
            # Validate serial number format
            if not validator(new_value, username):
                serial_attempts += 1
                log_instance.log_invalid_input(username, "serial_number", "Invalid serial number format")
                
                if serial_attempts >= MAX_SERIAL_ATTEMPTS:
                    print("Too many failed serial number attempts.")
                    log_instance.addlog(username, "Scooter update", "Too many failed serial number attempts", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
                continue
            
            # Check if serial number is already in use by another scooter
            existing_scooter = get_scooter_by_serial_number(new_value)
            if existing_scooter and existing_scooter.id != target_scooter.id:
                serial_attempts += 1
                print("Serial number already exists. Please try again.")
                log_instance.log_invalid_input(username, "serial_number", "Attempt to use duplicate serial number")
                
                if serial_attempts >= MAX_SERIAL_ATTEMPTS:
                    log_instance.addlog(username, "Scooter update", "Too many failed serial number attempts", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
                continue
            
            valid_serial = True
    else:
        # For other fields, just get the input once
        new_value = input(f"Enter new value for {label}: ").strip()


    # SOC-range specific validation
    if choice in ['6', '7']:
        if not new_value.isdigit() or not (0 <= int(new_value) <= 100):
            print("SOC range must be between 0 and 100.")
            return
        if choice == '6':  # Min
            soc_max = int(target_scooter.soc_range_max)
            if int(new_value) >= soc_max:
                print(f"SOC Range Min must be less than SOC Range Max ({soc_max}).")
                return
        elif choice == '7':  # Max
            soc_min = int(target_scooter.soc_range_min)
            if int(new_value) <= soc_min:
                print(f"SOC Range Max must be greater than SOC Range Min ({soc_min}).")
                return

    # Locatie validation
    if choice == '8':
        if not Validation.location_validation(new_value, target_scooter.location_longitude, username):
            return
    elif choice == '9':
        if not Validation.location_validation(target_scooter.location_latitude, new_value, username):
            return

    if not validator(new_value, username):
        print(f"Invalid {label}. Update cancelled.")
        log_instance.log_invalid_input(username, field_key, f"Update validation failed")
        return

    # Convert
    if field_key == 'out_of_service':
        new_value = new_value.lower() == 'yes'
    elif field_key in ['top_speed', 'battery_capacity', 'soc', 'soc_range_min', 'soc_range_max', 'mileage']:
        new_value = int(new_value)
    elif field_key in ['location_latitude', 'location_longitude']:
        new_value = float(new_value)

    # Update the scooter
    if update_scooter(scooter_id, {field_key: new_value}):
        print("Scooter updated successfully.")
        log_instance.addlog(username, f"Scooter {field_key} updated", f"ID: {scooter_id}", False)
    else:
        print("Update failed.")
        log_instance.addlog(username, f"Scooter {field_key} update failed", f"ID: {scooter_id}", True)

def search_scooter(current_user):
    require_authorization(current_user, 'search_scooter')

    query = Validation.get_valid_input(
        prompt="Enter a part of a brand/ model or serialnumber: ",
        validation_fn=Validation.is_valid_search_input, 
        username=current_user.username,
        field_name="search scooter"
    )
    
    result = search_scooters_partial(query)

    if result:
        print("\n--- Search Results ---")
        for scooter in result:
            print(f"Brand: {scooter.brand}, Model: {scooter.model}, Serial Number: {scooter.serial_number}")
            log_instance.addlog(current_user.username, "Scooter search", query, False)
    else:
        print("No matching scooters found.")
        log_instance.addlog(current_user.username, "Scooter search - no results", query, False)
