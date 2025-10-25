import time
from models.scooter import create_scooter, list_scooters, get_scooter_by_serial_number, delete_scooter, update_scooter, search_scooters_partial
from security.validation import Validation
from logs.log import log_instance
from controllers.rolecheck import is_authorized, require_authorization
from helpers.general_methods import general_methods

# Unique validation function for scooter serial number
def unique_serial_number_validation(serial_number, username, exclude_serial=None):
    """Validate serial number format and check for uniqueness."""
    if not Validation.serial_number_validation(serial_number, username):
        return False
    # UE-1: Allow unchanged serial during updates
    if exclude_serial and serial_number.lower() == exclude_serial.lower():
        return True
    if get_scooter_by_serial_number(serial_number):
        print("A scooter with this serial number already exists.")
        log_instance.log_invalid_input(username, "serial_number", "Duplicate serial number")
        return False
    return True

def scooter_menu(current_user):
   while True:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + "Scooter Management".center(75) + "|")
        print("----------------------------------------------------------------------------")

        options = {}

        number = 1

        if is_authorized(current_user.role, 'add_scooter'):
            print(f"[{number}] Add a new scooter")
            options[str(number)] = add_scooter
            number += 1

        if is_authorized(current_user.role, 'show_scooter'):
            print(f"[{number}] View all scooters")
            options[str(number)] = show_scooters
            number += 1

        if is_authorized(current_user.role, 'search_scooter'):
            print(f"[{number}] Search for a scooter")
            options[str(number)] = search_scooter
            number += 1

        if is_authorized(current_user.role, 'delete_scooter'):
            print(f"[{number}] Delete a scooter")
            options[str(number)] = deleting_scooter
            number += 1

        if is_authorized(current_user.role, 'update_scooter'):
            print(f"[{number}] Update a scooter")
            options[str(number)] = update_scooter_controller
            number += 1

        print(f"[0] Return to previous menu")
        return_option = str(0)

        print("----------------------------------------------------------------------------")
        choice = input("Choose an option: ").strip()

        if choice in options:
            options[choice](current_user)
        elif choice == return_option:
            print("Returning to the previous menu...")
            return
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1)

def add_scooter(current_user):
    require_authorization(current_user, 'add_scooter')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Add Scooter".center(75) + "|")
    print("----------------------------------------------------------------------------")

    username = current_user.username

    # 1. BRAND
    brand = Validation.get_valid_input(
        prompt="Brand (or type 'cancel'): ",
        validation_fn=Validation.brand_validation,
        username=username,
        field_name="brand"
    )
    if brand is None: return

    # 2. MODEL
    model = Validation.get_valid_input(
        prompt="Model (or type 'cancel'): ",
        validation_fn=Validation.model_validation,
        username=username,
        field_name="model"
    )
    if model is None: return

    # 3. SERIAL NUMBER (UNIQUE)
    serial_number = Validation.get_valid_input(
        prompt="Serial Number (or type 'cancel'): ",
        validation_fn=lambda serial, user: unique_serial_number_validation(serial, user),
        username=username,
        field_name="serial number"
    )
    if serial_number is None: return

    # 4. TOP SPEED
    top_speed = Validation.get_valid_input(
        prompt="Top Speed km/h (or type 'cancel'): ",
        validation_fn=Validation.top_speed_validation,
        username=username,
        field_name="top speed"
    )
    if top_speed is None: return

    # 5. BATTERY CAPACITY
    battery_capacity = Validation.get_valid_input(
        prompt="Battery Capacity 50-2000 mAh (or type 'cancel'): ",
        validation_fn=Validation.battery_capacity_validation,
        username=username,
        field_name="battery capacity"
    )
    if battery_capacity is None: return

    # 6. SOC
    soc = Validation.get_valid_input(
        prompt="State of Charge 0-100 (or type 'cancel'): ",
        validation_fn=Validation.soc_single_value,
        username=username,
        field_name="state of charge"
    )
    if soc is None: return

    # 7 & 8. SOC RANGE (SR-1)
    soc_range_min, soc_range_max = Validation.get_valid_range_input(
        prompt_min="Target SOC Range MIN 0-99 (or 'cancel'): ",
        prompt_max="Target SOC Range MAX 0-100 (or 'cancel'): ",
        validation_fn=Validation.soc_range_validation,
        username=username,
        field_name="target SOC range"
    )
    if soc_range_min is None or soc_range_max is None: return

    # 9 & 10. LOCATION (LOC-R1)
    location_latitude, location_longitude = Validation.get_valid_coordinates(
        prompt_lat="Latitude (51.85000-52.05000, or 'cancel'): ",
        prompt_lon="Longitude (4.40000-4.55000, or 'cancel'): ",
        validation_fn=Validation.location_validation,
        username=username
    )
    if location_latitude is None or location_longitude is None: return

    # 11. OUT OF SERVICE (yes/no -> ST-A)
    out_of_service = Validation.get_valid_input(
        prompt="Out of Service? (yes/no, or 'cancel'): ",
        validation_fn=Validation.yes_no_validation,
        username=username,
        field_name="out_of_service"
    )
    if out_of_service is None: return
    out_of_service = (out_of_service.lower() == "yes")  # ST-A

    # 12. MILEAGE
    mileage = Validation.get_valid_input(
        prompt="Mileage (or 'cancel'): ",
        validation_fn=Validation.mileage_validation,
        username=username,
        field_name="mileage"
    )
    if mileage is None: return

    # 13. LAST MAINTENANCE DATE
    last_maintenance_date = Validation.get_valid_input(
        prompt="Last Maintenance Date YYYY-MM-DD (or 'cancel'): ",
        validation_fn=Validation.last_maintenance_date_validation,
        username=username,
        field_name="maintenance date"
    )
    if last_maintenance_date is None: return

    # --- FINAL DATABASE CALL ---
    try:
        success = create_scooter(
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
        if success:
            print("\nScooter created successfully.")
            log_instance.addlog(username, "Scooter created", f"Serial: {serial_number}", False)
        else:
            print("\nFailed to create scooter.")
            log_instance.addlog(username, "Scooter creation failed", f"Serial: {serial_number}", True)
    except Exception as e:
        print("\nAn error occurred while creating the scooter.")
        log_instance.addlog(username, "Scooter creation exception", str(e), True)

    general_methods.hidden_input("\nPress Enter to return...")

def show_scooters(current_user):
    require_authorization(current_user, 'show_scooter')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Scooter List".center(75) + "|")
    print("----------------------------------------------------------------------------")

    scooters = list_scooters()
    if scooters:
        for s in scooters:
            print(f"Brand: {s.brand}")
            print(f"Model: {s.model}")
            print(f"Serial Number: {s.serial_number}")
            print(f"Top Speed: {s.top_speed} km/h")
            print(f"Battery Capacity: {s.battery_capacity} mAh")
            print(f"State of Charge: {s.soc}%")
            print(f"SOC Range: {s.soc_range_min}% - {s.soc_range_max}%")
            print(f"Location: Latitude {s.location_latitude}, Longitude {s.location_longitude}")
            print(f"Out of Service: {'Yes' if s.out_of_service else 'No'}")
            print(f"Mileage: {s.mileage} km")
            print(f"Last Maintenance Date: {s.last_maintenance_date}")
            print(f"In Service Date: {s.in_service_date}")
            print("----------------------------------------------------------------------------")
            
    else:
        print("No scooters found.")

    general_methods.hidden_input("\nPress Enter to return to the scooter menu...")

def deleting_scooter(current_user):
    require_authorization(current_user, 'delete_scooter')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Delete Scooter".center(75) + "|")
    print("----------------------------------------------------------------------------")

    username = current_user.username

    # Fetch scooters
    scooters = list_scooters()
    if not scooters:
        print("No scooters available for deletion.")
        general_methods.hidden_input("\nPress Enter to return...")
        return

    # Display scooters (show serial clearly)
    print("\nAvailable Scooters:")
    print("----------------------------------------------------------------------------")
    for s in scooters:
        print(f"Serial: {getattr(s, 'serial_number', '')} | Brand: {getattr(s, 'brand', '')} | "
              f"Model: {getattr(s, 'model', '')} | "
              f"Status: {'out of service' if getattr(s, 'out_of_service', False) else 'in service'}")
    print("----------------------------------------------------------------------------")

    # --- INPUT LOOP FOR SERIAL ---
    while True:
        serial_input = Validation.get_valid_input(
            prompt="\nEnter the SERIAL NUMBER of the scooter to delete (or 'cancel'): ",
            validation_fn=Validation.serial_number_validation,
            username=username,
            field_name="serial number"
        )
        if serial_input is None:
            print("Deletion cancelled.")
            return

        # Find scooter locally first to avoid useless DB calls
        scooter = next((x for x in scooters if getattr(x, 'serial_number', '') == serial_input), None)
        if not scooter:
            print("No scooter found with that serial number. Please try again.")
            log_instance.log_invalid_input(username, "serial_number", "Serial not found for deletion")
            continue
        break

    # --- CONFIRM ---
    confirmation = Validation.get_valid_input(
        prompt=(
            f"Are you sure you want to delete scooter '{getattr(scooter, 'serial_number', '')}' "
            f"({getattr(scooter, 'brand', '')} {getattr(scooter, 'model', '')})? (yes/no): "
        ),
        validation_fn=Validation.yes_no_validation,
        username=username,
        field_name="confirmation"
    )

    # Treat cancel or any answer other than 'yes' as cancel; proceed only on exact 'yes'
    if confirmation is None or confirmation.lower() != "yes":
        print("Deletion cancelled.")
        general_methods.hidden_input("\nPress Enter to return...")
        return

    # --- DELETE VIA MODEL (by serial number) ---
    try:
        success = delete_scooter(getattr(scooter, 'serial_number', None))
    except Exception as e:
        print("An error occurred while deleting scooter:", str(e))
        log_instance.addlog(username, "Scooter deletion exception", str(e), True)
        return

    if success:
        print(f"\nScooter '{getattr(scooter, 'serial_number', '')}' deleted successfully.")
        log_instance.addlog(username, "Scooter deleted", getattr(scooter, 'serial_number', ''), False)
    else:
        print("\nFailed to delete scooter.")
        log_instance.addlog(username, "Scooter delete failed", getattr(scooter, 'serial_number', ''), True)

    general_methods.hidden_input("\nPress Enter to return...")

def update_scooter_controller(current_user):
    require_authorization(current_user, 'update_scooter')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Update Scooter".center(75) + "|")
    print("----------------------------------------------------------------------------")

    # List scooters (compact)
    scooters = list_scooters()
    if not scooters:
        print("No scooters found.")
        general_methods.hidden_input("\nPress Enter to return...")
        return

    for s in scooters:
        # Adjust attribute names if your model differs
        print(f"ID: {s.id} | {getattr(s, 'brand', '')} {getattr(s, 'model', '')} | SN: {getattr(s, 'serial_number', '')}")

    # --- SELECT SCOOTER ID ---
    while True:
        target_id_str = Validation.get_valid_input(
            prompt="\nEnter scooter ID to update (or 'cancel' to stop): ",
            validation_fn=Validation.get_valid_id_input,
            username=current_user.username,
            field_name="scooter_id"
        )
        if target_id_str is None:
            print("Update cancelled.")
            return

        scooter_id = int(target_id_str)
        scooter = next((x for x in scooters if x.id == scooter_id), None)
        if not scooter:
            print("Invalid selection. Please try again.")
            continue
        break

    # --- MENU ---
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Update Scooter".center(75) + "|")
    print("----------------------------------------------------------------------------")

    print("\nWhich field do you want to update?")
    print(f"[1] Brand: {scooter.brand}")
    print(f"[2] Model: {scooter.model}")
    print(f"[3] Serial Number: {scooter.serial_number}")
    print(f"[4] Top Speed: {scooter.top_speed} km/h")
    print(f"[5] Battery Capacity: {scooter.battery_capacity} mAh")
    print(f"[6] State of Charge: {scooter.soc}%")
    print(f"[7] SOC Range (MIN/MAX): {scooter.soc_range_min} - {scooter.soc_range_max}%")
    print(f"[8] Location: Latitude {scooter.location_latitude}, Longitude {scooter.location_longitude}")
    print(f"[9] Out of Service (yes/no): {'Yes' if scooter.out_of_service else 'No'}")
    print(f"[10] Mileage: {scooter.mileage} km")
    print(f"[11] Last Maintenance Date: {scooter.last_maintenance_date}")
    print("[0] Cancel")

    choice = input("Choose a number: ").strip()
    username = current_user.username

    # Simple fields (handled via get_valid_input)
    field_map = {
        '1': ('brand', "Brand (or 'cancel'): ", Validation.brand_validation, str),
        '2': ('model', "Model (or 'cancel'): ", Validation.model_validation, str),
        '4': ('top_speed', "Top Speed km/h (or 'cancel'): ", Validation.top_speed_validation, int),
        '5': ('battery_capacity', "Battery Capacity 50-2000 mAh (or 'cancel'): ", Validation.battery_capacity_validation, int),
        '6': ('soc', "State of Charge 0-100 (or 'cancel'): ", Validation.soc_single_value, int),
        '10': ('mileage', "Mileage (or 'cancel'): ", Validation.mileage_validation, int),
        '11': ('last_maintenance_date', "Last Maintenance Date YYYY-MM-DD (or 'cancel'): ", Validation.last_maintenance_date_validation, str),
    }

    update_data = {}

    # --- CANCEL ---
    if choice == '0':
        print("Update cancelled.")
        return

    # --- SERIAL NUMBER (unique with UE-1) ---
    if choice == '3':
        new_serial = Validation.get_valid_input(
            prompt="Serial Number (or 'cancel'): ",
            validation_fn=lambda serial, user: unique_serial_number_validation(
                serial, user, exclude_serial=getattr(scooter, 'serial_number', '')
            ),
            username=username,
            field_name="serial number"
        )
        if new_serial is None:
            print("Update cancelled.")
            return
        update_data['serial_number'] = new_serial

    # --- SOC RANGE (SR-1, both values) ---
    elif choice == '7':
        new_min, new_max = Validation.get_valid_range_input(
            prompt_min="Target SOC Range MIN 0-99 (or 'cancel'): ",
            prompt_max="Target SOC Range MAX 0-100 (or 'cancel'): ",
            validation_fn=Validation.soc_range_validation,
            username=username,
            field_name="target SOC range"
        )
        if new_min is None or new_max is None:
            print("Update cancelled.")
            return
        update_data['soc_range_min'] = int(new_min)
        update_data['soc_range_max'] = int(new_max)

    # --- LOCATION (LOC-1 + LOC-R1) ---
    elif choice == '8':
        new_lat, new_lon = Validation.get_valid_coordinates(
            prompt_lat="Latitude (51.85000-52.05000, or 'cancel'): ",
            prompt_lon="Longitude (4.40000-4.55000, or 'cancel'): ",
            validation_fn=Validation.location_validation,
            username=username
        )
        if new_lat is None or new_lon is None:
            print("Update cancelled.")
            return
        # LAT-1: store as entered (cast to float only if your model expects float)
        update_data['location_latitude'] = float(new_lat)
        update_data['location_longitude'] = float(new_lon)

    # --- OUT OF SERVICE (yes/no -> boolean ST-A) ---
    elif choice == '9':
        yn = Validation.get_valid_input(
            prompt="Out of Service? (yes/no, or 'cancel'): ",
            validation_fn=Validation.yes_no_validation,
            username=username,
            field_name="out_of_service"
        )
        if yn is None:
            print("Update cancelled.")
            return
        update_data['out_of_service'] = (yn.lower() == 'yes')

    # --- SIMPLE FIELDS (map-driven) ---
    elif choice in field_map:
        field_key, prompt, validator, caster = field_map[choice]
        new_val = Validation.get_valid_input(
            prompt=prompt,
            validation_fn=validator,
            username=username,
            field_name=field_key
        )
        if new_val is None:
            print("Update cancelled.")
            return
        update_data[field_key] = caster(new_val) if caster is not str else new_val

    else:
        print("Invalid choice.")
        return

    # --- APPLY UPDATE ---
    try:
        success = update_scooter(scooter_id, update_data)
    except Exception as e:
        print("An error occurred while updating scooter:", str(e))
        log_instance.addlog(username, "Scooter update exception", str(e), True)
        return

    if success:
        print("\nScooter updated successfully.")
        log_instance.addlog(username, "Scooter updated", str(update_data), False)
    else:
        print("\nUpdate failed.")
        log_instance.addlog(username, "Scooter update failed", str(update_data), True)

    general_methods.hidden_input("\nPress Enter to return...")

def search_scooter(current_user):
    require_authorization(current_user, 'search_scooter')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Search scooter".center(75) + "|")
    print("----------------------------------------------------------------------------")

    query = Validation.get_valid_input(
        prompt="Enter a part of a brand/model or serialnumber: ",
        validation_fn=Validation.is_valid_search_input, 
        username=current_user.username,
        field_name="search scooter"
    )
    
    result = search_scooters_partial(query)
    number_of_results = len(result) if result else 0

    if result:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + "Found scooters".center(75) + "|")
        print("----------------------------------------------------------------------------")
        for s in result:
            print(f"ID: {s.id}")
            print(f"Brand: {s.brand}")
            print(f"Model: {s.model}")
            print(f"Serial Number: {s.serial_number}")
            print(f"Top Speed: {s.top_speed} km/h")
            print(f"Battery Capacity: {s.battery_capacity} mAh")
            print(f"State of Charge: {s.soc}%")
            print(f"SOC Range: {s.soc_range_min}% - {s.soc_range_max}%")
            print(f"Location: Latitude {s.location_latitude}, Longitude {s.location_longitude}")
            print(f"Out of Service: {'Yes' if s.out_of_service else 'No'}")
            print(f"Mileage: {s.mileage} km")
            print(f"Last Maintenance Date: {s.last_maintenance_date}")
            print(f"In Service Date: {s.in_service_date}")
            print("----------------------------------------------------------------------------")
            log_instance.addlog(current_user.username, "Scooter search", query, False)
    else:
        print("No matching scooters found.")
        log_instance.addlog(current_user.username, "Scooter search - no results", query, False)
    
    general_methods.hidden_input("\nPress Enter to return to the scooter menu...")
