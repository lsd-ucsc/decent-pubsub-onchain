# import sys
# import time
# import pprint
import os
# import subprocess
# from subprocess import PIPE, Popen
# import glob
import json
#
# import solcx
from web3.providers import HTTPProvider
from web3 import Web3

import importlib.util
file_path = '/Users/royshadmon/Web3-Ethereum-Interface/src/web3_eth.py'

# Specify the module name
module_name = 'Web3_Eth'

# Load the module from the file path
spec = importlib.util.spec_from_file_location(module_name, file_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# deploy ganache
# ganache-cli -d -a 10 --miner.callGasLimit 30000000000 --miner.blockGasLimit 30000000000 --miner.defaultGasPrice 10000000000 --logging.debug true



# def deploy_contract(w3, abi, bin, constructor_params=None):
#     Contract = w3.eth.contract(abi=abi, bytecode=bin)
#
#     transaction = Contract.constructor().buildTransaction({
#         'from': w3.eth.accounts[0],
#         'nonce': w3.eth.getTransactionCount(w3.eth.accounts[0]),
#         'gas': 2000000,
#         'gasPrice': w3.toWei('50', 'gwei')
#     })
#
#     sender_account = w3.eth.account.privateKeyToAccount("0x4d81c18f65ac69928410139ec72d7e7fe6bf044fb8899e2bedc7fbff49db3c1f")
#     signed_tx = sender_account.sign_transaction(transaction)
#
#     tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
#
#     tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
#     contract_address = tx_receipt.contractAddress
#     return contract_address
#
#
# def compile_contract(contract_name, solidity_version):
#     contract_path = os.path.join(root_directory, f"contracts/{contract_name}")
#     contract_name = contract_name.split('.')[0]
#     output_dir = os.path.join(root_directory, f"contracts/compiled_contracts/{solidity_version}/{contract_name}")
#     # Run the javascript compile contract command
#     # base_path = contract_path.split(contract_name)[0]
#     compile_command = f"solcjs --bin --abi {contract_path} --output-dir {output_dir}"
#
#
#     print(compile_command.strip())
#     p = Popen(compile_command.strip(), shell=True)
#     p.communicate()
#
#     # Remove the interface files
#     keyword = "Interface"
#     file_list = glob.glob(os.path.join(output_dir, f"*{keyword}*"))
#     for file_path in file_list:
#         os.remove(file_path)
#
#     # Rename files
#     for filename in os.listdir(output_dir):
#         if filename.split('.')[-1] == 'bin':
#             os.rename(os.path.join(output_dir,filename), os.path.join(output_dir,f'{contract_name}.bin'))
#         elif filename.split('.')[-1] == 'abi':
#             os.rename(os.path.join(output_dir,filename), os.path.join(output_dir,f'{contract_name}.abi'))
#
#
# def get_contract_abi_bin(contract_name, solidity_version):
#     name = contract_name.split(".")[0]
#     with open( os.path.join(root_directory, f"contracts/compiled_contracts/{solidity_version}/{name}_sol_{name}.abi")) as f:
#         abi = f.read()
#     with open( os.path.join(root_directory, f"contracts/compiled_contracts/{solidity_version}/{name}_sol_{name}.bin")) as f:
#         bin = f.read()
#
#     return abi, bin


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

    contract_instance = web3_interface.w3.eth.contract(address=web3_interface.w3.to_checksum_address(contract_addr), abi=abi)
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

    acct_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"
    user_private_key = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
    print(web3_interface.w3.is_connected())

    # # Compile Contracts
    publisher_id, publisher_interface = compile_contract(web3_interface, root_directory, "Publisher.sol")
    publisher_addr, publisher_contract = web3_interface.deploy_contract(publisher_interface, user_private_key)

    id, interface = compile_contract(web3_interface, root_directory, "PubSubService.sol")
    pubsub_addr, pubsub_contract = web3_interface.deploy_contract(interface, user_private_key)
    # id, interface = compile_contract(web3_interface, root_directory, "EventManager.sol")
    subscriber_id, subscriber_interface = compile_contract(web3_interface, root_directory, "Subscriber.sol")


    transaction = publisher_contract.functions.registerToPubSubService(pubsub_addr).build_transaction(
        {
            'chainId': 1337,  # Ganache chain id
            'nonce': web3_interface.w3.eth.get_transaction_count(acct_address),
            # 'value': 0,
        }
    )

    tx_receipt = submit_transaction(web3_interface, transaction, private_key=user_private_key)

    print(f'HERERE {tx_receipt}')
    # Get event manager contract address
    em_addr = publisher_contract.events.EM_CREATED().process_receipt(tx_receipt)[0].args.em_addr
    print(f"EVENT MANAGER {em_addr}")

    # print(publisher_contract.events.EM_CREATED().process_receipt(tx_receipt))

    # Deploy Subscriber

    subscriber_addr, subscriber_contract = web3_interface.deploy_contract(subscriber_interface, user_private_key, publisher_addr, pubsub_addr, 100000010101, value=100000010101)
    print(f'SUBSCRIBER_ADDR {subscriber_addr}')

    # new_user_private_key = '0x6cbed15c793ce57650b9877cf6fa156fbef513c4e6134f022a85b1ffdd59b2a1'
    # new_user_public_key = '0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0'
    transaction = publisher_contract.functions.addToBlackList('0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1').build_transaction({
        'chainId': 1337,  # Ganache chain id
        'nonce': web3_interface.w3.eth.get_transaction_count(acct_address),
    })
    tx_receipt = submit_transaction(web3_interface, transaction, private_key=user_private_key)
    print(f'{tx_receipt}')
    exit(-1)


    # deploy_contract(self, abi, bin, account_private_key, account_addr=None, constructor_params=None):
    # publisher_abi, publisher_bin = load_contract_abi_bin(root_directory, "Publisher", "0.8.17")
    # Publisher_addr = web3_interface.deploy_contract(publisher_abi, publisher_bin, user_private_key, acct_address)
    pubsub_abi, pubsub_bin = load_contract_abi_bin(root_directory, "PubSubService", "0.8.17")
    PubSub_addr = web3_interface.deploy_contract(pubsub_abi, pubsub_bin, user_private_key, acct_address)
    print(f"Publisher {Publisher_addr}")
    print(f"PubSub {PubSub_addr}")

    # publisher_contract = get_contract_instance(web3_interface, Publisher_addr, publisher_abi)
    contract = web3_interface.w3.eth.contract(Publisher_addr, abi=publisher_abi)

    user = web3_interface.get_eth_user(user_private_key)
    nonce = web3_interface.getTransactionCount(user)
    gas_limit = 3000000000

    web3_interface.w3.eth.default_account = web3_interface.w3.eth.accounts[0]


    a = contract.functions.getContractBalance().call()
    print(f"A {a}")

    contract = web3_interface.w3.eth.contract(web3_interface.w3.to_checksum_address(PubSub_addr), abi=pubsub_abi)

    transaction = contract.functions.register().build_transaction(
        {
            'gas': 10000000,     # 3172000
            'chainId': 1337,  # Ganache chain id
            'gasPrice': int(web3_interface.w3.eth.gas_price),
            'nonce': web3_interface.getTransactionCount(user),
            # 'value': 0,
        }
    )

    # transaction = contract.functions.registerToPubSubService(PubSub_addr).build_transaction(
    #     {
    #         # 'gas': 10000000,     # 3172000
    #         'chainId': 1337,  # Ganache chain id
    #         # 'gasPrice': int(web3_interface.w3.eth.gas_price),
    #         'nonce': web3_interface.getTransactionCount(user),
    #         # 'value': 0,
    #     }
    # )


    #
    # print(f"Transaction {transaction}")
    signed_tx = web3_interface.signTransaction(user.address, user_private_key, transaction)

    tx_hash = web3_interface.sendRawTransaction(signed_tx)

    tx_receipt = web3_interface.waitForTransactionReceipt(tx_hash)
    print(f"TX HASH {tx_hash}")
    print(f"RECEIPT {tx_receipt}")
    # reply = f'RECEIPT {tx_receipt}'
    # logs = publisher_contract.events.EM_CREATED().process_receipt(tx_receipt)

    # log = publisher_contract.events.EventManager_Created().process_receipt(tx_receipt)
    # print(f'LOG {log}')

    # solidity_version = "0.8.17"
    #
    # contract_name = "Publisher.sol"
    #
    # contract_abi, contract_bin = get_contract_abi_bin(contract_name, solidity_version)
    #
    # address = deploy_contract(w3, contract_abi, contract_bin)
    #
    # print(address)


if __name__ == "__main__":
    main()