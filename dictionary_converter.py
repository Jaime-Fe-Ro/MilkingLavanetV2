import json
import os
from datetime import datetime


def get_dictionary_file():
    logs_folder = 'logs'
    logs_path = os.path.join(os.getcwd(), logs_folder)
    if not os.path.exists(logs_path):
        print(f"Logs folder '{logs_folder}' does not exist.")
        return None

    # List files in the logs folder
    print("Available log files:")
    log_files = [file for file in os.listdir(logs_path) if file.startswith("dictionary_") and file.endswith(".json")]
    for i, file in enumerate(log_files, start=1):
        print(f"{i}. {file}")

    date_str = input("Enter 'today' to use logs from today or specify the date in DD-MM-YYYY format: ")
    if date_str.lower() == 'end':
        return None

    if date_str.lower() == 'today':
        date_str = datetime.today().strftime('%d-%m-%Y')

    matching_files = [file for file in log_files if date_str in file]

    if not matching_files:
        print("No matching log files found.")
        return None

    if len(matching_files) == 1:
        return os.path.join(logs_path, matching_files[0])
    else:
        print("Multiple log files found for the specified date. Please select one:")
        for i, file in enumerate(matching_files, start=1):
            print(f"{i}. {file}")
        choice = input("Enter the number of the file you want to choose or type 'end' to exit: ")
        if choice.lower() == 'end':
            return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(matching_files):
                return os.path.join(logs_path, matching_files[index])
            else:
                print("Invalid choice.")
                return None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None

def convert_rpc_endpoints(input_file, output_folder):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    for address, info in data.items():
        rpc_endpoint = info.get('rpc_endpoint')
        if rpc_endpoint and rpc_endpoint.startswith('https://eth1.lava.build/lava-referer-'):
            info['rpc_endpoint'] = rpc_endpoint.replace('https://eth1.lava.build/lava-referer-', '')
    
    output_file = os.path.join(output_folder, "converted_" + os.path.basename(input_file))
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    input_file = get_dictionary_file()
    if not input_file:
        print("No valid dictionary file found.")
    else:
        output_folder = os.path.join(os.getcwd(), 'logs')
        convert_rpc_endpoints(input_file, output_folder)
