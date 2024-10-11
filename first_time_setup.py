import json
from os import system, path
from sys import platform

name = r"""
 ______   ___                           __      __                
/\  _  \ /\_ \               __        /\ \    /\ \__             
\ \ \L\ \\//\ \     ___ ___ /\_\     __\ \ \___\ \ ,_\  __  __    
 \ \  __ \ \ \ \  /' __` __`\/\ \  /'_ `\ \  _ `\ \ \/ /\ \/\ \   
  \ \ \/\ \ \_\ \_/\ \/\ \/\ \ \ \/\ \L\ \ \ \ \ \ \ \_\ \ \_\ \  
   \ \_\ \_\/\____\ \_\ \_\ \_\ \_\ \____ \ \_\ \_\ \__\\/`____ \ 
    \/_/\/_/\/____/\/_/\/_/\/_/\/_/\/___L\ \/_/\/_/\/__/ `/___/> \
                                     /\____/                /\___/
                                     \_/__/                 \/__/ 
"""[1:-1]

if __name__ != "__main__":
    print("I don't know why your importing the setup utility, but please just run this as a script.")
    raise NotImplementedError()

def Yes_or_No(prompt: str) -> bool:
    while True:
        text = input(f"{prompt}[Y/n]> ").lower()
        if text.strip() == "" or text == "y":
            return True
        elif text == "n":
            return False
        else:
            print("Invalid Input")

def in_list(prompt: str, valid: list[str]) -> str:
    while True:
        text = input(f"{prompt} {valid}> ").lower()
        if text in valid: return text
        print("Invalid input")

def is_int(prompt: str) -> int:
    while True:
        try: return int(input(prompt))
        except: print("Invalid Input")

print(name)

print("Welcome To Almighty, This is the Setup Guide.")
print("If you don't already have firefox please install it.")

if not path.exists("config.json"):
    print("\nStep 1: Firefox / Config Setup.")
    print("1.A Please setup a firefox profile with an google account logged in")
    print("  Note: while some google forms don't require an google login, some do,\n  so this sub-step is semi-optional, But Recomended")

    input("Enter to Continue... ")

    print("\n1.B In firefox, head to 'about:profiles', and find the profile with the google account")
    print("  Tip: it's advised to visit this page with the profile with the google acount because it will label which 'profile is in use and cannot be deleted', if its the only profile open.")

    input("Enter to Continue... ")

    print("\n1.C In firefox, under the profile name, in the table copy the value of \"Root Directory\"")
    
    profile_path = input("Firefox Profile Path: ")

    print("\n1.D Please provide an email")
    print("  Note: while some forms have an automatic email collection method where you manualy input the email and it like a question. but internaly, it isn't")

    email = input("Email: ")

    print("\n1.E Exportation Rules, how forms will be exported the following modes exist: ")
    print(" * All: Will export all awnsers, including unscored questions like name entries")
    print(" * Scored: Will only all scored awnsers")
    print(" * Empty: Will only export the questions without an awnser key.")
    print(" * None: Will not export.")
    print(" * Ask: Will prompt user at export time.")

    options = ["all", "scored", "ask", "none", "empty"]
    error_mode = in_list("When almighty encounters an error", options)
    
    compleate_mode = in_list("When almighty succeeds", options)
    
    save_directory = input("Where would you like to save these files (defualts to `forms/`)?> ")
    if save_directory.strip() == "": save_directory = "forms/"
    if not save_directory.endswith('/') and not save_directory.endswith('\\'): save_directory += '/'
    
    print("\n1.F Networking (Cheatsheet) Rules: ")
    print("  Cheatsheet is a network extenstension to almighty where it's crowd sourced awnser key's for whatever form you are compleating.")
    print("if your providers have the awnser for the form, it reduces the atempts needed down to one if all awnsers are filled in.")
    print("and if not, you get to help the next person searching for the exact same form using almighty.")
    print("\n  All form data gets properly sanitized beforehand so you won't be sending personal info like name or email adrress, before it leaves your device.")

    enable_cheatsheet =  Yes_or_No("Enable Cheatsheet?[Y/n]> ")
    
    print("")
    if enable_cheatsheet:
        print("1.F.1 Networking (Cheatsheet) Rules: Form Sending")
        print("  In order for the critical functionaly of Cheatsheet to work, it needs crowd sourced forms.")

        form_sending = Yes_or_No("Will you contribute your forms?")

        print("\n1.F.2 Networking (Cheatsheet) Rules: Form Receiving")
        print("  With this off, you won't donwload any awnserkeys from Cheatsheet")

        form_receiving = Yes_or_No("Will you receiving forms?")

        print("\n1.F.3 Networking (Cheatsheet) Rules: Providers")
        print("  Without configuring your providers, you won't be doing any Sending or Reciving")
        print("\n  Also I, the creator have my own provider, would you like to add it to your provider list (it's sorta the defualt)?")

        provider_list = []

        add_formtress = Yes_or_No("Add defualt provider?")

        if add_formtress:
            provider_list.append({
                "name": "Formtress (Defualt)",
                "mode": "ipv4",
                "addr": "ipv4",
                "port": 6590,
            })

        add_localhost_provider = Yes_or_No("Add localhost provider? (useful for development)")

        if add_localhost_provider:
            provider_list.append({
                "name": "Localhost",
                "mode": "ipv4",
                "addr": "127.7.7.7",
                "port": 6590,
            })

        while True:
            add_another_config = Yes_or_No("Would you like to add another provider?")
            if not add_another_config: break
            provider_list.append({
                "name": input("Provider Name> "),
                "mode": in_list("Provider Mode", ["ipv4", "ipv6", "blue"]),
                "addr": input("Provider Address> "),
                "port": is_int("Provider Port")
            })

        print("\n1.F.4 Networking (Cheatsheet) Rules: Hosting Configuration")
        print("  Cheatsheet works compleatly fine without any hosting configurations on the client computer.")
        print("\n  Also I, the creator have my own provider, would you like to add it to your provider list (it's sorta the defualt)?")

        host_config_list = []

        if add_localhost_provider:
            host_config_list.append({
                "name": "Localhost",
                "mode": "ipv4",
                "addr": "127.7.7.7",
                "port": 6590,
                "form_directory": save_directory
            })
        
        while True:
            add_another_config = Yes_or_No("Would you like to add another hosting config?")
            if not add_another_config: break
            provider_list.append({
                "name": input("Config Name> "),
                "mode": in_list("Config Mode", ["ipv4", "ipv6", "blue"]),
                "addr": input("Config Address> "),
                "port": is_int("Config Port"),
                "form_directory": input("Form Storage Dirctory> ")
            })  

        config = {
            "profiles": {
                "defualt": {
                    "profile_path": profile_path,
                    "provided_email": email
                }
            },
            "export": {
                "on_error": error_mode,
                "on_compleation": compleate_mode,
                "export_dir": save_directory
            },
            "cheatsheet": {
                "enabled": True,
                "send_forms": True,
                "recv_forms": True,
                "providers": provider_list,
                "hosting": host_config_list
            }
        }

    else:
        print("Cool, if you ever want to change your mind look at config.json and CONFIG.md")
        print("If your sure you absolutly don't want it you can delete cheatsheet.py and main.py will be compleatly unefected.")
        config = {
            "profiles": {
                "defualt": {
                    "profile_path": profile_path,
                    "provided_email": email
                }
            },
            "export": {
                "on_error": error_mode,
                "on_compleation": compleate_mode,
                "export_dir": save_directory
            },
            "cheatsheet": {
                "enabled": False,
                "send_forms": False,
                "recv_forms": False,
                "providers": [],
                "hosting": []
            }
        }
    
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=4)


print("\nStep 2: Dependancy Setup.")
print("2.A In order for Almighty to run, It relys on non-standard libary modules, This step will use `pip`, to install the python modules.")
print("  Tip: it's advised to make sure you are connected to the internet.")

if not Yes_or_No("Install Dependencies?"):
    print("Aborting Setup...")
    exit(-1)

system("pip install -r requirements.txt") 
if platform == "win32": system("pip install -r requirements.txt") # pip on windows sometimes errors out because of '.delete me' logic, so run it again

print("\nStep 3: Validation.")
print("3.A This step will open up a web browser navigate to `example.com` and then validate it's contents")
print("  Tip: it's advised to make sure you are connected to the internet, and close ALL instances of firefox.")

input("Enter to Continue... ")

try:
    print("\nImporting main file... ", end="")
    import main
    print("Imported.")
    main.term_init()
    main.display_logo()
    example_gradent = main.gradent_str('https://example.com', (0, 255, 0), (0, 255, 255))
    print("\nSpawning Firefox... ", end="")
    driver, _, _ = main.make_webdriver()
    print("Spawned.")
    print(f"Going to `{example_gradent}`... ", end="")
    driver.get("https://example.com")
    print("Page Loaded.")
    print(f"Validating hash of: `{example_gradent}`... ", end="")
    number = hash(driver.page_source)
    driver.close()
    assert number == 0x2a0ebd1e8523c243 # hash of example.com
    print("Valid.")

except AssertionError:
    print("Hash Check Fail.")
    print("This error doesn't really matter much, maybe ietf updated example.com?")

except ImportError:
    print("Import Failure.")
    print(" * Check that all the dependancies are properly installed.")
    print(" * Make sure that this script is running in the same directory as the main.py")

except Exception as e:
    print(f"Webdriver error: {e}")
    print(" * Check that all the dependancies are properly installed.")
    print(" * Make sure you didn't mess with firefox while its running.")
    print(" * Make sure that there were no open firefox instances.")
    print(" * Make sure that you are connected to the internet.")
    print(" * Make sure that this script is running in the same directory as the main.py")

finally:
    print("If an error accoured, please follow the following debug information.")
    print("Elsewise, You are ready to run `main.py`")
