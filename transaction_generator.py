import numpy as np

transactions = 100


def generate_eth_transaction_quantity():
    # Generate transaction values from a combination of two distributions
    value_low = np.random.lognormal(mean=0.5, sigma=0.5)
    value_high = np.random.lognormal(mean=2.5, sigma=1.0)
    value = np.concatenate((value_low, value_high))
    # Clip values to ensure they are within the desired range [0.2, 134]
    value = np.clip(value, 0.2, 134)
    # Shuffle the values
    np.random.shuffle(value)
    # Round values to six decimal places
    eth_transferred = np.round(value, decimals=6)
    return eth_transferred


print(generate_eth_transaction_quantity())
