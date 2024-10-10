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

    while True: 
        error_mode = input("When almighty encounters an error> ").lower()
        if error_mode in ["all", "scored", "ask", "none", "empty"]: break
        print("Invalid input")
    
    while True: 
        compleate_mode = input("When almighty succeeds> ").lower()
        if compleate_mode in ["all", "scored", "ask", "none", "empty"]: break
        print("Invalid input")
    
    save_directory = input("Where would you like to save these files (defualts to `forms/`)")
    if save_directory.strip() == "": save_directory = "forms/"
    
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
            "export_dir": "forms/"
        }
    }

print("\nStep 2: Dependancy Setup.")
print("2.A In order for Almighty to run, It relys on non-standard libary modules, This step will use `pip`, to install the python modules.")
print("  Tip: it's advised to make sure you are connected to the internet.")

while True: 
    text = input("Install Dependencies? [y/N] ").lower()
    if not text or text == 'n':
        print("Aborting Setup...")
        exit(-1)
    if text == 'y': break
    else: print("Input was not explicitly Y or N")

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
