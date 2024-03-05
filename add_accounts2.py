import json
import os
import re
from datetime import datetime

logs_folder = 'logs'


def create_logs_folder_if_not_existing():
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)


def get_today_highest_log_number():
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")
    pattern = re.compile(f'dictionary_{date_str}-(\d+).json')

    highest_log_number = 0
    for file_name in os.listdir(logs_folder):
        match = pattern.match(file_name)
        if match:
            log_number = int(match.group(1))
            if log_number > highest_log_number:
                highest_log_number = log_number
    return highest_log_number if highest_log_number != 0 else 1


def create_log_file_name():
    log_count_today = get_today_highest_log_number()
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")
    return f"{logs_folder}/dictionary_{date_str}-{log_count_today + 1}.json"


def save_account_dict(account_dict, file_name):
    with open(file_name, 'w') as file:
        json.dump(account_dict, file, indent=4)
        print("Account dictionary saved")


def validate_rpc_endpoint(rpc_endpoint, account_dict, file_name):
    if len(rpc_endpoint) != 74:
        rpc_endpoint = input("Invalid RPC endpoint, try again: ")
        stop_running_check(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = validate_rpc_endpoint(rpc_endpoint, account_dict, file_name)
        check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name)
    rpc_endpoint = rpc_endpoint.replace('https://eth1.lava.build/lava-referer-', '')
    return rpc_endpoint


def validate_wallet_address(wallet_address, account_dict, file_name):
    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        wallet_address = input("Invalid wallet address, try again: ")
        stop_running_check(wallet_address, account_dict, file_name)
        validate_wallet_address(wallet_address, account_dict, file_name)
        check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name)
    return wallet_address


def validate_private_key(private_key, account_dict, file_name):
    if len(private_key) != 64:
        private_key = input("Invalid private key, try again: ")
        stop_running_check(private_key, account_dict, file_name)
        validate_private_key(private_key, account_dict, file_name)
        check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name)
    return private_key


def check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name):
    if rpc_endpoint in [v["rpc_endpoint"] for v in account_dict.values()]:
        rpc_endpoint = input("Duplicate RPC endpoint, try again: ")
        stop_running_check(rpc_endpoint, account_dict, file_name)
        validate_rpc_endpoint(rpc_endpoint, account_dict, file_name)
        check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name)
    return rpc_endpoint


def check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name):
    if wallet_address in account_dict:
        wallet_address = input("Duplicate wallet address, try again: ")
        stop_running_check(wallet_address, account_dict, file_name)
        validate_wallet_address(wallet_address, account_dict, file_name)
        check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name)
    return wallet_address


def check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name):
    if private_key in [v["private_key"] for v in account_dict.values()]:
        private_key = input("Duplicate private key, try again: ")
        stop_running_check(private_key, account_dict, file_name)
        validate_private_key(private_key, account_dict, file_name)
        check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name)
    return private_key


def add_account_to_dictionary(account_dict, wallet_address, private_key, rpc_endpoint):
    account_dict[wallet_address] = {"private_key": private_key, "rpc_endpoint": rpc_endpoint}
    print(f"Account added to dictionary")


def input_new_accounts():
    create_logs_folder_if_not_existing()
    file_name = create_log_file_name()
    account_dict = {}
    count = 1
    while True:
        print(f"Account {count}:")

        # RPC endpoint
        rpc_endpoint = input("Enter the RPC endpoint: ")
        stop_running_check(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = validate_rpc_endpoint(rpc_endpoint, account_dict, file_name)
        check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name)

        # Wallet address
        wallet_address = input("Enter the wallet address: ")
        stop_running_check(wallet_address, account_dict, file_name)
        wallet_address = validate_wallet_address(wallet_address, account_dict, file_name)
        check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name)

        # Private key
        # private_key = input("Enter the private key: ")
        # stop_running_check(private_key, account_dict, file_name)
        # private_key = validate_private_key(private_key, account_dict, file_name)
        # check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name)
        private_key = "d7aa36d14d42a043718b77a747406fbfe307bbb2483d0f55bbea30ac1ddf5c1b"

        # Add account to dictionary
        add_account_to_dictionary(account_dict, wallet_address, private_key, rpc_endpoint)
        save_account_dict(account_dict, file_name)
        count += 1


def stop_running_check(user_input, account_dict, file_name):
    if user_input.lower() == 'end':
        save_account_dict(account_dict, file_name)
        exit()


input_new_accounts()