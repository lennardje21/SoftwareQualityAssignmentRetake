# Standard library imports
import os
import sys
import shutil
import sqlite3
import random
import string
import zipfile
from datetime import datetime
import re

# Local application imports
from controllers.rolecheck import is_authorized
from helpers.general_methods import general_methods
from logs.log import log_instance
from models.db import open_connection
from security.encryption import load_symmetric_key, encrypt_message, decrypt_message
from security.validation import Validation


# --- Helper functions for safe SQL identifier handling ---
def is_safe_identifier(name: str) -> bool:
    """Allow only simple SQLite identifiers (letters, digits, underscore),
    starting with a letter or underscore, and not a system table."""
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)) and not name.startswith("sqlite_")


def quote_ident(name: str) -> str:
    """Quote an SQL identifier safely for SQLite by doubling internal quotes."""
    return '"' + name.replace('"', '""') + '"'


class BackupManager:
    """Class to manage backup operations for the Urban Mobility database."""

    def __init__(self):
        """Initialize the BackupManager."""
        pass

    @staticmethod
    def get_paths():
        """Helper to get common paths."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'data', 'urban_mobility.db')
        backup_dir = os.path.join(base_dir, 'backups')
        return base_dir, db_path, backup_dir
    
    @staticmethod
    def extract_db_from_zip(zip_path, target_path, current_user=None):
        """Extract database from zip file."""

        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                db_file_in_zip = next((f for f in zipf.namelist() if f.endswith('.db')), None)
                
                if not db_file_in_zip:
                    error_msg = "No database file found in the backup archive"
                    print(f"Error: {error_msg}")
                    if current_user:
                        log_instance.addlog(current_user.username, "Restore backup failed", error_msg, True)
                    return False
                
                with zipf.open(db_file_in_zip) as source_file:
                    with open(target_path, 'wb') as target_file:
                        shutil.copyfileobj(source_file, target_file)
            return True
        except Exception as e:
            error_msg = f"Error extracting database: {e}"
            print(error_msg)
            if current_user:
                log_instance.addlog(current_user.username, "Restore backup failed", error_msg, True)
            return False

    def create_backup(current_user):
        """Create a backup of the database."""

        if not is_authorized(current_user.role, 'create_backup'):
                print("You do not have permission to create backups.")
                return

        base_dir, db_path, backup_dir = BackupManager.get_paths()

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # create a zip file which contains the database file
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_name = f"urban_mobility_backup_{timestamp}"
        zip_path = os.path.join(backup_dir, f"{backup_name}.zip")
        
        try:
            # Check if the database file exists
            if not os.path.exists(db_path):
                print(f"Error: Database file not found at {db_path}")
                log_instance.addlog(current_user.username, "Create backup failed", f"Database file not found at {db_path}", True)
                return False

            # Create a zip file containing the database
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add the database to the zip, but use only the filename in the zip
                zipf.write(db_path, os.path.basename(db_path))
            
            print(f"Backup created successfully as {backup_name}")
            log_instance.addlog(current_user.username, "Create backup", f"Backup {backup_name} created", False)
            general_methods.hidden_input("\nPress Enter to return to the user menu...")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            log_instance.addlog(current_user.username, "Create backup failed", f"Error: {str(e)}", True)
            general_methods.hidden_input("\nPress Enter to return to the user menu...")
            return False

    def generate_unique_restore_code():
        """Generate a unique restore code."""

        # Generate a random code of 8 characters (letters and digits)
        code_length = 8
        characters = string.ascii_letters + string.digits
        restore_code = ''.join(random.choice(characters) for _ in range(code_length))

        return restore_code


    @staticmethod
    def link_backup_restore_code(current_user):
        """Super admin: link a restore code to a system admin and a specific backup (stored outside the DB)."""
        from security.restore_codes_store import RestoreCodeStore

        if not is_authorized(current_user.role, 'link_backup_restore_code'):
            print("You do not have permission to generate backup restore codes.")
            return

        key = load_symmetric_key()
        base_dir, db_path, backup_dir = BackupManager.get_paths()

        # List system admins
        conn = open_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users")
            all_users = cursor.fetchall()
        finally:
            conn.close()

        system_admins = []
        for user in all_users:
            try:
                decrypted_role = decrypt_message(user[2], key)
                if decrypted_role == "system_administrator":
                    decrypted_username = decrypt_message(user[1], key)
                    system_admins.append((user[0], decrypted_username))
            except Exception:
                continue

        if not system_admins:
            print("No system admins found.")
            return

        print("These are the current admins in the system:")
        for admin in system_admins:
            print(f"{admin[0]}. {admin[1]}")

        # Select admin
        admin_found = False

        while not admin_found:
            admin_id = int(Validation.get_valid_input(
                "\nEnter the ID of the system administrator: ",
                lambda id, username: Validation.get_valid_id_input(id, username),
                current_user.username,
                "admin id"
            ))

            for admin in system_admins:
                if admin[0] == admin_id:
                    selected_admin_id = admin_id
                    selected_admin_name = admin[1]
                    admin_found = True
                    break

            if not admin_found:
                print(f"No system administrator found with ID {admin_id}.")
                log_instance.log_invalid_input(current_user.username, "admin selection", f"Invalid admin ID: {admin_id}")

        # Show available backups
        if not os.path.exists(backup_dir):
            print("Backup directory not found.")
            return

        backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
        if not backups:
            print("No backup files found.")
            return

        print("\n=== Available Backups ===")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup}")

        # Select backup
        backup_found = False

        while not backup_found:
            backup_choice = Validation.get_valid_input(
                "\nEnter the number of the backup you wish to link (or 'cancel' to stop): ",
                Validation.get_valid_id_input,
                current_user.username,
                "backup selection"
            )
            if backup_choice is None:
                print("Operation cancelled.")
                return

            backup_index = int(backup_choice) - 1
            if 0 <= backup_index < len(backups):
                selected_backup = backups[backup_index]
                backup_found = True
            else:
                print(f"Invalid backup selection. Please choose a number between 1 and {len(backups)}.")
                log_instance.log_invalid_input(current_user.username, "backup selection",
                                            f"Invalid backup index: {backup_index + 1}")

        # Generate code and store OUTSIDE DB
        restore_code = BackupManager.generate_unique_restore_code()
        RestoreCodeStore().add_code(selected_admin_id, selected_backup, restore_code)

        print(f"\nBackup restore code generated successfully: {restore_code}")
        print(f"This code has been linked to administrator: {selected_admin_name}")
        print(f"For backup file: {selected_backup}")
        print("\nIMPORTANT: Share this code securely with the administrator.")
        general_methods.hidden_input("\nPress Enter to return to the user menu...")

        log_instance.addlog(
            current_user.username,
            "Generated restore code",
            f"Code linked to admin ID {selected_admin_id} for backup {selected_backup}",
            False
        )


    @staticmethod
    def system_administrator_restore_backup(current_user):
        """Restore using a restore code linked to this System Admin (codes stored outside DB)."""
        from security.restore_codes_store import RestoreCodeStore

        if not is_authorized(current_user.role, 'system_administrator_restore_backup'):
            print("You do not have permission to restore backups.")
            general_methods.hidden_input("\nPress Enter to return to the backup menu...")
            return

        # Verify there is a code for this admin
        if not BackupManager.check_for_restore_code(current_user):
            print("No restore code linked to your account. Please contact a super administrator.")
            general_methods.hidden_input("\nPress Enter to return to the backup menu...")
            return
        
        MAX_RESTORE_CODE_ATTEMPTS = 3
        attempts = 0
        store = RestoreCodeStore()
        base_dir, db_path, backup_dir = BackupManager.get_paths()

        matching_index = None
        backup_filename = None
        general_methods.clear_console()
        print("----------------------------------------------------------------------------")
        print("|" + "Restore Backup".center(75) + "|")
        print("----------------------------------------------------------------------------")

        while attempts < MAX_RESTORE_CODE_ATTEMPTS:
            code_input = Validation.get_valid_input(
                "\nEnter your restore code (or 'cancel' to stop): ",
                Validation.restore_code_validation,
                current_user.username,
                "restore code"
            )
            if code_input is None:
                print("Backup restoration cancelled.")
                general_methods.hidden_input("\nPress Enter to return to the backup menu...")
                return

            match = store.find_matching_code(code_input, current_user.id)
            if match:
                matching_index, rec = match
                # decrypt backup filename
                backup_filename = decrypt_message(rec["backup_filename"], store.key)
                break

            attempts += 1
            print("Invalid restore code.")
            log_instance.log_invalid_input(current_user.username, "system administrator restore backup",
                                        f"Invalid restore code: {code_input}")
            if attempts >= MAX_RESTORE_CODE_ATTEMPTS:
                print("Too many failed attempts to enter a valid restore code.")
                log_instance.addlog(current_user.username, "system administrator restore backup",
                                    f"Multiple failed restore code attempts ({attempts})", True)
                print("For security reasons, you have been logged out.")
                sys.exit(1)


        # Proceed with restoring the backup
        backup_path = os.path.join(base_dir, 'backups', backup_filename)
        if not os.path.exists(backup_path):
            print(f"Backup file {backup_filename} does not exist at {backup_path}")
            log_instance.addlog(current_user.username, "Restore backup failed",
                                f"Backup file not found: {backup_filename}", True)
            return

        # Confirm
        print("\nIMPORTANT: After restoring the backup, you will be logged out automatically for security reasons.")
        print("You will need to log in again after the restore process is complete.")

        while True:
            confirm_choice = Validation.get_valid_input(
                "WARNING: This will replace all data (except logs & restore codes). Continue? (yes/no): ",
                Validation.yes_no_validation,
                current_user.username,
                "confirmation"
            )
            if confirm_choice is None or confirm_choice.lower() == 'no':
                print("Backup restoration cancelled.")
                return False
            if confirm_choice.lower() == 'yes':
                break

        # Restore (table-safe) and consume the code
        if BackupManager.restore_database_from_backup(backup_path, current_user):
            store.consume_code_by_index(matching_index)
            print("\nYou are now being logged out for security reasons.")
            print("Please restart the application and log in again.")
            sys.exit(0)
        else:
            print("\nRestore failed.")
            return False


    @staticmethod
    def check_for_restore_code(current_user):
        """Check if the current user has a restore code linked to their account (stored outside DB)."""
        from security.restore_codes_store import RestoreCodeStore

        if not is_authorized(current_user.role, 'check_for_restore_code'):
            print("You do not have permission to check for restore codes.")
            return False

        return RestoreCodeStore().has_code_for_admin(current_user.id)


    @staticmethod
    def revoke_restore_code_by_super_admin(current_user):
        """Super admin: revoke a restore code stored outside DB."""
        from security.restore_codes_store import RestoreCodeStore

        if not is_authorized(current_user.role, 'revoke_restore_code'):
            print("You do not have permission to revoke restore codes.")
            return

        # Build admin name lookup for display (from users table)
        key = load_symmetric_key()
        conn = open_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users")
            all_users = cursor.fetchall()
        finally:
            conn.close()

        admin_usernames = {}
        for user_id, username_encrypted in all_users:
            try:
                admin_usernames[user_id] = decrypt_message(username_encrypted, key)
            except Exception:
                admin_usernames[user_id] = f"User ID {user_id}"

        # Load codes (decrypted for display)
        store = RestoreCodeStore()
        codes = store.list_all_decrypted()
        if not codes:
            print("No restore codes found.")
            return

        print("\n=== Active Restore Codes ===")
        for i, c in enumerate(codes, 1):
            admin_name = admin_usernames.get(c["admin_id"], f"Unknown Admin (ID: {c['admin_id']})")
            print(f"{i}. Code: {c['code']} - Admin: {admin_name} - Backup: {c['backup_filename']} - Created: {c['created_at']}")

        # Select which to revoke
        index = None

        while True:
            choice = Validation.get_valid_input(
                "\nEnter the number of the code to revoke (or 'cancel' to stop): ",
                Validation.get_valid_id_input,
                current_user.username,
                "restore code selection"
            )
            if choice is None:
                print("Operation cancelled.")
                return

            idx = int(choice) - 1
            if 0 <= idx < len(codes):
                index = idx
                break
            else:
                print(f"Please enter a number between 1 and {len(codes)}.")
                log_instance.log_invalid_input(current_user.username, "restore code selection",
                                            f"Invalid code index: {idx + 1}")

        # Confirm revocation
        while True:
            confirm = Validation.get_valid_input(
                f"Are you sure you want to revoke the restore code {codes[index]['code']}? (yes/no): ",
                Validation.yes_no_validation,
                current_user.username,
                "confirmation"
            )
            if confirm is None or confirm.lower() == 'no':
                print("Operation cancelled.")
                return
            if confirm.lower() == 'yes':
                break

        # Revoke
        store.consume_code_by_index(index)
        print("Restore code successfully revoked.")
        log_instance.addlog(
            current_user.username,
            "Revoked restore code",
            f"Revoked code {codes[index]['code']} from admin ID {codes[index]['admin_id']}",
            False
        )


    def super_admin_restore_backup(current_user):
        """Restore the database from a previous backup."""

        if not is_authorized(current_user.role, 'super_admin_restore_backup'):
                print("You do not have permission to restore backups.")
                return

        base_dir, db_path, backup_dir = BackupManager.get_paths()

        # Check if the backup directory exists
        if not os.path.exists(backup_dir):
            print("Backup directory not found.")
            return False

        # Search for the latest backup in the backups directory
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
        if not backups:
            print("No backups found.")
            return False

        # Sort backups by date (newest first)
        backups.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)

        print("\n=== Available Backups ===")
        for i, backup in enumerate(backups, 1):
            # Fetch the date of the file
            backup_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, backup)))
            backup_time_str = backup_time.strftime('%Y-%m-%d %H:%M:%S')
            backup_size = os.path.getsize(os.path.join(backup_dir, backup)) / 1024  # Size in KB
            
            print(f"{i}. {backup} (Created: {backup_time_str}, Size: {backup_size:.1f} KB)")

        # Ask user for choice
        backup_selection_valid = False
        selected_backup = None

        while not backup_selection_valid:
            choice = Validation.get_valid_input(
                "\nEnter the number of the backup you want to restore (or 'cancel' to stop): ",
                Validation.get_valid_id_input,
                current_user.username,
                "backup selection"
            )
            
            if choice is None:
                print("Backup restoration cancelled.")
                return False
            
            choice_index = int(choice) - 1
            
            if 0 <= choice_index < len(backups):
                selected_backup = backups[choice_index]
                backup_selection_valid = True
            else:
                print(f"Please enter a number between 1 and {len(backups)}.")
                log_instance.log_invalid_input(current_user.username, "backup selection", 
                                            f"Invalid backup index: {choice_index + 1}")
                
        
        selected_backup_path = os.path.join(backup_dir, selected_backup)

        # Confirm destructive operation (consistency with System Admin flow)
        print("\nIMPORTANT: After restoring the backup, you will be logged out automatically for security reasons.")
        print("You will need to log in again after the restore process is complete.")

        while True:
            confirm = Validation.get_valid_input(
                "WARNING: This will replace all data (except logs & restore codes). Continue? (yes/no): ",
                Validation.yes_no_validation,
                current_user.username,
                "confirmation"
            )
            if confirm is None or confirm.lower() == 'no':
                print("Backup restoration cancelled.")
                return False
            if confirm.lower() == 'yes':
                break

        try:
            # Use the table-safe restore (logs & restore codes preserved)
            if BackupManager.restore_database_from_backup(selected_backup_path, current_user):
                print(f"\nDatabase successfully restored from {selected_backup}")
                print("\nYou are now being logged out for security reasons.")
                print("Please restart the application and log in again.")
                sys.exit(0)
            else:
                print("\nRestore failed.")
                return False
        except Exception as e:
            print(f"Error restoring backup: {e}")
            log_instance.addlog(current_user.username, "Super admin restore backup failed", f"Error: {str(e)}", True)
            return False

        
    @staticmethod
    def restore_database_from_backup(backup_path, current_user):
        """
        Restore database tables from a backup, excluding logs and system tables (those starting with 'sqlite_').
        Also logs the restore event afterwards.
        """
        base_dir, db_path, backup_dir = BackupManager.get_paths()
        temp_db = os.path.join(base_dir, 'data', 'temp_restore.db')

        # STEP 1: Extract backup → temp DB
        if backup_path.endswith('.zip'):
            if not BackupManager.extract_db_from_zip(backup_path, temp_db, current_user):
                return False
        else:
            shutil.copy2(backup_path, temp_db)

        # STEP 2: Open current & backup DB
        conn_current = open_connection()
        conn_backup = sqlite3.connect(temp_db)
        
        try:
            cur_current = conn_current.cursor()
            cur_backup = conn_backup.cursor()

            # STEP 3: Copy tables except logs (and system tables)
            tables_to_skip = {"logs"}

            cur_backup.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur_backup.fetchall()]

            for table in tables:
                # Validate identifier and skip disallowed/system tables
                if not is_safe_identifier(table) or table in tables_to_skip:
                    continue

                # Use the validated identifier directly (no quoting needed)
                qname = table

                # wipe current table
                cur_current.execute(f'DELETE FROM {qname}')

                # restore data
                cur_backup.execute(f'SELECT * FROM {qname}')
                rows = cur_backup.fetchall()
                if rows:
                    placeholders = ", ".join("?" * len(rows[0]))
                    cur_current.executemany(
                        f'INSERT INTO {qname} VALUES ({placeholders})',
                        rows
                    )

            # STEP 4: Commit
            conn_current.commit()
        finally:
            # STEP 5: Close connections
            conn_backup.close()
            conn_current.close()

        # STEP 6: Cleanup
        os.remove(temp_db)

        # STEP 7: Log the restore event
        from logs.log import log_instance
        log_instance.addlog(
            current_user.username,
            "Restore backup",
            f"System restored using backup: {os.path.basename(backup_path)}",
            False
        )

        return True


backup_instance = BackupManager()