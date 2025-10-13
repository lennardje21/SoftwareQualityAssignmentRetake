import os, re, getpass
class general_methods:
    @staticmethod
    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def highlight(value, search_key):
        if search_key is None:
            return str(value)
        value_str = str(value)
        pattern = re.compile(re.escape(search_key), re.IGNORECASE)
        return pattern.sub(lambda m: f'\033[92m{m.group(0)}\033[0m', value_str)
    
    
    @staticmethod
    def input_password(prompt="Password: "):
        return getpass.getpass(prompt)
    
    @staticmethod
    def hidden_input(prompt=""):
        return getpass.getpass(prompt)