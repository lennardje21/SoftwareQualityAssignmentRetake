class BackupManager:
    """Class to manage backup operations for the Urban Mobility database."""

    def __init__(self):
        """Initialize the BackupManager."""
        pass

    @staticmethod
    def get_paths():
        import os

        """Helper to get common paths."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'data', 'urban_mobility.db')
        backup_dir = os.path.join(base_dir, 'backups')
        return base_dir, db_path, backup_dir
    
    @staticmethod
    def extract_db_from_zip(zip_path, target_path, current_user=None):
        """Extract database from zip file."""
        import zipfile
        import shutil
        from logs.log import log_instance

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
        import os
        import zipfile
        from datetime import datetime
        from controllers.rolecheck import is_authorized
        from logs.log import log_instance

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
            
            print(f"Backup created successfully as ZIP archive at {zip_path}")
            log_instance.addlog(current_user.username, "Create backup", f"Backup created at {zip_path}", False)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            log_instance.addlog(current_user.username, "Create backup failed", f"Error: {str(e)}", True)
            return False

    def generate_unique_restore_code():
        """Generate a unique restore code."""
        import random
        import string

        # Generate a random code of 8 characters (letters and digits)
        code_length = 8
        characters = string.ascii_letters + string.digits
        restore_code = ''.join(random.choice(characters) for _ in range(code_length))

        return restore_code
    
    def link_backup_restore_code(current_user):
        """Function to link a backup restore code to a system admin.
        This function is intended to be used by a super administrator.
        It allows the super admin to select a system admin and generate a unique restore code for them"""

        from controllers.rolecheck import is_authorized
        import sqlite3
        import os
        from security.encryption import load_symmetric_key, encrypt_message, decrypt_message
        from logs.log import log_instance
        from security.validation import Validation
        import sys

        if not is_authorized(current_user.role, 'link_backup_restore_code'):
            print("You do not have permission to generate backup restore codes.")
            return
        
        key = load_symmetric_key()
        base_dir, db_path, backup_dir = BackupManager.get_paths()

        # Show a list of system admins to choose from
        conn = sqlite3.connect('data/urban_mobility.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        all_users = cursor.fetchall()
        conn.close()

        # Filter system admins after decryption
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

        # Get user selection for admin
        admin_found = False
        invalid_admin_attempts = 0
        MAX_INVALID_ADMIN_ATTEMPTS = 3

        while not admin_found:
            admin_id = int(Validation.get_valid_input(
                "\nEnter the ID of the system administrator: ",
                lambda id, username: Validation.get_valid_id_input(id, username),
                current_user.username,
                "admin id"
            ))

            # Check if this ID exists in the system_admins list
            for admin in system_admins:
                if admin[0] == admin_id:
                    selected_admin_id = admin_id
                    selected_admin_name = admin[1]
                    admin_found = True
                    break
                    
            if not admin_found:
                invalid_admin_attempts += 1
                print(f"No system administrator found with ID {admin_id}.")
                log_instance.log_invalid_input(current_user.username, "admin selection", f"Invalid admin ID: {admin_id}")
                
                if invalid_admin_attempts >= MAX_INVALID_ADMIN_ATTEMPTS:
                    print("Too many failed attempts to select a valid administrator.")
                    log_instance.addlog(current_user.username, "Backup restore ID input", 
                                    f"Multiple failed admin ID selection attempts ({invalid_admin_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
        
        # Show available backups
        backup_dir = os.path.join(base_dir, 'backups')
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

        
        # Get user selection for backup file
        backup_found = False
        invalid_backup_attempts = 0
        MAX_INVALID_BACKUP_ATTEMPTS = 3

        while not backup_found:
            backup_choice = input("\nEnter the number of the backup you wish to restore: ")
            try:
                backup_index = int(backup_choice) - 1
                if backup_index in range(len(backups)):
                    selected_backup = backups[backup_index]
                    backup_found = True
                else:
                    invalid_backup_attempts += 1
                    print(f"Invalid backup selection. Please choose a number between 1 and {len(backups)}.")
                    log_instance.log_invalid_input(current_user.username, "backup selection", f"Invalid backup index: {backup_index + 1}")
                    
                    if invalid_backup_attempts >= MAX_INVALID_BACKUP_ATTEMPTS:
                        print("Too many failed attempts to select a valid backup file.")
                        log_instance.addlog(current_user.username, "Backup restore file selection", 
                                        f"Multiple failed backup selection attempts ({invalid_backup_attempts})", True)
                        print("For security reasons, you have been logged out.")
                        sys.exit(1)
            except ValueError:
                invalid_backup_attempts += 1
                print("Please enter a valid number.")
                log_instance.log_invalid_input(current_user.username, "backup selection", f"Invalid backup selection input: {backup_choice}")
                
                if invalid_backup_attempts >= MAX_INVALID_BACKUP_ATTEMPTS:
                    print("Too many failed attempts to select a valid backup file.")
                    log_instance.addlog(current_user.username, "Backup restore file selection", 
                                    f"Multiple failed backup selection attempts ({invalid_backup_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)

        # Generate a unique restore code
        restore_code = BackupManager.generate_unique_restore_code()

        # Encrypt the data before storing
        encrypted_code = encrypt_message(restore_code, key)
        selected_backup = backups[backup_index]  # fetch the selected backup file name
        encrypted_backup_filename = encrypt_message(selected_backup, key)
        encrypted_admin_id = encrypt_message(str(selected_admin_id), key)

        # Store the encrypted restore code in the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO restore_codes (code, system_admin_id, backup_filename) VALUES (?, ?, ?)",
                        (encrypted_code, encrypted_admin_id, encrypted_backup_filename))
            conn.commit()
            
            print(f"\nBackup restore code generated successfully: {restore_code}")
            print(f"This code has been linked to administrator: {selected_admin_name}")
            print(f"For backup file: {selected_backup}")
            print("\nIMPORTANT: Share this code securely with the administrator.")
            
            log_instance.addlog(
                current_user.username, 
                "Generated restore code", 
                f"Code linked to admin ID {selected_admin_id} for backup {selected_backup}", 
                False
            )
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            log_instance.addlog(current_user.username, "Generate restore code failed", f"Error: {str(e)}", True)
        finally:
            conn.close()


    def system_administrator_restore_backup(current_user):
        """Restore the database from a previous backup using a restore code."""
        from controllers.rolecheck import is_authorized
        import sqlite3
        import os
        import sys
        import shutil
        from security.encryption import load_symmetric_key, encrypt_message, decrypt_message
        from logs.log import log_instance
        from security.validation import Validation


        if not is_authorized(current_user.role, 'system_administrator_restore_backup'):
            print("You do not have permission to restore backups.")
            return

        # Check if the user has a restore code linked to their account
        if not BackupManager.check_for_restore_code(current_user):
            print("No restore code linked to your account. Please contact a super administrator.")
            return
        
            # Ask for the restore code with validation and attempt limiting
        MAX_RESTORE_CODE_ATTEMPTS = 3
        restore_code_attempts = 0
        valid_code_found = False
        
        # Get key for decryption
        key = load_symmetric_key()
        base_dir, db_path, backup_dir = BackupManager.get_paths()
        
        while not valid_code_found and restore_code_attempts < MAX_RESTORE_CODE_ATTEMPTS:
            restore_code_input = input("\nEnter your restore code (or 'c' to cancel): ").strip()
            
            if restore_code_input.lower() == 'c':
                print("Backup restoration cancelled.")
                return
            
            # Connect to database and get all restore codes
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, system_admin_id, backup_filename FROM restore_codes")
            all_restore_codes = cursor.fetchall()
            conn.close()

            # Look for a matching restore code
            matching_restore_code = None
            backup_filename = None
            
            for code_id, code_encrypted, admin_id, filename_encrypted in all_restore_codes:
                try:
                    decrypted_code = decrypt_message(code_encrypted, key)
                    if decrypted_code == restore_code_input:
                        decrypted_admin_id = int(decrypt_message(admin_id, key))
                        
                        if decrypted_admin_id == current_user.id:
                            matching_restore_code = code_id
                            backup_filename = decrypt_message(filename_encrypted, key)
                            valid_code_found = True
                            break
                except Exception as e:
                    continue
            
            if not valid_code_found:
                restore_code_attempts += 1
                print("Invalid restore code or code does not belong to your account.")
                log_instance.log_invalid_input(current_user.username, "system administrator restore backup", f"Invalid restore code: {restore_code_input}")
                
                if restore_code_attempts >= MAX_RESTORE_CODE_ATTEMPTS:
                    print("Too many failed attempts to enter a valid restore code.")
                    log_instance.addlog(current_user.username, "system administrator restore backup", 
                                    f"Multiple failed restore code attempts ({restore_code_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)

        # Proceed with restoring the backup
        backup_path = os.path.join(base_dir, 'backups', backup_filename)

        if not os.path.exists(backup_path):
            print(f"Backup file {backup_filename} does not exist at {backup_path}")
            log_instance.addlog(current_user.username, "Restore backup failed", f"Backup file not found: {backup_filename}", True)
            return

        # Confirmation with attempt limiting
        MAX_CONFIRM_ATTEMPTS = 3
        confirm_attempts = 0
        confirmation_received = False
        # Ask for confirmation before restoring the backup
        print("\nIMPORTANT: After restoring the backup, you will be logged out automatically for security reasons.")
        print("You will need to log in again after the restore process is complete.")
        confirm = input(f"WARNING: This will replace the current database with the backup from {backup_filename}.\nAll current data will be lost. Continue? (y/n): ")
        
        while not confirmation_received and confirm_attempts < MAX_CONFIRM_ATTEMPTS:
            confirm = input(f"WARNING: This will replace the current database with the backup from {backup_filename}.\nAll current data will be lost. Continue? (y/n): ")
            
            if confirm.lower() == 'y':
                confirmation_received = True
            elif confirm.lower() == 'n':
                print("Backup restoration cancelled.")
                return False
            else:
                confirm_attempts += 1
                print("Invalid input. Please enter 'y' to continue or 'n' to cancel.")
                log_instance.log_invalid_input(current_user.username, "confirmation", f"Invalid confirmation input: {confirm}")
                
                if confirm_attempts >= MAX_CONFIRM_ATTEMPTS:
                    print("Too many failed attempts to confirm. Operation cancelled.")
                    log_instance.addlog(current_user.username, "Restore backup", 
                                    f"Multiple failed confirmation attempts ({confirm_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)


        try:
            # Proceed with restoring the backup
            backup_path = os.path.join(backup_dir, backup_filename)

            # Ensure the backup directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            # Use the extract_db_from_zip helper
            if backup_filename.endswith('.zip'):
                if BackupManager.extract_db_from_zip(backup_path, db_path, current_user):
                    print(f"Database successfully restored from {backup_filename}")
                else:
                    return False
            else:
                # If it's not a ZIP file, copy the file directly
                shutil.copy2(backup_path, db_path)

            # Remove the restore code after use
            conn = sqlite3.connect(db_path)  # Use the path from the helper
            cursor = conn.cursor()
            cursor.execute("DELETE FROM restore_codes WHERE id = ?", (matching_restore_code,))
            conn.commit()
            conn.close()

            print(f"Database successfully restored from {backup_filename}.")
            print("\nYou are now being logged out for security reasons.")
            print("Please restart the application and log in again.")
            sys.exit(0)  # Close the application successfully

        except Exception as e:
            print(f"Error restoring backup: {e}")
            log_instance.addlog(current_user.username, "Restore backup failed", f"Error: {str(e)}", True)
            return False

    def check_for_restore_code(current_user):
        """Check if the current user has a restore code linked to their account."""
        from controllers.rolecheck import is_authorized
        import sqlite3
        import os
        from security.encryption import load_symmetric_key, decrypt_message
        
        if not is_authorized(current_user.role, 'check_for_restore_code'):
            print("You do not have permission to check for restore codes.")
            return False
        
        base_dir, db_path, backup_dir = BackupManager.get_paths()
        key = load_symmetric_key()
        
        conn = sqlite3.connect('data/urban_mobility.db')
        cursor = conn.cursor()

        # Query for all restore codes linked to this admin
        cursor.execute("SELECT code, backup_filename, system_admin_id FROM restore_codes")
        all_codes = cursor.fetchall()
        conn.close()

        # Filter codes linked to this administrator
        user_codes = []
        for code_encrypted, filename_encrypted, admin_id_encrypted in all_codes:
            try:
                # Decrypt the admin ID and compare with current user
                decrypted_admin_id = int(decrypt_message(admin_id_encrypted, key))
                
                if decrypted_admin_id == current_user.id:
                    decrypted_code = decrypt_message(code_encrypted, key)
                    decrypted_filename = decrypt_message(filename_encrypted, key)
                    user_codes.append((decrypted_code, decrypted_filename))
            except Exception:
                continue
        
        if not user_codes:
            return False  # No restore codes found

        return True  # Restore codes found

    def revoke_restore_code_by_super_admin(current_user):
        """Revoke a restore code as a super administrator."""
        from controllers.rolecheck import is_authorized
        import sqlite3
        import os
        from security.encryption import load_symmetric_key, decrypt_message
        from logs.log import log_instance
        from security.validation import Validation
        import sys
        
        if not is_authorized(current_user.role, 'revoke_restore_code'):
            print("You do not have permission to revoke restore codes.")
            return
            
        base_dir, db_path, backup_dir = BackupManager.get_paths()
        key = load_symmetric_key()
        
        # Get all restore codes
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, code, system_admin_id, backup_filename FROM restore_codes")
        all_restore_codes = cursor.fetchall()
        
        # Get all administrators for displaying names
        cursor.execute("SELECT id, username FROM users")
        all_users = cursor.fetchall()
        conn.close()
        
        # Create a lookup table for admin usernames
        admin_usernames = {}
        for user_id, username_encrypted in all_users:
            try:
                admin_usernames[user_id] = decrypt_message(username_encrypted, key)
            except Exception:
                admin_usernames[user_id] = f"User ID {user_id}"
        
        # Process and display all restore codes
        if not all_restore_codes:
            print("No restore codes found in the system.")
            return
        
        print("\n=== Active Restore Codes ===")
        valid_codes = []
        
        for i, (code_id, code_encrypted, admin_id_encrypted, filename_encrypted) in enumerate(all_restore_codes, 1):
            try:
                decrypted_code = decrypt_message(code_encrypted, key)
                decrypted_filename = decrypt_message(filename_encrypted, key)
                decrypted_admin_id = int(decrypt_message(admin_id_encrypted, key))
                admin_name = admin_usernames.get(decrypted_admin_id, f"Unknown Admin (ID: {decrypted_admin_id})")
                
                print(f"{i}. Code: {decrypted_code} - Admin: {admin_name} - Backup: {decrypted_filename}")
                valid_codes.append((code_id, decrypted_code, decrypted_admin_id, admin_name, decrypted_filename))
            except Exception as e:
                print(f"Error processing code ID {code_id}: {e}")
                continue
        
        if not valid_codes:
            print("No valid restore codes found.")
            return
        
        # Ask which code to revoke
        MAX_SELECTION_ATTEMPTS = 3
        selection_attempts = 0
        code_selection_valid = False
        
        while not code_selection_valid and selection_attempts < MAX_SELECTION_ATTEMPTS:
            choice = input("\nEnter the number of the code to revoke (or 'c' to cancel): ")
            
            if choice.lower() == 'c':
                print("Operation cancelled.")
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(valid_codes):
                    code_to_revoke = valid_codes[index]
                    code_selection_valid = True
                else:
                    selection_attempts += 1
                    print(f"Please enter a number between 1 and {len(valid_codes)}.")
                    log_instance.log_invalid_input(current_user.username, "restore code selection", f"Invalid code index: {index + 1}")
                    
                    if selection_attempts >= MAX_SELECTION_ATTEMPTS:
                        print("Too many failed attempts to select a valid restore code.")
                        log_instance.addlog(current_user.username, "Backup code revoking", 
                                        f"Multiple failed restore code selection attempts ({selection_attempts})", True)
                        print("For security reasons, you have been logged out.")
                        sys.exit(1)
            except ValueError:
                selection_attempts += 1
                print("Please enter a valid number.")
                log_instance.log_invalid_input(current_user.username, "restore code selection", f"Invalid input: {choice}")
                
                if selection_attempts >= MAX_SELECTION_ATTEMPTS:
                    print("Too many failed attempts to select a valid restore code.")
                    log_instance.addlog(current_user.username, "ackup code revoking", 
                                    f"Multiple failed restore code selection attempts ({selection_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
        
        # Confirm revocation with validation and attempt limiting
        MAX_CONFIRM_ATTEMPTS = 3
        confirm_attempts = 0
        confirmation_received = False
        
        while not confirmation_received and confirm_attempts < MAX_CONFIRM_ATTEMPTS:
            confirm = input(f"Are you sure you want to revoke the restore code {code_to_revoke[1]} assigned to {code_to_revoke[3]}? (y/n): ")
            
            if confirm.lower() == 'y':
                confirmation_received = True
            elif confirm.lower() == 'n':
                print("Operation cancelled.")
                return
            else:
                confirm_attempts += 1
                print("Invalid input. Please enter 'y' to confirm or 'n' to cancel.")
                log_instance.log_invalid_input(current_user.username, "confirmation", f"Invalid confirmation input: {confirm}")
                
                if confirm_attempts >= MAX_CONFIRM_ATTEMPTS:
                    print("Too many failed attempts to confirm. Operation cancelled.")
                    log_instance.addlog(current_user.username, "Revoke restore code", 
                                    f"Multiple failed confirmation attempts ({confirm_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
        
        # Revoke the code
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM restore_codes WHERE id = ?", (code_to_revoke[0],))
            conn.commit()
            conn.close()
            
            print(f"Restore code successfully revoked.")
            log_instance.addlog(
                current_user.username, 
                "Revoked restore code", 
                f"Revoked code {code_to_revoke[1]} from admin {code_to_revoke[3]}", 
                False
            )
        except sqlite3.Error as e:
            print(f"Error revoking restore code: {e}")
            log_instance.addlog(current_user.username, "Revoke restore code failed", f"Error: {str(e)}", True)


    def super_admin_restore_backup(current_user):
        """Restore the database from a previous backup."""
        import os
        import zipfile
        from datetime import datetime
        from controllers.rolecheck import is_authorized
        import shutil
        import sys
        from logs.log import log_instance
        from security.validation import Validation

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
        MAX_SELECTION_ATTEMPTS = 3
        selection_attempts = 0
        backup_selection_valid = False
        selected_backup = None
        
        while not backup_selection_valid and selection_attempts < MAX_SELECTION_ATTEMPTS:
            choice = input("\nEnter the number of the backup you want to restore (or 'c' to cancel): ")
            
            if choice.lower() == 'c':
                print("Backup restoration cancelled.")
                return False
            
            try:
                choice_index = int(choice) - 1
                
                if 0 <= choice_index < len(backups):
                    selected_backup = backups[choice_index]
                    backup_selection_valid = True
                else:
                    selection_attempts += 1
                    print(f"Please enter a number between 1 and {len(backups)}.")
                    log_instance.log_invalid_input(current_user.username, "backup selection", 
                                                f"Invalid backup index: {choice_index + 1}")
                    
                    if selection_attempts >= MAX_SELECTION_ATTEMPTS:
                        print("Too many failed attempts to select a valid backup.")
                        log_instance.addlog(current_user.username, "Backup restoration", 
                                        f"Multiple failed backup selection attempts ({selection_attempts})", True)
                        print("For security reasons, you have been logged out.")
                        sys.exit(1)
            except ValueError:
                selection_attempts += 1
                print("Please enter a valid number.")
                log_instance.log_invalid_input(current_user.username, "backup selection", f"Invalid backup selection input: {choice}")
                
                if selection_attempts >= MAX_SELECTION_ATTEMPTS:
                    print("Too many failed attempts to select a valid backup.")
                    log_instance.addlog(current_user.username, "Backup restoration", 
                                    f"Multiple failed backup selection attempts ({selection_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
        
        selected_backup_path = os.path.join(backup_dir, selected_backup)

        # Ask for confirmation
        MAX_CONFIRM_ATTEMPTS = 3
        confirm_attempts = 0
        confirmation_received = False

        print("\n\nIMPORTANT: After restoring the backup, you will be logged out automatically for security reasons.")
        print("You will need to log in again after the restore process is complete.")
        confirm = input(f"WARNING: This will replace the current database with the backup from {selected_backup}.\nAll current data will be lost.\nContinue? (y/n): ")
        
        while not confirmation_received and confirm_attempts < MAX_CONFIRM_ATTEMPTS:
            confirm = input(f"WARNING: This will replace the current database with the backup from {selected_backup}.\nAll current data will be lost.\nContinue? (y/n): ")
            
            if confirm.lower() == 'y':
                confirmation_received = True
            elif confirm.lower() == 'n':
                print("Backup restoration cancelled.")
                return False
            else:
                confirm_attempts += 1
                print("Invalid input. Please enter 'y' to continue or 'n' to cancel.")
                log_instance.log_invalid_input(current_user.username, "confirmation", f"Invalid confirmation input: {confirm}")
                
                if confirm_attempts >= MAX_CONFIRM_ATTEMPTS:
                    print("Too many failed attempts to confirm. Operation cancelled.")
                    log_instance.addlog(current_user.username, "Super admin restore backup", 
                                    f"Multiple failed confirmation attempts ({confirm_attempts})", True)
                    print("For security reasons, you have been logged out.")
                    sys.exit(1)
    
        try:
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            # Use the extract_db_from_zip helper
            if BackupManager.extract_db_from_zip(selected_backup_path, db_path, current_user):
                print(f"Database successfully restored from {selected_backup}")
            else:
                return False
            
            print("\nYou are now being logged out for security reasons.")
            print("Please restart the application and log in again.")
            sys.exit(0)  # Close the application successfully

        except Exception as e:
            print(f"Error restoring backup: {e}")
            log_instance.addlog(current_user.username, "Super admin restore backup failed", f"Error: {str(e)}", True)
            return False
            

backup_instance = BackupManager()