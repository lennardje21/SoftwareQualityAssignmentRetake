from models.db import initialize_database
from controllers.auth import login
from controllers.menus import service_engineer_menu, system_administrator_menu, super_administrator_menu


def main():

    initialize_database()
    while True:
        # print("--- DEBUG: User login attempt --")
        user = login()
        if not user:
            continue  # login failed, opnieuw proberen
        while True:
            # Toon menu voor deze ingelogde user
            role = user.role
            if role == "service_engineer":
                stay_logged_in = service_engineer_menu(user)
            elif role == "system_administrator":
                stay_logged_in = system_administrator_menu(user)
            elif role == "super_administrator":
                stay_logged_in = super_administrator_menu(user)
            else:
                print("Unknown role.")
                stay_logged_in = False

            if not stay_logged_in:
                print("You have been logged out.")
                break  # terug naar login-prompt

if __name__ == "__main__":
    main()







    
