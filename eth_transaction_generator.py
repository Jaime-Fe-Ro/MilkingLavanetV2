import json
import random
import numpy as np

def generate_transaction_values(num_values):
    # Generate transaction values from a combination of two distributions
    values_low = np.random.lognormal(mean=0.5, sigma=0.5, size=int(0.9*num_values))
    values_high = np.random.lognormal(mean=2.5, sigma=1.0, size=int(0.1*num_values))
    values = np.concatenate((values_low, values_high))
    # Clip values to ensure they are within the desired range [0.2, 134]
    values = np.clip(values, 0.2, 134)
    # Shuffle the values
    np.random.shuffle(values)
    # Round values to six decimal places
    values = np.round(values, decimals=6)
    return list(values)

def generate_gas_limits(num_limits):
    # Generate gas limits ranging from 768,000 to 1,232,680
    return [random.randint(768000, 1232680) for _ in range(num_limits)]

def generate_gas_prices(num_prices):
    # Generate gas prices ranging from 70 to 110 Gwei
    return [random.randint(70, 110) for _ in range(num_prices)]

def generate_pairs(num_pairs):
    transaction_values = generate_transaction_values(num_pairs)
    gas_limits = generate_gas_limits(num_pairs)
    gas_prices = generate_gas_prices(num_pairs)

    # Create pairs
    pairs = [{"transaction_value_eth": value, "gas_limit": limit, "gas_price_gwei": price} for value, limit, price in zip(transaction_values, gas_limits, gas_prices)]
    return pairs

if __name__ == "__main__":
    num_pairs = 1000
    pairs = generate_pairs(num_pairs)

    # Save pairs to a JSON file
    with open('eth_transaction_pairs.json', 'w') as f:
        json.dump(pairs, f, indent=4)
        print(f"Saved {num_pairs} transaction pairs to eth_transaction_pairs.json")