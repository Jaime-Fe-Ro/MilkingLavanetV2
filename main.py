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
    account_dictionary = user_select_account_file()
    return account_dictionary


def check_log_folder_exists():
    logs_path = os.path.join(os.getcwd(), logs_folder)
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
        account_dictionary = get_account_dictionary(selected_log)
        return account_dictionary

    else:
        print("Multiple log files found for the specified date:")
        for i in range(len(log_list)):
            print(f"{i + 1}. {log_list[i]}")
        choice = int(input("Enter the number of the file you want to choose or type 'end' to exit: "))
        choice -= 1
        try:
            if 0 <= choice < len(log_list):
                selected_log = get_account_dictionary_file_path(log_list, choice)
                account_dictionary = get_account_dictionary(selected_log)
                return account_dictionary
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
            account_dictionary = json.load(file)
            if isinstance(account_dictionary, dict):
                return account_dictionary
            else:
                print(f"Error: Unexpected data format in file '{log_path}'. Expected a dictionary.")
                return {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading account dictionary from '{log_path}': {e}")
        return {}


def get_account_dictionary_file_path(log_list, choice):
    return os.path.join(logs_path, log_list[choice])


async def run(account_dictionary):
    connector = TCPConnector(limit=100, limit_per_host=40)
    async with ClientSession(connector=connector) as session:
        while True:
            wallets_and_endpoints = get_wallets_and_endpoints(account_dictionary)

            tasks = []
            for wallet_address, rpc_endpoint in wallets_and_endpoints.items():
                tasks.append(check_wallet_balance(session, wallet_address, rpc_endpoint))
                tasks.append(check_gas_price(session, rpc_endpoint))
                tasks.append(check_block_number(session, rpc_endpoint))

            await asyncio.gather(*tasks)

def get_wallets_and_endpoints(account_dictionary):
    wallets_and_endpoints = {}
    for wallet_address, details in account_dictionary.items():
        rpc_endpoint = details.get('rpc_endpoint')
        wallets_and_endpoints[wallet_address] = rpc_endpoint
    return wallets_and_endpoints


async def check_wallet_balance(session, wallet_address, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    if result is not None and 'result' in result:
        balance = int(str(result['result']), 16) / 1e18
        print(f"Wallet balance: {balance} ETH, rpc endpoint: {rpc_endpoint}")


async def check_gas_price(session, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 2
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    if result is not None and 'result' in result:
        try:
            balance_hex = result['result']
            if isinstance(balance_hex, str):
                gas_price = int(balance_hex, 16) / 1e18
                print(f"Gas price: {gas_price} Gwei, rpc endpoint: {rpc_endpoint}")
            else:
                print(f"Unexpected data type for balance: {type(balance_hex)}. Expected a hexadecimal string.")
        except ValueError as e:
            print(f"Error converting balance: {e}")



async def check_block_number(session, rpc_endpoint):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 3
    }
    result = await fetch_data(session, payload, rpc_endpoint)
    if result is not None and 'result' in result:
        try:
            block_number = int(result['result'], 16)
            print(f"Block number: {block_number}, rpc endpoint: {rpc_endpoint}")
        except TypeError as e:
            print(f"Error converting block number: {e}")

async def fetch_data(session, payload, rpc_endpoint):
    connector = TCPConnector(limit=50, limit_per_host=25)  # rate limmiting, 50 requests per second. Otherwise crashes server
    try:
        async with session.post(rpc_endpoint, json=payload) as response:
            if response.status == 429:
                # print(f"Too Many Requests. Waiting 1 second for the server to recover. {rpc_endpoint}")
                await asyncio.sleep(1)
                return None

            if response.status != 200:
                # print(f"Error fetching data: HTTP status {response.status}. {rpc_endpoint}")
                return None

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                # print(f"Unexpected response content type: {content_type}, {rpc_endpoint}")
                return None

            return await response.json()
    except ClientOSError:
        # print(f"A network error occurred. Retrying after 1 second. {rpc_endpoint}")
        await asyncio.sleep(1)
        return await fetch_data(session, payload, rpc_endpoint)
    except Exception as e:
        # print(f"Error fetching data: {e}. {rpc_endpoint}")
        return None


def main(account_dictionary):
    print(f"Starting the program at {datetime.now()}")
    asyncio.run(run(account_dictionary))


if __name__ == "__main__":
    account_dictionary = startup()
    main(account_dictionary)
