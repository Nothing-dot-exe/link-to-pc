import os
import subprocess
import time

def run_adb(command):
    """Runs an ADB command and returns the output."""
    try:
        # command is a list of strings
        full_command = ["adb"] + command
        print(f"\n[>] Running: {' '.join(full_command)}")
        result = subprocess.run(full_command, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error running command: {e}")
        print(f"[!] Engine Output: {e.stderr}")
        return None
    except FileNotFoundError:
        print("\n[!] Error: 'adb' is not installed or not added to your system PATH.")
        return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    while True:
        clear_screen()
        print("="*55)
        print("          🚀 Ultimate ADB Power Toolkit 🚀          ")
        print("="*55)
        print("1. 🔌 Device Connection & Power")
        print("2. 📦 App Management (Package Manager)")
        print("3. 👆🏼 UI & Automation (Simulate Touches/Keys)")
        print("4. 📸 Screen Capture & Media")
        print("5. 🛠️ Diagnostics & System Info")
        print("0. ❌ Exit")
        print("="*55)
        
        choice = input("Select a category (0-5): ")
        
        if choice == '1':
            device_menu()
        elif choice == '2':
            app_menu()
        elif choice == '3':
            ui_menu()
        elif choice == '4':
            media_menu()
        elif choice == '5':
            sys_menu()
        elif choice == '0':
            print("Exiting toolkit... Goodbye!")
            break
        else:
            print("Invalid choice! Please select a valid number.")
            time.sleep(1)

def device_menu():
    clear_screen()
    print("--- 🔌 Device Connection & Power ---")
    print("1. List Connected Devices")
    print("2. Restart ADB Server (Fix Disconnects)")
    print("3. Reboot Device Normally")
    print("4. Reboot to Bootloader (Fastboot)")
    print("5. Connect via Wi-Fi (Requires Port 5555 open)")
    print("0. Back to Main Menu")
    
    c = input("\nChoice: ")
    if c == '1': run_adb(["devices"])
    elif c == '2':
        run_adb(["kill-server"])
        run_adb(["start-server"])
    elif c == '3': run_adb(["reboot"])
    elif c == '4': run_adb(["reboot", "bootloader"])
    elif c == '5':
        ip = input("Enter Device IP Address (e.g., 192.168.1.5): ")
        run_adb(["connect", ip])
    
    input("\nPress Enter to return...")

def app_menu():
    clear_screen()
    print("--- 📦 App Management ---")
    print("1. List All Installed Packages")
    print("2. Install an APK from PC")
    print("3. Uninstall an App")
    print("4. Clear App Data & Cache (Factory Reset App)")
    print("5. Disable/Freeze an App (Bloatware removal)")
    print("0. Back to Main Menu")
    
    c = input("\nChoice: ")
    if c == '1': run_adb(["shell", "pm", "list", "packages"])
    elif c == '2':
        apk = input("Enter path to APK file: ")
        run_adb(["install", apk])
    elif c == '3':
        pkg = input("Enter package name (e.g., com.android.chrome): ")
        run_adb(["uninstall", pkg])
    elif c == '4':
        pkg = input("Enter package name to clear: ")
        run_adb(["shell", "pm", "clear", pkg])
    elif c == '5':
        pkg = input("Enter package name to disable (e.g., com.google.android.youtube): ")
        run_adb(["shell", "pm", "disable-user", pkg])
        
    input("\nPress Enter to return...")

def ui_menu():
    clear_screen()
    print("--- 👆🏼 UI & Automation ---")
    print("1. Simulate Screen Tap")
    print("2. Simulate Swipe Gesture")
    print("3. Inject/Type Text")
    print("4. Press Power Button (Wake/Sleep)")
    print("5. Press Home Button")
    print("0. Back to Main Menu")
    
    c = input("\nChoice: ")
    if c == '1':
        x = input("Enter X coordinate: ")
        y = input("Enter Y coordinate: ")
        run_adb(["shell", "input", "tap", x, y])
    elif c == '2':
        x1 = input("Start X: ")
        y1 = input("Start Y: ")
        x2 = input("End X: ")
        y2 = input("End Y: ")
        run_adb(["shell", "input", "swipe", x1, y1, x2, y2, "500"])
    elif c == '3':
        txt = input("Enter text to type: ")
        # ADB text injection requires spaces to be replaced with %s
        run_adb(["shell", "input", "text", txt.replace(" ", "%s")])
    elif c == '4': run_adb(["shell", "input", "keyevent", "26"])
    elif c == '5': run_adb(["shell", "input", "keyevent", "3"])

    input("\nPress Enter to return...")

def media_menu():
    clear_screen()
    print("--- 📸 Screen Capture & Media ---")
    print("1. Take Screenshot (Saves as screenshot.png on PC)")
    print("2. Record Screen (10 seconds, saves as screenrecord.mp4 on PC)")
    print("0. Back to Main Menu")
    
    c = input("\nChoice: ")
    if c == '1':
        print("Taking screenshot on device...")
        run_adb(["shell", "screencap", "-p", "/sdcard/sc_temp.png"])
        print("Pulling screenshot to PC...")
        run_adb(["pull", "/sdcard/sc_temp.png", "screenshot.png"])
        run_adb(["shell", "rm", "/sdcard/sc_temp.png"])
        print("\n[+] Saved as screenshot.png in current folder.")
    elif c == '2':
        print("Recording for 10 seconds... Please wait.")
        run_adb(["shell", "screenrecord", "--time-limit", "10", "/sdcard/sr_temp.mp4"])
        print("Pulling video to PC...")
        run_adb(["pull", "/sdcard/sr_temp.mp4", "screenrecord.mp4"])
        run_adb(["shell", "rm", "/sdcard/sr_temp.mp4"])
        print("\n[+] Saved as screenrecord.mp4 in current folder.")
        
    input("\nPress Enter to return...")

def sys_menu():
    clear_screen()
    print("--- 🛠️ Diagnostics & System Info ---")
    print("1. Check Battery Health & Level")
    print("2. Get Device Model & Android Version")
    print("3. List Top Running Processes (RAM usage)")
    print("4. Change Screen Resolution (Danger)")
    print("0. Back to Main Menu")
    
    c = input("\nChoice: ")
    if c == '1':
        run_adb(["shell", "dumpsys", "battery"])
    elif c == '2':
        print("Device Model:")
        run_adb(["shell", "getprop", "ro.product.model"])
        print("Android Version:")
        run_adb(["shell", "getprop", "ro.build.version.release"])
    elif c == '3':
        run_adb(["shell", "top", "-n", "1", "-m", "15"])
    elif c == '4':
        res = input("Enter new resolution (e.g., 1080x1920) or type 'reset': ")
        if res.lower() == 'reset':
            run_adb(["shell", "wm", "size", "reset"])
        else:
            run_adb(["shell", "wm", "size", res])
        
    input("\nPress Enter to return...")

if __name__ == "__main__":
    print("Checking if ADB is available...")
    if run_adb(["version"]):
        time.sleep(1)
        main_menu()
    else:
        print("\n[!] Please install ADB and add it to your system PATH before running this tool.")
