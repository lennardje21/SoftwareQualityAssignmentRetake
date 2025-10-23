import sys
from controllers.backup_controller import backup_management_menu
from controllers.user_controller import user_menu, change_own_password, view_profile, show_all_users
from controllers.traveller_controller import traveller_menu
from controllers.scooter_controller import scooter_menu
from logs.log import LogFunction
from controllers.rolecheck import is_authorized, require_authorization
from security.backup import BackupManager
from helpers.general_methods import general_methods
import time

def service_engineer_menu(user_data):
    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Service Engineer Menu".center(75) + "|")
    print("----------------------------------------------------------------------------")
    print("[1] Change Password")
    print("[2] View Profile")
    print("[3] Manage Scooters")
    print("[4] Logout")
    print("[0] Exit")
    print("----------------------------------------------------------------------------")

    choice = input("Choose an option: ").strip()
    general_methods.clear_console()

    if choice == '1':
        if is_authorized(user_data.role, "update_own_password"):
            success = change_own_password(user_data)
            if success:
                return False
        else:
            print("You are not authorized to perform this action.")
            time.sleep(0.5)
    elif choice == '2':
        view_profile(user_data)
    elif choice == '3':
        if any(is_authorized(user_data.role, p) for p in ['search_scooter', 'update_scooter']):
            scooter_menu(user_data)
        else:
            print("You are not authorized to perform this action.")
            time.sleep(0.5)
    elif choice == '4':
        print("Logging out...")
        time.sleep(0.5)
        return False
    elif choice == '0':
        print("Exiting the system. Goodbye!")
        time.sleep(0.5)
        sys.exit()
    else:
        print("Invalid choice. Please try again.")
        time.sleep(0.5)

    return True

def system_administrator_menu(user_data):
    logger = LogFunction()

    if logger.check_for_suspicious_logs(user_data):
        require_authorization(user_data, 'view_logs')
        logger.show_suspicious_logs(user_data)

    general_methods.clear_console()
    
    print("----------------------------------------------------------------------------")
    print("|" + "System Admin Menu".center(75) + "|")
    print("----------------------------------------------------------------------------")
    print("[1] Change Password")
    print("[2] View Profile")
    print("[3] Traveller Management")
    print("[4] Scooter Management")
    print("[5] User Management")
    print("[6] View Logs")
    print("[7] Backup Management")
    print("[10] Logout")
    print("[0] Exit")
    print("----------------------------------------------------------------------------")

    choice = input("Choose an option: ").strip()
    general_methods.clear_console()

    if choice == '1':
        log_out = change_own_password(user_data)
        if log_out:
            return False
    elif choice == '2':
        view_profile(user_data)
    elif choice == '3':
        traveller_menu(user_data)
    elif choice == '4':
        scooter_menu(user_data)
    elif choice == '5':
        user_menu(user_data)
    elif choice == '6':
        require_authorization(user_data, 'view_logs')
        logger = LogFunction()
        logger.show_logs(user_data)
    elif choice == '7':  # or whichever number backup was
        backup_management_menu(user_data)

    elif choice == '10':
        print("Logging out...")
        time.sleep(0.5)
        return False
    elif choice == '0':
        print("Exiting the system. Goodbye!")
        time.sleep(0.5)
        return sys.exit()
    else:
        general_methods.clear_console()
        print("Invalid choice. Please try again.")
        time.sleep(0.5)
    return True

def super_administrator_menu(user_data):
    logger = LogFunction()

    if logger.check_for_suspicious_logs(user_data):
        require_authorization(user_data, 'view_logs')
        logger.show_suspicious_logs(user_data)

    general_methods.clear_console()

    print("----------------------------------------------------------------------------")
    print("|" + "Super Admin Menu".center(75) + "|")
    print("----------------------------------------------------------------------------")
    print("[1] View Profile")
    print("[2] Traveller Management")
    print("[3] Scooter Management")
    print("[4] User Management")
    print("[5] View Logs")
    print("[6] Backup Management")
    print("[10] Logout")
    print("[0] Exit")
    print("----------------------------------------------------------------------------")
    choice = input("Choose an option: ").strip()
    general_methods.clear_console()

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
        backup_management_menu(user_data)
    elif choice == '10':        
        print("Logging out...")
        time.sleep(0.5)
        return False
    elif choice == '0':
        print("Exiting the system. Goodbye!")
        time.sleep(0.5)
        sys.exit()
    else:
        print("Invalid choice. Please try again.")
        time.sleep(0.5)

    return True