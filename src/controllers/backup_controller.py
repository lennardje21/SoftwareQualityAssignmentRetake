# controllers/backup_controller.py

import os
import time
import sys
from security.backup import BackupManager
from security.restore_codes_store import RestoreCodeStore
from controllers.rolecheck import is_authorized, require_authorization
from logs.log import log_instance
from helpers.general_methods import general_methods
from security.validation import Validation
from security.encryption import load_symmetric_key, decrypt_message

def backup_management_menu(user_data):
    """Entry menu for backup management. Role determines which options are shown."""
    while True:
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + "Backup Management".center(75) + "|")
        print("----------------------------------------------------------------------------")

        # SYSTEM ADMIN Menu
        if user_data.role == "system_administrator":
            print("[1] Create Backup")
            print("[2] Restore Backup via Code")
            print("[0] Back")
            print("----------------------------------------------------------------------------")
            choice = input("Choose an option: ").strip()

            if choice == '1':
                BackupManager.create_backup(user_data)
            elif choice == '2':
                BackupManager.system_administrator_restore_backup(user_data)
            elif choice == '0':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)

        # SUPER ADMIN Menu
        else:
            print("[1] Create Backup")
            print("[2] Restore Backup (Full Restore)")
            print("[3] View Active Restore Codes")
            print("[4] Generate Restore Code")
            print("[5] Revoke Restore Code")
            print("[0] Back")
            print("----------------------------------------------------------------------------")
            choice = input("Choose an option: ").strip()

            if choice == '1':
                require_authorization(user_data, 'create_backup')
                BackupManager.create_backup(user_data)
            elif choice == '2':
                require_authorization(user_data, 'super_admin_restore_backup')
                BackupManager.super_admin_restore_backup(user_data)
            elif choice == '3':
                _view_codes(user_data)
            elif choice == '4':
                require_authorization(user_data, 'generate_restore_code')
                BackupManager.link_backup_restore_code(user_data)
            elif choice == '5':
                require_authorization(user_data, 'revoke_restore_code')
                BackupManager.revoke_restore_code_by_super_admin(user_data)
            elif choice == '0':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)


def _view_codes(user_data):
    """
    Displays all active restore codes for super admin viewing.

    Args:
        user_data: The user data object representing the current user. Must be a super admin.
    """
    store = RestoreCodeStore()
    codes = store.list_all_decrypted()
    general_methods.clear_console()
    
    print("----------------------------------------------------------------------------")
    print("|" + "Restore codes".center(75) + "|")
    print("----------------------------------------------------------------------------")

    if not codes:
        print("No active restore codes.")
        general_methods.hidden_input("Press Enter to return...")
        return

    for i, c in enumerate(codes, 1):
        print(f"{i}) Code: {c['code']} | Admin ID: {c['admin_id']} | Backup: {c['backup_filename']} | Created: {c['created_at']}")

    general_methods.hidden_input("\nPress Enter to return...")
