from aiohttp import TCPConnector, ClientSession, ClientOSError
import sys
import asyncio
import json
import os
from datetime import datetime

logs_folder = 'logs'
logs_path = os.path.join(os.getcwd(), logs_folder)
today = datetime.today().strftime('%d-%m-%Y')


def get_time_now():
    return datetime.now().strftime('%d-%m-%Y %H-%M-%S')


def log_setup():
    main_log_folder = 'main_logs'
    main_logs_path = os.path.join(os.getcwd(), main_log_folder)
    if not os.path.exists(main_logs_path):
        os.makedirs(main_logs_path)
    log_file_name = f"log_{get_time_now()}.txt"
    main_logs_file_path = os.path.join(main_logs_path, log_file_name)
    return main_logs_file_path


class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


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
        print("Selected log file:", selected_log)
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
                print("Selected log file:", selected_log)
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


async def run(dictionary_file, started_at, eth):
    connector = TCPConnector(limit=10, limit_per_host=1)
    wallets_and_endpoints = get_wallets_and_endpoints(dictionary_file)
    loop_counter = 0
    success_counter = {'count': 0}
    async with ClientSession(connector=connector) as session:
        while loop_counter <= 2:
            if eth:
                # tasks = []
                # print(f"\nStarting loop {loop_counter + 1}")
                # for wallet_index, (wallet_address, rpc_endpoint) in enumerate(wallets_and_endpoints.items()):
                #     tasks.append(check_wallet_balance(session, wallet_address, rpc_endpoint, success_counter, wallet_index))
                #     tasks.append(check_gas_price(session, rpc_endpoint, success_counter, wallet_address, wallet_index))
                #     tasks.append(check_block_number(session, rpc_endpoint, success_counter, wallet_address, wallet_index))
                # await asyncio.gather(*tasks)
                # loop_counter += 1
                # print(f"Finished loop {loop_counter}\n")
                # print("Totals:")
                # running_for = datetime.now() - started_at
                # print(f"{success_counter['count']} successful requests")
                # running_time = round(running_for.total_seconds(), 1)
                # print(f"{running_time} seconds of running")
                # avg_requests_per_sec = round(success_counter['count'] / running_for.total_seconds(), 1)
                # print(f"{avg_requests_per_sec} average requests per second")
                # avg_requests_per_wallet = round(success_counter['count'] / len(wallets_and_endpoints))
                # print(f"{avg_requests_per_wallet} requests per wallet")
                print("You fucked up")
            else:
                tasks = []
                print(f"\nStarting loop {loop_counter + 1}")
                for wallet_index, (wallet_address, rpc_endpoint) in enumerate(wallets_and_endpoints.items()):
                    tasks.append(check_status_near(session, rpc_endpoint, success_counter, wallet_address, wallet_index))
                    tasks.append(check_wallet_balance_near(session, "ironar.near", rpc_endpoint, success_counter, wallet_address, wallet_index))
                await asyncio.gather(*tasks)
                loop_counter += 1
                print(f"Finished loop {loop_counter}\n")
                print("Totals:")
                print(f"{success_counter['count']} successful requests")
                print(f"{round((datetime.now() - started_at).total_seconds(), 1)} seconds of running")
                print(f"{round(success_counter['count'] / (datetime.now() - started_at).total_seconds(), 1)} average requests per second")
                print(f"{round(success_counter['count'] / len(wallets_and_endpoints))} requests per wallet")


def get_wallets_and_endpoints(selected_account_dictionary):
    wallets_and_endpoints = {}
    for wallet_address, details in selected_account_dictionary.items():
        rpc_endpoint = details.get('rpc_endpoint')
        wallets_and_endpoints[wallet_address] = rpc_endpoint
    return wallets_and_endpoints


async def check_wallet_balance(session, wallet_address, rpc_endpoint, success_counter, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            balance = int(str(result['result']), 16) / 1e18
            print(f"{wallet_index + 1}: {wallet_address} -> balance: {balance} ETH")
            success_counter['count'] += 1
        except Exception as e:
            print(f"Error converting balance: {e}")


async def check_gas_price(session, rpc_endpoint, success_counter, wallet_address, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 2}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            balance_hex = result['result']
            if isinstance(balance_hex, str):
                gas_price = int(balance_hex, 16) / 1e18
                print(f"{wallet_index + 1}: {wallet_address} -> gas price: {gas_price} Gwei")
                success_counter['count'] += 1
            else:
                print(f"Unexpected data type for balance: {type(balance_hex)}. Expected a hexadecimal string.")
        except Exception as e:
            print(f"Error converting balance: {e}")


async def check_block_number(session, rpc_endpoint, success_counter, wallet_address, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 3}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            block_number = int(result['result'], 16)
            print(f"{wallet_index + 1}: {wallet_address} -> block number: {block_number}")
            success_counter['count'] += 1
        except Exception as e:
            print(f"Error converting block number: {e}")


async def check_wallet_balance_near(session, account_id, rpc_endpoint, success_counter, wallet_address, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "query",
        "params": {
            "request_type": "view_account",
            "finality": "final",
            "account_id": account_id
        },
        "id": 1}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            balance = str(result['result']['amount'])
            print(f"{wallet_index + 1}: {wallet_address} -> balance: {balance} ETH")
            success_counter['count'] += 1
        except Exception as e:
            print(f"Error converting balance: {e}")


async def check_status_near(session, rpc_endpoint, success_counter, wallet_address, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "status",
        "params": {},
        "id": 2}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            print(f"{wallet_index + 1}: {wallet_address} -> Checked network status")
            success_counter['count'] += 1
        except Exception as e:
            print(f"Error converting status: {e}")


async def fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index):
    try:
        async with session.post(rpc_endpoint, json=payload) as response:
            if response.status == 429:
                print(f"ERROR. Too Many Requests. Waiting 1 second for the server to recover. {wallet_index + 1}: {wallet_address}")
                await asyncio.sleep(1)
                return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)

            if response.status != 200:
                print(f"ERROR. Error fetching data: HTTP status {response.status}. {wallet_index + 1}: {wallet_address}")
                return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                print(f"ERROR. Unexpected response content type: {content_type}, {wallet_index + 1}: {wallet_address}")
                return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)

            return await response.json()
    except ClientOSError:
        print(f"ERROR. A network error occurred. Retrying after 1 second. {wallet_index + 1}: {wallet_address}")
        await asyncio.sleep(1)
        return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    except Exception as e:
        print(f"ERROR. Error fetching data: {e}. {wallet_index + 1}: {wallet_address}")
        return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)


def get_protocol_choice_and_modify_account_dictionary(final_account_dictionary):
    while True:
        protocol_choice = input(" - Input protocol number - \n1. Ethereum  \n2. Near Protocol\n-> ")
        if protocol_choice == '1':
            rpc_eth = True
            print("Ethereum protocol selected")
            return final_account_dictionary, rpc_eth

        elif protocol_choice == '2':
            rpc_prefix = "https://near.lava.build/lava-referer-"
            print("Near protocol selected")
            rpc_eth = False
            for address, info in final_account_dictionary.items():
                rpc_endpoint = info.get('rpc_endpoint')
                if rpc_endpoint.startswith('https://eth1.lava.build/lava-referer-'):
                    info['rpc_endpoint'] = rpc_endpoint.replace('https://eth1.lava.build/lava-referer-', rpc_prefix)
            return final_account_dictionary, rpc_eth


if __name__ == "__main__":
    log_file_path = log_setup()
    sys.stdout = Logger(log_file_path)
    account_dictionary = startup()
    modified_account_dictionary, eth_rpc = get_protocol_choice_and_modify_account_dictionary(account_dictionary)
    starting = datetime.now()
    print(f"Starting the program at {starting}")
    asyncio.run(run(modified_account_dictionary, starting, eth_rpc))
