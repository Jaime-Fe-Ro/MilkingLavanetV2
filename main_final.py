import aiohttp
import asyncio
import json
import os
import random
from datetime import datetime

logs_folder = 'logs'

def get_protocol_choice():
    while True:
        protocol_choice = input("Choose the protocol: 1. Ethereum  2. Near Protocol: ")
        if protocol_choice == '1' or protocol_choice == '2':
            return protocol_choice
        else:
            print("Invalid choice. Please choose 1 for Ethereum or 2 for Near Protocol.")

def list_log_files():
    logs_path = os.path.join(os.getcwd(), logs_folder)
    if not os.path.exists(logs_path):
        print(f"Logs folder '{logs_folder}' does not exist.")
        return None

    print("Available log files:")
    log_files = [file for file in os.listdir(logs_path) if file.startswith("dictionary_") and file.endswith(".json")]
    for i, file in enumerate(log_files, start=1):
        print(f"{i}. {file}")
    return log_files

def get_dictionary_file(date_str, log_files):
    if not log_files:
        return None

    if date_str.lower() == 'today':
        date_str = datetime.today().strftime('%d-%m-%Y')

    matching_files = [file for file in log_files if date_str in file]

    if not matching_files:
        print("No matching log files found.")
        return None

    if len(matching_files) == 1:
        return matching_files[0]
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
                return matching_files[index]
            else:
                print("Invalid choice.")
                return None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None


def load_account_dict(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
            else:
                print(f"Error: Unexpected data format in file '{file_path}'. Expected a dictionary.")
                return {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading account dictionary from '{file_path}': {e}")
        return {}


async def main():
    protocol_choice = get_protocol_choice()
    if protocol_choice == '1':
        rpc_prefix = "https://eth1.lava.build/lava-referer-"
        eth_rpc = True
    elif protocol_choice == '2':
        rpc_prefix = "https://near.lava.build/lava-referer-"
        eth_rpc = False

    log_files = list_log_files()
    if not log_files:
        return

    date_str = input("Enter 'today' to use logs from today or specify the date in DD-MM-YYYY format: ")
    if date_str.lower() == 'end':
        return

    dictionary_file = get_dictionary_file(date_str, log_files)
    if not dictionary_file:
        print("No valid log file found.")
        return

    account_dict = load_account_dict(os.path.join(os.getcwd(), logs_folder, dictionary_file))
    if not account_dict:
        print("Account dictionary is empty.")
        return

    request_count = 0
    requests_per_random_account = 30
    selected_entry = random.choice(list(account_dict.items()))
    print(f"Selected entry: {selected_entry}")

    async with aiohttp.ClientSession() as session:
        wallet_index = 1
        cycle_count = 0
        while True:
            wallet_address, data = selected_entry
            rpc_endpoint = data['rpc_endpoint']
            if eth_rpc:
                full_rpc_endpoint = rpc_prefix + rpc_endpoint
                results = await asyncio.gather(
                    check_wallet_balance_eth(session, wallet_address, full_rpc_endpoint),
                    check_gas_price_eth(session, full_rpc_endpoint),
                    check_block_number_eth(session, full_rpc_endpoint)
                )
            else:
                full_rpc_endpoint = rpc_prefix + rpc_endpoint
                results = await asyncio.gather(
                    check_wallet_balance_near(session, "ironar.near", full_rpc_endpoint)
                )

            request_count += 1
            if request_count >= requests_per_random_account:
                print("Changing the account and RPC endpoint pair due to request count limit reached.")
                wallet_index += 1
                if wallet_index > len(account_dict):
                    wallet_index = 1  # Reset to 1 if the index exceeds the total number of wallets
                    cycle_count += 1
                    print(f"Completed {cycle_count} cycles through the entire list of wallets.")
                selected_entry = list(account_dict.items())[wallet_index - 1]
                print(f"New selected entry: Wallet {wallet_index} ({selected_entry[0]})")
                request_count = 0
            else:
                print(" -- Batch Successful -- ")


async def check_wallet_balance_eth(session, wallet_address, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    return result


async def check_gas_price_eth(session, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 2
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    return result


async def check_block_number_eth(session, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 3
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    return result


async def check_wallet_balance_near(session, wallet_address, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "query",
        "params": {"request_type": "view_account", "account_id": wallet_address},
        "id": 1
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    return result


async def fetch_data(session, payload, rpc_endpoint):
    try:
        async with session.post(rpc_endpoint, json=payload) as response:
            if response.status == 429:
                print("Too Many Requests. Waiting for the server to recover.")
                await asyncio.sleep(1)  # Wait for 1 second before retrying
                return None

            if response.status != 200:
                print(f"Error fetching data: HTTP status {response.status}")
                return None

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                print(f"Unexpected response content type: {content_type}")
                return None

            return await response.json()
    except aiohttp.ClientOSError:
        print("A network error occurred. Retrying after 1 second...")
        await asyncio.sleep(1)
        return await fetch_data(session, payload, rpc_endpoint)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


if __name__ == "__main__":
    print("Running main")
    asyncio.run(main())
