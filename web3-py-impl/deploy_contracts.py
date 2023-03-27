# import sys
# import time
# import pprint
import os
# import subprocess
# from subprocess import PIPE, Popen
# import glob
import json

import web3.logs
#
# import solcx
from web3.providers import HTTPProvider
from web3 import Web3
import matplotlib.pyplot as plt
import numpy as np

import importlib.util
file_path = '/Users/royshadmon/Web3-Ethereum-Interface/src/web3_eth.py'

# Specify the module name
module_name = 'Web3_Eth'

# Load the module from the file path
spec = importlib.util.spec_from_file_location(module_name, file_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_contract_abi_bin(root_directory, contract_name, solidity_version="0.8.17"):
    with open(
        os.path.join(root_directory, f"contracts/compiled_contracts/{solidity_version}/{contract_name}/{contract_name}.abi")) as f:

        abi = f.read()
    with open(
        os.path.join(root_directory, f"contracts/compiled_contracts/{solidity_version}/{contract_name}/{contract_name}.bin")) as f:

        bin = f.read()
    return abi, bin


def compile_contract(web3_interface, root_dir, contract_name, output_dir=None, solidity_version="0.8.17"):
    contract_path = os.path.join(root_dir, f"contracts/{contract_name}")
    contract_name = contract_name.split('.')[0]
    if not output_dir:
        output_dir = os.path.join(root_dir, f"contracts/compiled_contracts/{solidity_version}/{contract_name}")

    id, interface = web3_interface.compile_contract(contract_path, output_dir, solidity_version)
    return id, interface

# self.connection.eth.contract(address=contract_address, abi=abi_)
def get_contract_instance(web3_interface, contract_addr, abi):

    contract_instance = web3_interface.w3.eth.contract(address=web3_interface.toCheckSumAddress(contract_addr), abi=abi)
    return contract_instance


def deploy_contract(web3_interface, contract_name, account_addr, private_key, solidity_version="0.8.17"):
    abi, bin = load_contract_abi_bin(contract_name, solidity_version)
    if web3_interface.verify_acct_addr_matches_p_key(account_addr, private_key):
        contract_address = web3_interface.deploy_contract(abi, bin, private_key, account_addr)
    else:
        print(f"Account address does not match private key")
        exit(-1)
    return contract_address

def submit_transaction(web3_interface, transaction, private_key):
    signed_tx = web3_interface.signTransaction(transaction, private_key=private_key)
    tx_hash = web3_interface.sendRawTransaction(signed_tx)
    tx_receipt = web3_interface.waitForTransactionReceipt(tx_hash)
    return tx_receipt


def main():
    # Get the directory where the current Python script is located
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # Get the root directory of the project (assuming the root directory is the parent directory of the script directory)
    root_directory = os.path.dirname(script_directory)
    ganache_url = "http://127.0.0.1:8545"
    web3_interface = module.Web3_Eth(ganache_url)

    # acct_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"
    # user_private_key = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"

    # Get Private Keys
    with open(os.path.join(root_directory, "eth_accounts/keys.json")) as f:
        private_keys = f.read()
        private_keys = json.loads(private_keys)['private_keys']

    private_keys_list = list(private_keys.values())

    user_private_key = private_keys_list[0]
    acct_address = web3_interface.get_eth_user(user_private_key).address


    print(web3_interface.w3.is_connected())

    # # Compile Contracts
    publisher_id, publisher_interface = compile_contract(web3_interface, root_directory, "Publisher.sol")
    id, interface = compile_contract(web3_interface, root_directory, "PubSubService.sol")
    subscriber_id, subscriber_interface = compile_contract(web3_interface, root_directory, "Subscriber.sol")

    notify_add_cost = []
    notify_remove_cost = []

    for i in range(1, len(private_keys_list)):
        publisher_addr, publisher_contract = web3_interface.deploy_contract(publisher_interface, user_private_key)
        print(f"PUBLISHER ADDRESS {web3_interface.toCheckSumAddress(publisher_addr)}")

        pubsub_addr, pubsub_contract = web3_interface.deploy_contract(interface, user_private_key)

        # Publisher register to PubSubService
        transaction = publisher_contract.functions.registerToPubSubService(pubsub_addr).build_transaction(
            {
                'from': acct_address,
                'chainId': 1337,  # Ganache chain id
                'nonce': web3_interface.w3.eth.get_transaction_count(acct_address),
                # 'value': 0,
            }
        )
        tx_receipt = submit_transaction(web3_interface, transaction, private_key=user_private_key)

        # Get event manager contract address
        em_addr = publisher_contract.events.EM_CREATED().process_receipt(tx_receipt)[0].args.em_addr
        print(f"EVENT MANAGER {em_addr}")

        # Deploy Subscribers
        for p_key in private_keys_list[:i]:
            user = web3_interface.get_eth_user(p_key)
            subscriber_addr, subscriber_contract = web3_interface.deploy_contract(subscriber_interface, p_key, publisher_addr, pubsub_addr, 100000010101, value=100000010101)
            print(f'SUBSCRIBER_ADDR {subscriber_addr}')


        # Add to blacklist


        user = web3_interface.get_eth_user(p_key)
        print(f'ADDING {web3_interface.toCheckSumAddress(user.address)}')
        transaction = publisher_contract.functions.addToBlackList(web3_interface.toCheckSumAddress(user.address)).build_transaction({
            'from': web3_interface.toCheckSumAddress(user.address),
            'chainId': 1337,  # Ganache chain id
            'nonce': web3_interface.getTransactionCount(user),
        })
        tx_receipt = submit_transaction(web3_interface, transaction, p_key)
        print(f"TX_RECEIPT")
        print(f"=======================")
        notify_add_cost.append(publisher_contract.events.GAS_COST().process_receipt(tx_receipt, errors=web3.logs.DISCARD)[0].args.gas) # Discarding warnings due to "MismatchedABI(The event signature did not match the provided ABI)". Reason from https://github.com/oceanprotocol/ocean.py/issues/348


        # Remove single element from blacklist

        print(f'REMOVING {web3_interface.toCheckSumAddress(user.address)}')


        transaction = publisher_contract.functions.removeFromBlackList(web3_interface.toCheckSumAddress(user.address)).build_transaction({
            'from': web3_interface.toCheckSumAddress(user.address),
            'chainId': 1337,  # Ganache chain id
            'nonce': web3_interface.getTransactionCount(user),
        })
        tx_receipt = submit_transaction(web3_interface, transaction, p_key)
        print(f"TX_RECEIPT")
        print(f"=======================")
        notify_remove_cost.append(publisher_contract.events.GAS_COST().process_receipt(tx_receipt, errors=web3.logs.DISCARD)[0].args.gas)

    plt.plot(np.arange(1, len(notify_add_cost) + 1), notify_add_cost)
    plt.title(f"Gas cost adding to blacklist")
    plt.xlabel("Number of subscribers to notify")
    plt.ylabel("Gas cost (Wei)")
    plt.show()
    print(notify_add_cost)

    plt.plot(np.arange(1, len(notify_remove_cost) + 1), notify_remove_cost)
    plt.title(f"Gas cost removing from blacklist starting with {len(notify_remove_cost)} items")
    plt.xlabel("Number of subscribers to notify")
    plt.ylabel("Gas cost (Wei)")
    plt.show()
    exit(-1)




if __name__ == "__main__":
    main()