import aiohttp
import asyncio
import json
import random

account_dict_file = 'account_dict.json'
transaction_pairs_file = 'eth_transaction_pairs.json'


def load_account_dict():
    try:
        with open(account_dict_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading account dictionary: {e}")
        return {}


def load_transaction_pairs():
    try:
        with open(transaction_pairs_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading transaction pairs: {e}")
        return []


async def main():
    account_dict = load_account_dict()
    transaction_pairs = load_transaction_pairs()

    if not account_dict:
        print("Account dictionary is empty.")
        return

    if not transaction_pairs:
        print("Transaction pairs are empty.")
        return

    requests_per_random_account = 3

    async with aiohttp.ClientSession() as session:
        for wallet_address, rpc_endpoint in account_dict.items():
            private_key = account_dict[wallet_address].get('private_key')
            if private_key:
                print(f"Selected entry: {wallet_address}: {rpc_endpoint}")

                # Retrieve a random transaction pair
                transaction_pair = random.choice(transaction_pairs)
                eth_value = transaction_pair['transaction_value_eth']
                gas_limit = transaction_pair['gas_limit']
                gas_price = transaction_pair['gas_price_gwei']

                # Perform the transaction RPC call
                result = await perform_transaction(session, wallet_address, private_key, rpc_endpoint, eth_value,
                                                   gas_limit, gas_price)

                if result:
                    print(f"Transaction successful: {result}")
                else:
                    print("Transaction failed.")
            else:
                print(f"No private key found for wallet address: {wallet_address}")


async def perform_transaction(session, wallet_address, private_key, rpc_endpoint, eth_value, gas_limit, gas_price):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_sendTransaction",
        "params": [{
            "from": wallet_address,
            "to": "0xC0Fe952E091bbe17A617daD4883b0cE0B6ce72bA",  # Specify the recipient address
            "value": hex(int(eth_value * 1e18)),  # Convert ETH value to Wei
            "gas": hex(gas_limit),
            "gasPrice": hex(gas_price * 1e9)  # Convert Gwei to Wei
        }],
        "id": 1
    }

    headers = {
        'Content-Type': 'application/json',
    }

    auth = aiohttp.BasicAuth(wallet_address, private_key)

    async with session.post(rpc_endpoint, json=payload, headers=headers, auth=auth) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Transaction failed with status code: {response.status}")
            return None


# Remaining functions remain the same...

if __name__ == "__main__":
    print("Running main")
    asyncio.run(main())
