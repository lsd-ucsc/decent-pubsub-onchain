import sys
import time
import pprint
import os
import subprocess
from subprocess import PIPE

from web3.providers import HTTPProvider
from web3 import Web3

# Get the directory where the current Python script is located
script_directory = os.path.dirname(os.path.abspath(__file__))
# Get the root directory of the project (assuming the root directory is the parent directory of the script directory)
root_directory = os.path.dirname(script_directory)


def deploy_contract(w3, contract_interface):
    tx_hash = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']).constructor().transact()

    address = w3.eth.get_transaction_receipt(tx_hash)['contractAddress']
    return address


def compile_contract(contract_name, solidity_version):
    contract_path = os.path.join(root_directory, f"contracts/{contract_name}")
    output_dir = os.path.join(root_directory, f"contracts/compiled_contracts/{solidity_version}")
    # Run the javascript compile contract command
    base_path = contract_path.split(contract_name)[0]
    compile_command = f"solcjs --bin --abi --base-path {base_path} {contract_name} --output-dir {output_dir}"


    print(compile_command)
    subprocess.run(str(compile_command), shell=True)



def main():
    solidity_version = "0.8.17"
    contract_name = "Publisher.sol"
    compile_contract(contract_name, solidity_version)





if __name__ == "__main__":
    main()