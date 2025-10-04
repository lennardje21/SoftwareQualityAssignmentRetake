import sys
from logs.log import log_instance

def require_authorization(current_user, action: str):
    if not is_authorized(current_user.role, action):
        log_instance.addlog(current_user.username, action, "Unauthorized access attempt", True)
        print(f"You do not have permission to perform the action: {action}.")
        sys.exit()

def is_authorized(role: str, action: str) -> bool:
    """Check if the user role is authorized to perform the action."""
    role = role.strip().lower()
    role_permissions = {
        "service_engineer": {
            "update_scooter",
            "search_scooter",
            "show_scooter",
            "update_own_password"
        },
        "system_administrator": {
            # all roles for a service engineer
            "update_scooter", "search_scooter", "update_own_password", "show_scooter",
            # traveller management
            "add_traveller", "update_traveller", "delete_traveller", "search_traveller","show_traveller"
            # scooter management
            "add_scooter", "update_scooter", "delete_scooter",
            # user management (service engineers)
            "add_new_user", "update_user", "reset_password",
            "delete_user", "view_users",
            # system management
            "view_logs", "restore_backup", "create_backup", "system_administrator_restore_backup", "check_for_restore_code"
        },
        "super_administrator": {
            # all roles for a system administrator and service engineer
            "update_scooter", "search_scooter",
            "add_traveller", "update_traveller", "delete_traveller", "search_traveller", "list_travellers", "show_traveller",
            "add_scooter", "update_scooter", "delete_scooter", "search_scooter", "show_scooter",
            "add_new_user", "update_user", "reset_password",
            "delete_user", "view_users",
            "view_logs", 
            # extra superadmin rights
            "delete_user",
            "generate_restore_code",
            "revoke_restore_code", "restore_backup", "create_backup", "link_backup_restore_code", "super_admin_restore_backup"
        }
    }
    return action in role_permissions.get(role, set())