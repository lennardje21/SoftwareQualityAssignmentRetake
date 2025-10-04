import sys
from controllers.user_controller import user_menu, change_own_password, view_profile, show_all_users
from controllers.traveller_controller import traveller_menu
from controllers.scooter_controller import scooter_menu
from logs.log import LogFunction
from controllers.rolecheck import is_authorized, require_authorization
from security.backup import BackupManager


def service_engineer_menu(user_data):
    while True:
        print("\n--- Service Engineer Menu ---")
        options = {}

        number = 1

        # Can change own password
        if is_authorized(user_data.role, "update_own_password"):
            print(f"{number}. Change Password")
            options[str(number)] = lambda: change_own_password(user_data)
            number += 1

        print(f"{number}. View Profile")
        options[str(number)] = lambda: view_profile(user_data)
        number += 1

        # Only show traveller management options if the user is authorized
        if any(is_authorized(user_data.role, p) for p in ['search_scooter', 'update_scooter']):
            print(f"{number}. Manage Scooters")
            options[str(number)] = lambda: scooter_menu(user_data)
            number += 1

        print(f"{number}. Logout")
        logout_option = str(number)
        number += 1

        print(f"{number}. Exit")
        exit_option = str(number)

        choice = input("Choose an option: ").strip()

        if choice in options:
            options[choice]()  # Call the corresponding function
        elif choice == logout_option:
            print("Logging out...")
            return False
        elif choice == exit_option:
            print("Exiting the system. Goodbye!")
            sys.exit()
        else:
            print("Invalid choice. Please try again.")

def system_administrator_menu(user_data):
    logger = LogFunction()

    if logger.check_for_suspicious_logs(user_data):
        require_authorization(user_data.role, 'view_logs')
        logger.show_suspicious_logs(user_data)

    """Display the system administrator menu."""
    print("\n--- System Administrator Menu ---")
    print("1. Change Password")
    print("2. View Profile")
    print("3. Traveller Management")
    print("4. Scooter Management")
    print("5. List All Users")
    print("6. User Management")
    print("7. Logout")
    print("8. Exit")
    print("9. View Logs")
    print("10. Create backup")
    print("99. Restore backup using restore code")

    choice = input("Choose an option: ").strip()
    if choice == '1':
        change_own_password(user_data)
    elif choice == '2':
        view_profile(user_data)
    elif choice == '3':
        traveller_menu(user_data)
    elif choice == '4':
        scooter_menu(user_data)
    elif choice == '5':
        show_all_users(user_data)
    elif choice == '6':
        user_menu(user_data)
    elif choice == '7':
        print("Logging out...")
        return False
    elif choice == '8':
        print("Exiting the system. Goodbye!")
        return sys.exit()
    elif choice == '9':
        require_authorization(user_data, 'view_logs')
        logger = LogFunction()
        logger.show_logs(user_data)
    elif choice == '10':
        BackupManager.create_backup(user_data)
    elif choice == '99':
        BackupManager.system_administrator_restore_backup(user_data)
    else:
        print("Invalid choice. Please try again.")
    return True

def super_administrator_menu(user_data):
    logger = LogFunction()

    if logger.check_for_suspicious_logs(user_data):
        require_authorization(user_data, 'view_logs')
        logger.show_suspicious_logs(user_data)

    print("\n--- Super Administrator Menu ---")
    print("1. View Profile")
    print("2. Traveller Management")
    print("3. Scooter Management")
    print("4. User Management")
    print("5. View Logs")
    print("6. Logout")
    print("7. Exit")
    print("8. Create Backup")
    print("9. Restore Backup")
    print("10. Create Restore Code")
    print("11. Revoke Restore Code")

    choice = input("Choose an option: ").strip()

    if choice == '1':
        view_profile(user_data)
    elif choice == '2':
        traveller_menu(user_data)
    elif choice == '3':
        scooter_menu(user_data)
    elif choice == '4':
        user_menu(user_data)
    elif choice == '5':
        require_authorization(user_data, 'view_logs')
        logger.show_logs(user_data)
    elif choice == '6':
        print("Logging out...")
        return False
    elif choice == '7':
        print("Exiting the system. Goodbye!")
        sys.exit()
    elif choice == '8':
        require_authorization(user_data, 'create_backup')
        BackupManager.create_backup(user_data)
    elif choice == '9':
        require_authorization(user_data, 'super_admin_restore_backup')
        BackupManager.super_admin_restore_backup(user_data)
    elif choice == '10':
        require_authorization(user_data, 'generate_restore_code')
        BackupManager.link_backup_restore_code(user_data)
    elif choice == '11':
        require_authorization(user_data, 'revoke_restore_code')
        BackupManager.revoke_restore_code_by_super_admin(user_data)
    else:
        print("Invalid choice. Please try again.")
    
    return True