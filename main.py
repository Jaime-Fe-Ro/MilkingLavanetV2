from aiohttp import TCPConnector, ClientSession, ClientOSError

import asyncio
import json
import os
from datetime import datetime

logs_folder = 'logs'
logs_path = os.path.join(os.getcwd(), logs_folder)
today = datetime.today().strftime('%d-%m-%Y')


def startup():
    check_log_folder_exists()
    account_dictionary_file = user_select_account_file()
    return account_dictionary_file


def check_log_folder_exists():
    if not os.path.exists(logs_path):
        print(f"Logs folder '{logs_folder}' does not exist.")
        exit()


def user_select_account_file():
    selected_day = input("Enter 'today' to use logs from today or specify the date in DD-MM-YYYY format: ")
    if selected_day.lower() == 'today':
        selected_day = today

    validate_selected_date_format(selected_day)
    log_list = get_account_dictionary_list_for_selected_date(selected_day)

    if len(log_list) == 0:
        print(f"No log files found for {selected_day}, check logs and run the program again")
        exit()

    elif len(log_list) == 1:
        selected_log = get_account_dictionary_file_path(log_list, 0)
        dictionary = get_account_dictionary(selected_log)
        return dictionary

    else:
        print("Multiple log files found for the specified date:")
        for i in range(len(log_list)):
            print(f"{i + 1}. {log_list[i]}")
        choice = int(input("Enter the number of the file you want to choose or type 'end' to exit: "))
        choice -= 1
        try:
            if 0 <= choice < len(log_list):
                selected_log = get_account_dictionary_file_path(log_list, choice)
                dictionary = get_account_dictionary(selected_log)
                return dictionary
            else:
                print("Invalid choice, run the program again and select a valid file.")
                exit()
        except ValueError:
            print("Invalid input format, run the program again and select a valid file.")
            exit()


def validate_selected_date_format(selected_date):
    try:
        datetime.strptime(selected_date, '%d-%m-%Y')
    except ValueError:
        print("Invalid date format. Run the program again and enter a valid date in DD-MM-YYYY format")
        exit()


def get_account_dictionary_list_for_selected_date(selected_date):
    matching_files = []
    for file in os.listdir(logs_path):
        if file.startswith("dictionary_") and file.endswith(".json"):
            if selected_date in file:
                matching_files.append(file)
    return matching_files


def get_account_dictionary(log_path):
    try:
        with open(log_path, 'r') as file:
            dictionary = json.load(file)
            if isinstance(dictionary, dict):
                return dictionary
            else:
                print(f"Error: Unexpected data format in file '{log_path}'. Expected a dictionary.")
                return {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading account dictionary from '{log_path}': {e}")
        return {}


def get_account_dictionary_file_path(log_list, choice):
    return os.path.join(logs_path, log_list[choice])


async def run(dictionary_file, started_at):
    connector = TCPConnector(limit=10, limit_per_host=1)
    wallets_and_endpoints = get_wallets_and_endpoints(dictionary_file)
    loop_counter = 0
    success_counter = {'count': 0}
    async with ClientSession(connector=connector) as session:
        while True:
            tasks = []
            print(f"\nStarting loop {loop_counter + 1}")
            for wallet_address, rpc_endpoint in wallets_and_endpoints.items():
                tasks.append(check_wallet_balance(session, wallet_address, rpc_endpoint, success_counter))
                tasks.append(check_gas_price(session, rpc_endpoint, success_counter, wallet_address))
                tasks.append(check_block_number(session, rpc_endpoint, success_counter, wallet_address))
            await asyncio.gather(*tasks)
            loop_counter += 1
            print(f"Finished loop {loop_counter}\n")
            print("Totals:")
            running_for = datetime.now() - started_at
            print(f"{success_counter['count']} successful requests")
            running_time = round(running_for.total_seconds(), 1)
            print(f"{running_time} seconds of running")
            avg_requests_per_sec = round(success_counter['count'] / running_for.total_seconds(), 1)
            print(f"{avg_requests_per_sec} average requests per second")
            avg_requests_per_wallet = round(success_counter['count'] / len(wallets_and_endpoints))
            print(f"{avg_requests_per_wallet} requests per wallet")


def get_wallets_and_endpoints(selected_account_dictionary):
    wallets_and_endpoints = {}
    for wallet_address, details in selected_account_dictionary.items():
        rpc_endpoint = details.get('rpc_endpoint')
        wallets_and_endpoints[wallet_address] = rpc_endpoint
    return wallets_and_endpoints


async def check_wallet_balance(session, wallet_address, rpc_endpoint, success_counter):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address)
    if result is not None and 'result' in result:
        try:
            balance = int(str(result['result']), 16) / 1e18
            print(f"{wallet_address} -> balance: {balance} ETH")
            success_counter['count'] += 1
        except ValueError as e:
            print(f"Error converting balance: {e}")


async def check_gas_price(session, rpc_endpoint, success_counter, wallet_adress):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 2}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_adress)
    if result is not None and 'result' in result:
        try:
            balance_hex = result['result']
            if isinstance(balance_hex, str):
                gas_price = int(balance_hex, 16) / 1e18
                print(f"{wallet_adress} -> gas price: {gas_price} Gwei")
                success_counter['count'] += 1
            else:
                print(f"Unexpected data type for balance: {type(balance_hex)}. Expected a hexadecimal string.")
        except ValueError as e:
            print(f"Error converting balance: {e}")


async def check_block_number(session, rpc_endpoint, success_counter, wallet_adress):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 3}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_adress)
    if result is not None and 'result' in result:
        try:
            block_number = int(result['result'], 16)
            print(f"{wallet_adress} -> block number: {block_number}")
            success_counter['count'] += 1
        except TypeError as e:
            print(f"Error converting block number: {e}")


async def fetch_data(session, payload, rpc_endpoint, wallet_address):
    try:
        async with session.post(rpc_endpoint, json=payload) as response:
            if response.status == 429:
                print(f"ERROR. Too Many Requests. Waiting 1 second for the server to recover. {wallet_address}")
                await asyncio.sleep(1)
                return await fetch_data(session, payload, rpc_endpoint, wallet_address)

            if response.status != 200:
                print(f"ERROR. Error fetching data: HTTP status {response.status}. {wallet_address}")
                return await fetch_data(session, payload, rpc_endpoint, wallet_address)

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                print(f"ERROR. Unexpected response content type: {content_type}, {wallet_address}")
                return await fetch_data(session, payload, rpc_endpoint, wallet_address)

            return await response.json()
    except ClientOSError:
        print(f"ERROR. A network error occurred. Retrying after 1 second. {wallet_address}")
        await asyncio.sleep(1)
        return await fetch_data(session, payload, rpc_endpoint, wallet_address)
    except Exception as e:
        print(f"ERROR. Error fetching data: {e}. {wallet_address}")
        return await fetch_data(session, payload, rpc_endpoint, wallet_address)


def main(loaded_account_dictionary):
    starting = datetime.now()
    print(f"Starting the program at {starting}")
    asyncio.run(run(loaded_account_dictionary, starting))


if __name__ == "__main__":
    account_dictionary = startup()
    main(account_dictionary)
