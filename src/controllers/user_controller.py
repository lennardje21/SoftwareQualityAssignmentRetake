import time
from security.validation import Validation
from models.user import get_user_by_username, create_user, update_password, list_users, User, delete_user_by_id, update_user_by_id, update_password_by_id, clear_temporary_passwords, get_user_password_by_username
from logs.log import log_instance
from controllers.rolecheck import is_authorized
from security.password_hashing import validate_password
from controllers.rolecheck import require_authorization
from helpers.general_methods import general_methods

def user_menu(user_data: User):
    if not isinstance(user_data, User):
        print("Access denied: invalid user type.")
        return

    while True:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + f"User Menu".center(75) + "|")
        print("----------------------------------------------------------------------------")
        number = 1

        if is_authorized(user_data.role, "add_new_user"):
            print(f"[{number}] Create new user")
            create_user_option = str(number)
            number += 1
        else:
            create_user_option = None

        if is_authorized(user_data.role, "view_users"):
            print(f"[{number}] List all users")
            list_users_option = str(number)
            number += 1
        else:
            list_users_option = None

        if is_authorized(user_data.role, "delete_user"):
            print(f"[{number}] Delete a user")
            delete_user_option = str(number)
            number += 1
        else:
            delete_user_option = None

        if is_authorized(user_data.role, "update_user"):
            print(f"[{number}] Update user account")
            update_user_option = str(number)
            number += 1
        else:
            update_user_option = None

        if is_authorized(user_data.role, "reset_password"):
            print(f"[{number}] Reset user password")
            reset_pw_option = str(number)
            number += 1
        else:
            reset_pw_option = None

        print(f"[{0}] Return to previous menu")
        exit_option = str(0)

        choice = input("Choose an option: ").strip()

        if choice == create_user_option:
            create_new_user(user_data)

        elif choice == list_users_option:
            show_all_users(user_data)

        elif choice == delete_user_option:
            delete_user_account(user_data)

        elif choice == update_user_option:
            update_user_account(user_data)

        elif choice == reset_pw_option:
            reset_user_password(user_data)

        elif choice == exit_option:
            return

        else:
            print("Invalid choice. Please try again.")

def view_profile(user):
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "User Profile".center(75) + "|")
    print("----------------------------------------------------------------------------")

    print(f"Username: {user.username}")
    print(f"Role: {user.role.replace('_', ' ').title()}")
    print(f"Registration Date: {user.registration_date}")

    general_methods.hidden_input("\nPress Enter to return to the user menu...")

def create_new_user(current_user):
    require_authorization(current_user, 'add_new_user')

    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Creating a new user".center(75) + "|")
    print("----------------------------------------------------------------------------")
    
    print("Username requirements: 8-10 characters, letters and numbers only.")
    while True:
        username = Validation.get_valid_input(
            prompt="Enter username (or 'cancel' to stop): ",
            validation_fn=lambda val, un: Validation.username_validation(val.lower()),
            username=current_user.username,
            field_name="username"
        )
        if username is None:
            return
        if get_user_by_username(username):
            print("Username already exists. Please try again.")
            log_instance.log_invalid_input(current_user.username, "username", "Attempt to create duplicate username", False)
            continue
        break
    
    print("Password requirements: At least 12 characters, including uppercase, lowercase, number, and special character (or 'cancel' to stop): ")
    password = Validation.get_valid_input(
    prompt="Enter password: ",
    validation_fn=Validation.password_validation,
    username=current_user.username,
    field_name="password"
    )
    if password is None:
        return
    allowed_roles = get_permitted_roles(current_user.role)
    # Build a whitelist mapping from both names (exact case and lowercase) and numbers -> role names
    role_lookup = {str(v): k for k, v in allowed_roles.items()}
    role_lookup.update({k.lower(): k for k in allowed_roles})  # Add lowercase variants to whitelist
    
    role_options = [f"{num}: {name}" for name, num in allowed_roles.items()]
    
    while True:
        # Accept input with .strip(), then check against whitelist (includes lowercase)
        role = input(f"Enter role ({', '.join(role_options)}) (or 'cancel' to stop): ").strip().lower()
        if role == "cancel":
            return
        # Check against whitelist (includes lowercase variants)
        if role in role_lookup:
            chosen_role = role_lookup[role]
            print(f"Selected role: {chosen_role}")
            break
        else:
            print("Invalid role. Please try again.")
    
    print("First and last names should only contain letters, hyphens, apostrophes, or spaces (or 'cancel' to stop):")    
    firstname = Validation.get_valid_input(
        prompt="Enter first name: ",
        validation_fn=Validation.name_validation,
        username=current_user.username,
        field_name="first name"
        )
    if firstname is None:
        return

    lastname = Validation.get_valid_input(
        prompt="Enter last name: ",
        validation_fn=Validation.name_validation,
        username=current_user.username,
        field_name="last name"
        )

    if lastname is None:
        return
    
    try:
        create_user(username, firstname, lastname, password, chosen_role)  # Store exactly what was validated
        log_instance.addlog(current_user.username, f"User creation", f"Account with username {username} created", False)
        print(f"{chosen_role} {username} created successfully.")
    except Exception as e:
        log_instance.addlog(current_user.username, f"Failed User creation for {username}", str(e), True)
        print("Error while creating user. Please contact system administrator.")

    general_methods.hidden_input("\nPress Enter to return to the user menu...")

def show_all_users(current_user):
    require_authorization(current_user, 'view_users')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Show all users".center(75) + "|")
    print("----------------------------------------------------------------------------")

    users = list_users()
    if users:
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Firstname: {user.firstname}")
            print(f"Lastname: {user.lastname}")
            print(f"Role: {user.role}")
            print("----------------------------------------------------------------------------")
    else:
        print("No users found.")
    
    general_methods.hidden_input("\nPress Enter to return to the user menu...")

def get_permitted_roles(user_role):
    role_permissions = {
        'super_administrator': {
            'service_engineer': 1,
            'system_administrator': 2
        },
        'system_administrator': {
            'service_engineer': 1
        }
    }
    return role_permissions.get(user_role, {})

def get_deletable_users(current_user):
    all_users = list_users()
    deletable = []

    for user in all_users:
        if user.username == current_user.username:
            continue  # users can not delete themselves

        if user.role == "super_administrator":
            continue  # super_admin may not be deleted

        if user.role == "system_administrator" and current_user.role == "super_administrator":
            deletable.append(user)

        elif user.role == "service_engineer" and current_user.role in ["system_administrator", "super_administrator"]:
            deletable.append(user)

        # Removed insecure logic that allowed deletion of users with role "1"

    return deletable

def delete_user_account(current_user):
    require_authorization(current_user, 'delete_user')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Delete a User".center(75) + "|")
    print("----------------------------------------------------------------------------")

    deletable_users = get_deletable_users(current_user)
    if not deletable_users:
        print("No users available for deletion.")
        general_methods.hidden_input("Press Enter to return...")
        return

    print("\nUsers you are authorized to delete:")
    for user in deletable_users:
        print(f"ID: {user.id} | Username: {user.username} | Role: {user.role}")

    # --- USER ID INPUT LOOP ---
    while True:
        target_id_str = Validation.get_valid_input(
            prompt="\nEnter the ID of the user you want to delete (or 'cancel' to stop): ",
            validation_fn=Validation.get_valid_id_input,
            username=current_user.username,
            field_name="id"
        )

        if target_id_str is None:   # user typed "cancel"
            print("Deletion cancelled.")
            return

        target_id = int(target_id_str)
        target_user = next((u for u in deletable_users if u.id == target_id), None)

        if not target_user:
            print("Invalid selection. Please try again.")
            continue  # ask again

        break  # valid target user selected

    # --- CONFIRMATION STEP ---
    confirmation = Validation.get_valid_input(
        prompt=f"Are you sure you want to delete '{target_user.username}'? (yes/no, or 'cancel'): ",
        validation_fn=Validation.yes_no_validation,
        username=current_user.username,
        field_name="confirmation"
    )
    if confirmation is None or confirmation.lower() == "no":
        print("Deletion cancelled.")
        general_methods.hidden_input("\nPress Enter to return...")
        return

    # --- PERFORM DELETE ---
    success = delete_user_by_id(target_id)
    if success:
        print(f"User '{target_user.username}' deleted successfully.")
        log_instance.addlog(current_user.username, "User deleted", target_user.username, False)
    else:
        print("Failed to delete user.")
        log_instance.addlog(current_user.username, "User delete failed", target_user.username, True)

    general_methods.hidden_input("\nPress Enter to return to the user menu...")

def get_editable_users(current_user):
    all_users = list_users()
    editable = []

    for user in all_users:
        if user.username == current_user.username:
            continue  # users can not edit themselves

        if user.role == "super_administrator":
            continue  # super_admin may not be edited

        if user.role == "system_administrator":
            if current_user.role == "super_administrator":
                editable.append(user)

        elif user.role == "service_engineer":
            if current_user.role in ["super_administrator", "system_administrator"]:
                editable.append(user)

    return editable

def update_user_account(current_user):
    require_authorization(current_user, 'update_user')
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Update a User Account".center(75) + "|")
    print("----------------------------------------------------------------------------")

    # Show editable users
    editable_users = get_editable_users(current_user)
    if not editable_users:
        print("No users available to update.")
        general_methods.hidden_input("Press Enter to return...")
        return

    for user in editable_users:
        print(f"ID: {user.id} | Username: {user.username} | Role: {user.role}")

    # --- USER SELECTION LOOP ---
    while True:
        target_id_str = Validation.get_valid_input(
            prompt="\nEnter the ID of the user you want to update (or 'cancel' to stop): ",
            validation_fn=Validation.get_valid_id_input,
            username=current_user.username,
            field_name="id"
        )
        if target_id_str is None:  # cancel
            print("Update cancelled.")
            return

        target_id = int(target_id_str)
        target_user = next((u for u in editable_users if u.id == target_id), None)

        if not target_user:
            print("Invalid selection. Please try again.")
            continue
        break
    # --- FIELD SELECTION LOOP ---
    while True:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + f"Update User: {target_user.firstname} {target_user.lastname}".center(75) + "|")
        print("----------------------------------------------------------------------------")
        print("\nWhich field do you want to update?")
        print(f"[1] Username: {target_user.username}")
        print(f"[2] First Name: {target_user.firstname}")
        print(f"[3] Last Name: {target_user.lastname}")
        print(f"[0] Cancel")

        choice = input("Choose an option: ").strip()

        update_data = {}
        if choice == '1':
            # Username update behavior same as CREATE
            print("Username requirements: 8-10 characters, letters and numbers only.")
            while True:
                # Normalize username to lowercase BEFORE validation (case-insensitive per spec)
                new_username = input("Enter new username (or 'cancel' to stop): ").strip().lower()

                if new_username == "cancel":
                    print("Update cancelled.")
                    return

                if not Validation.username_validation(new_username):
                    continue  # format invalid -> retry

                if get_user_by_username(new_username):
                    print("Username already exists. Please try again.")
                    log_instance.log_invalid_input(current_user.username, "username",
                                                   "Attempt to create duplicate username", False)
                    continue  # duplicate -> retry

                update_data = {"username": new_username}
                break
            break

        elif choice == '2':
            new_first = Validation.get_valid_input(
                prompt="Enter new first name (or 'cancel' to stop): ",
                validation_fn=Validation.name_validation,
                username=current_user.username,
                field_name="first name"
            )
            if new_first is None:
                print("Update cancelled.")
                return
            update_data = {"firstname": new_first}  # Store exactly what was validated
            break

        elif choice == '3':
            new_last = Validation.get_valid_input(
                prompt="Enter new last name (or 'cancel' to stop): ",
                validation_fn=Validation.name_validation,
                username=current_user.username,
                field_name="last name"
            )
            if new_last is None:
                print("Update cancelled.")
                return
            update_data = {"lastname": new_last}  # Store exactly what was validated
            break

        elif choice == '0':
            print("Update cancelled.")
            return

        else:
            print("Invalid option. Please try again.")
            continue

    # --- APPLY UPDATE ---
    success = update_user_by_id(target_id, update_data)
    if success:
        print("User updated successfully.")
        log_instance.addlog(current_user.username, "User updated", str(update_data), False)
    else:
        print("Failed to update user.")
        log_instance.addlog(current_user.username, "User update failed", str(update_data), True)

    general_methods.hidden_input("\nPress Enter to return to the user menu...")

def change_own_password(current_user) -> bool:
    require_authorization(current_user, 'update_own_password')
 
    general_methods.clear_console()
    print("----------------------------------------------------------------------------")
    print("|" + "Change Your Own Password".center(75) + "|")
    print("----------------------------------------------------------------------------")

    stored_hash = get_user_password_by_username(current_user.username)
    if not stored_hash:
        print("User not found.")
        return False

    # 3 attempts for current password
    for attempt in range(3):
        old_password = input("Enter your current password: ").strip()
        # Security: reject null bytes in current password input
        if Validation.contains_null_byte(old_password):
            print("Invalid current password input.")
            log_instance.log_invalid_input(current_user.username, "password", "Null byte detected in current password", suspicious=True)
            continue
        if validate_password(old_password, stored_hash):
            break  # correct -> ga door
        else:
            print("Incorrect current password.")
            log_instance.log_invalid_input(current_user.username, "password", "Incorrect current password")

    else:
        print("Too many incorrect current password attempts. Logging out...")
        log_instance.addlog(current_user.username, "Password change failed", "Too many old password attempts", True)
        time.sleep(1)
        return True  # force logout

    new_password = Validation.get_valid_input(
        "Enter your new password: ",
        Validation.password_validation,
        current_user.username,
        "password"
    )

    success = update_password(current_user.username, new_password)
    if success:
        log_instance.addlog(current_user.username, "Password changed successfully", "", False)
        print("Password changed successfully. You will now be logged out.")
        time.sleep(1)
        return True
    else:
        log_instance.addlog(current_user.username, "Password change failed", "Database error", True)
        print("Password change failed. Returning to menu.")
        time.sleep(1)
        return False

def reset_user_password(current_user):
    require_authorization(current_user, 'reset_password')
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Reset User Password".center(75) + "|")
    print("----------------------------------------------------------------------------")

    editable_users = get_editable_users(current_user)
    if not editable_users:
        print("No users available for password reset.")
        general_methods.hidden_input("Press Enter to return...")
        return

    # Display eligible users
    for user in editable_users:
        print(f"ID: {user.id} | Username: {user.username} | Role: {user.role}")

    # ----- ID INPUT LOOP -----
    while True:
        user_input = Validation.get_valid_input(
            "\nEnter the ID of the user (or type 'cancel' to stop): ",
            Validation.get_valid_id_input,
            current_user.username,
            "user id"
        )
        if user_input is None:
            print("Password reset cancelled.")
            return

        target_id = int(user_input)
        target_user = next((u for u in editable_users if u.id == target_id), None)

        if not target_user:
            print("User not found or not editable by your role. Try again.")
            continue
        break  # valid user -- exit loop

    # ----- PASSWORD INPUT -----
    new_pw = Validation.get_valid_input(
        "Enter new temporary password (or type 'cancel' to stop): ",
        Validation.password_validation,
        current_user.username,
        "password"
    )

    if new_pw is None:  # user typed cancel
        print("Password reset cancelled.")
        return

    # ----- UPDATE PASSWORD -----
    success = update_password_by_id(target_id, new_pw)

    if success:
        print(f"Temporary password has been reset for user '{target_user.username}'.")
        log_instance.addlog(current_user.username, "Password reset", f"Target: {target_user.username}", False)
    else:
        print("Password reset failed.")
        log_instance.addlog(current_user.username, "Password reset failed", f"Target: {target_user.username}", True)

    general_methods.hidden_input("\nPress Enter to return...")
