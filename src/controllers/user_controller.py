import sys
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

        if is_authorized(user_data.role, "update_own_password"):
            print(f"{number}. Change password")
            change_pw_option = str(number)
            number += 1
        else:
            change_pw_option = None

        print(f"{number}. View profile")
        view_profile_option = str(number)
        number += 1

        if is_authorized(user_data.role, "add_new_user"):
            print(f"{number}. Create new user")
            create_user_option = str(number)
            number += 1
        else:
            create_user_option = None

        if is_authorized(user_data.role, "view_users"):
            print(f"{number}. List all users")
            list_users_option = str(number)
            number += 1
        else:
            list_users_option = None

        if is_authorized(user_data.role, "delete_user"):
            print(f"{number}. Delete a user")
            delete_user_option = str(number)
            number += 1
        else:
            delete_user_option = None

        if is_authorized(user_data.role, "update_user"):
            print(f"{number}. Update user account")
            update_user_option = str(number)
            number += 1
        else:
            update_user_option = None

        if is_authorized(user_data.role, "reset_password"):
            print(f"{number}. Reset user password")
            reset_pw_option = str(number)
            number += 1
        else:
            reset_pw_option = None

        print(f"{number}. Exit user system, go back")
        exit_option = str(number)

        choice = input("Choose an option: ").strip()

        if choice == change_pw_option:
            success = change_own_password(user_data)
            if success:
                sys.exit() 
            else:
                continue  
        elif choice == view_profile_option:
            view_profile(user_data)

        elif choice == create_user_option:
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
            print("Exiting the system. Goodbye!")
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

    for attempt in range(3):
        username = input("Enter username: ").strip().lower()
        if Validation.username_validation(username):
            if get_user_by_username(username):
                print("Username already exists. Please try again.")
                log_instance.log_invalid_input(current_user.username, "username", "Attempt to create duplicate username", False)
            else:
                break
    else:
        print("Too many failed username attempts.")
        return

    password = Validation.get_valid_input(
    prompt="Enter password: ",
    validation_fn=Validation.password_validation,
    username=current_user.username,
    field_name="password"
    )

    allowed_roles = get_permitted_roles(current_user.role)
    # Build a mapping from both names and numbers → role names
    role_lookup = {str(v): k for k, v in allowed_roles.items()}
    role_lookup.update({k.lower(): k for k in allowed_roles})
    
    role_options = [f"{num}: {name}" for name, num in allowed_roles.items()]
    
    for attempt in range(3):
        role = input(f"Enter role ({', '.join(role_options)}): ").strip().lower()
        if role in role_lookup:
            chosen_role = role_lookup[role]
            print(f"Selected role: {chosen_role}")
            break
        else:
            print("Invalid role. Please try again.")
    else:
        print("Too many failed role attempts.")
        return
    
    firstname = Validation.get_valid_input(
        prompt="Enter first name: ",
        validation_fn=Validation.name_validation,
        username=current_user.username,
        field_name="first name"
        )

    lastname = Validation.get_valid_input(
        prompt="Enter last name: ",
        validation_fn=Validation.name_validation,
        username=current_user.username,
        field_name="last name"
        )

    try:
        create_user(username.lower(), firstname, lastname, password, chosen_role)
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
    print("|" + "Creating a new user".center(75) + "|")
    print("----------------------------------------------------------------------------")

    users = list_users()
    if users:
        for user in users:
            print(f"Username: {user.username} | Firstname: {user.firstname} | Lastname: {user.lastname} | Role: {user.role} | Created on: {user.registration_date}")
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

        if user.role == "1":
            deletable.append(user)

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
        return

    print("\nUsers you are authorized to delete:")
    for user in deletable_users:
        print(f"ID: {user.id} | Username: {user.username} | Role: {user.role}")

    try:
        target_id_str = Validation.get_valid_input(
            prompt="\nEnter the ID of the user you want to delete: ",
            validation_fn=Validation.get_valid_id_input,
            username=current_user,
            field_name="id"
        )

        target_id = int(target_id_str)
    except ValueError:
        print("Invalid input: ID must be a number.")
        log_instance.log_invalid_input(current_user.username, "user_id", "Invalid ID input for deletion", True)
        return

    target_user = next((u for u in deletable_users if u.id == target_id), None)
    if not target_user:
        print("You are not allowed to delete this user or user does not exist.")
        return

    confirmation = input(f"Are you sure you want to delete '{target_user.username}'? (yes/no): ").strip().lower()
    if confirmation != "yes":
        print("Cancelled.")
        return

    success = delete_user_by_id(target_id)
    if success:
        print(f" User '{target_user.username}' deleted successfully.")
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

    # Show all users that can be edited by the current user
    editable_users = get_editable_users(current_user)
    if not editable_users:
        print("No users available to update.")
        return

    for user in editable_users:
        print(f"ID: {user.id} | Username: {user.username} | Firstname: {user.firstname} | Lastname: {user.lastname} Role: {user.role}")

    try:
        target_id = int(input("\nEnter the ID of the user to update: ").strip())
    except ValueError:
        print("Invalid ID.")
        return

    target_user = next((u for u in editable_users if u.id == target_id), None)
    if not target_user:
        print("User not found or not editable by your role.")
        return

    print("\nWhich field do you want to update?")
    print("1. Username")
    print("2. First Name")
    print("3. Last Name")
    print("0. Cancel")

    choice = input("Choose an option: ").strip()

    if choice == '1':
        new_username = input("Enter new username: ").strip().lower()
        if not Validation.username_validation(new_username):
            print("Invalid username format.")
            return
        if get_user_by_username(new_username):
            print("Username already exists. Please choose another.")
            return
        update_data = {"username": new_username}

    elif choice == '2':
        new_first = input("Enter new first name: ").strip().title()
        if not Validation.name_validation(new_first, current_user.username):
            print("Invalid first name.")
            return
        update_data = {"firstname": new_first}

    elif choice == '3':
        new_last = input("Enter new last name: ").strip().title()
        if not Validation.name_validation(new_last, current_user.username):
            print("Invalid last name.")
            return
        update_data = {"lastname": new_last}

    elif choice == '0':
        print("Cancelled.")
        return
    else:
        print("Invalid choice.")
        return

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

    # Eerst: 3 pogingen voor huidig wachtwoord
    for attempt in range(3):
        old_password = input("Enter your current password: ").strip()
        if validate_password(old_password, stored_hash):
            break  # correct → ga door
        else:
            print("Incorrect current password.")
            log_instance.log_invalid_input(current_user.username, "password", "Incorrect current password")

    else:
        print("Too many incorrect current password attempts. You are now logged out.")
        log_instance.addlog(current_user.username, "Password change failed", "Too many old password attempts", True)
        return False

    # Daarna: 3 pogingen voor nieuw wachtwoord (via helper)
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
        sys.exit()
        return True
    else:
        log_instance.addlog(current_user.username, "Password change failed", "Database error", True)
        print("Password change failed. You are now logged out.")
        return False
    
#TODO: Check for the required role permissions before allowing password reset
def reset_user_password(current_user):
    print("\n--- Reset User Password ---")

    editable_users = get_editable_users(current_user)
    if not editable_users:
        print("No users available for password reset.")
        return

    for user in editable_users:
        print(f"ID: {user.id} | Username: {user.username} | Role: {user.role}")

    try:
        target_id = int(input("\nEnter the ID of the user to reset password: ").strip())
    except ValueError:
        print("Invalid ID.")
        return

    target_user = next((u for u in editable_users if u.id == target_id), None)
    if not target_user:
        print("User not found or not editable by your role.")
        return

    # Nieuw wachtwoord vragen en valideren
    new_pw = Validation.get_valid_input(
        "Enter new temporary password: ",
        Validation.password_validation,
        current_user.username,
        "password"
        )

    success = update_password_by_id(target_id, new_pw)

    if success:
        print("Password reset successfully.")
        log_instance.addlog(current_user.username, "Password reset", f"Target: {target_user.username}", False)
    else:
        print("Password reset failed.")
        log_instance.addlog(current_user.username, "Password reset failed", f"Target: {target_user.username}", False)
