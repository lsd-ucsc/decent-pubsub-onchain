#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse
import json
import logging
import os
import urllib.request
import web3

from eth_account.datastructures import SignedTransaction
from typing import Any, Dict, List, Tuple, Union
from web3 import Web3 # python3 -m pip install web3
from web3.contract.contract import Contract, ContractConstructor, ContractFunction
from web3.types import TxReceipt

# check web3 version
if list(map(int, web3.__version__.split('.'))) < [ 6, 2, 0 ]:
	raise RuntimeError(
		'web3 version {} is not supported; '
		'please upgrade to version 6.2.0 or above.'.format(web3.__version__)
	)


def LoadBytesFromRelease(
	projConf: dict,
	release: str,
	contract: str
) -> Tuple[str, str]:

	urlAbi = projConf['releaseUrl'].format(version=release, contract=contract + '.abi')
	with urllib.request.urlopen(urlAbi) as f:
		abiBytes = f.read().decode()

	urlBin = projConf['releaseUrl'].format(version=release, contract=contract + '.bin')
	with urllib.request.urlopen(urlBin) as f:
		binBytes = f.read().decode()

	return abiBytes, binBytes


def LoadBytesFromLocal(projConf: dict, contract: str) -> Tuple[str, str]:

	module = projConf['contractModuleMap'][contract]

	pathAbi = os.path.join(projConf['buildDir'], module, contract + '.abi')
	if os.path.isfile(pathAbi) is False:
		raise FileNotFoundError(
			'Cannot find locally built contract ABI file at {}; '
			'please build the contract first.'.format(pathAbi)
		)

	with open(pathAbi, 'r') as f:
		abiBytes = f.read()

	pathBin = os.path.join(projConf['buildDir'], module, contract + '.bin')
	if os.path.isfile(pathBin) is False:
		raise FileNotFoundError(
			'Cannot find locally built contract BIN file at {}; '
			'please build the contract first.'.format(pathBin)
		)

	with open(pathBin, 'r') as f:
		binBytes = f.read()

	return abiBytes, binBytes


def LoadContract(
	w3: Web3,
	projConf: Union[ dict, os.PathLike ],
	contractName: str,
	release: Union[ None, str ] = None,
	address: Union[ None, str ] = None,
) -> Contract:

	if not isinstance(projConf, dict):
		with open(projConf, 'r') as f:
			projConf = json.load(f)

	if release is None:
		# load from local build
		abiBytes, binBytes = LoadBytesFromLocal(projConf, contractName)
	else:
		# load from release
		abiBytes, binBytes = LoadBytesFromRelease(projConf, release, contractName)

	if address is None:
		# deploy new contract
		contract = w3.eth.contract(abi=abiBytes, bytecode=binBytes)
	else:
		# load existing contract
		contract = w3.eth.contract(address=address, abi=abiBytes)

	return contract


def _EstimateGas(
	executable: Union[ ContractConstructor, ContractFunction ],
	value: int,
) -> int:
	logger = logging.getLogger(__name__ + '.' + _EstimateGas.__name__)

	gas = executable.estimate_gas({
		'value': value,
	})
	logger.info('Estimated gas: {}'.format(gas))
	# add a little bit flexibility
	gas = int(gas * 1.1)

	return gas


def _DetermineGas(
	executable: Union[ ContractConstructor, ContractFunction ],
	gas: Union[ None, int ],
	value: int,
) -> int:
	logger = logging.getLogger(__name__ + '.' + _DetermineGas.__name__)

	if gas is None:
		gas = _EstimateGas(executable, value)

	logger.debug('Gas: {}; Value: {}'.format(gas, value))

	return gas


def _DetermineMaxPriorFee(
	w3: Web3,
) -> int:
	baseGasFee = w3.eth.gas_price
	# priority fee is 2% of base fee
	maxPriorFee = int(baseGasFee * 2) // 100
	# ensure it's higher than w3.eth.max_priority_fee
	maxPriorFee = max(maxPriorFee, int(w3.eth.max_priority_fee))

	return maxPriorFee


def _FillMessage(
	w3: Web3,
	gas: int,
	value: int,
	privKey: Union[ None, str ],
) -> dict:

	msg = {
		'nonce': w3.eth.get_transaction_count(w3.eth.default_account),
		'chainId': w3.eth.chain_id,
		'gas': gas,
		'value': value,
	}
	if privKey is not None:
		msg['maxFeePerGas'] = int(w3.eth.gas_price * 2)
		msg['maxPriorityFeePerGas'] = _DetermineMaxPriorFee(w3)

	return msg


def _SignTx(
	w3: Web3,
	tx: dict,
	privKey: str,
	confirmPrompt: bool
) -> SignedTransaction:
	logger = logging.getLogger(__name__ + '.' + _SignTx.__name__)

	maxBaseFee = tx['maxFeePerGas']
	maxPriorityFee = tx['maxPriorityFeePerGas']
	gas = tx['gas']
	value = tx['value']

	balance = w3.eth.get_balance(w3.eth.default_account)

	maxFee = (maxBaseFee + maxPriorityFee) * gas
	maxCost = maxFee + value
	if maxCost > balance:
		raise RuntimeError(
			'Insufficient balance to pay for the transaction'
			'(balance {} wei; max cost: {} wei)'.format(
				balance, maxCost
			)
		)

	if confirmPrompt:
		baseFee = w3.eth.gas_price
		baseFeeGwei = w3.from_wei(baseFee, 'gwei')
		fee = baseFee * gas
		feeGwei = w3.from_wei(fee, 'gwei')

		maxBaseFeeGwei = w3.from_wei(maxBaseFee, 'gwei')
		maxPriorityFeeGwei = w3.from_wei(maxPriorityFee, 'gwei')
		maxFeeGwei = w3.from_wei(maxFee, 'gwei')

		valueEther = w3.from_wei(value, 'ether')

		cost = fee + value
		costEther = w3.from_wei(cost, 'ether')
		maxCostEther = w3.from_wei(maxCost, 'ether')

		balanceEther = w3.from_wei(balance, 'ether')
		afterBalanceEther = w3.from_wei(balance - cost, 'ether')
		minAfterBalanceEther = w3.from_wei(balance - maxCost, 'ether')

		print('Gas:                  {}'.format(gas))
		print('gas price:            {:.9f} Gwei'.format(baseFeeGwei))
		print('Fee:                  {:.9f} Gwei'.format(feeGwei))
		print('Max fee / gas:        {:.9f} Gwei'.format(maxBaseFeeGwei))
		print('Max prior. fee / gas: {:.9f} Gwei'.format(maxPriorityFeeGwei))
		print('Max fee:              {:.9f} Gwei'.format(maxFeeGwei))
		print('Value:                {:.18f} Ether'.format(valueEther))
		print()
		print('Cost:                 {:.18f} Ether'.format(costEther))
		print('Max cost:             {:.18f} Ether'.format(maxCostEther))
		print()
		print('Balance:              {:.18f} Ether'.format(balanceEther))
		print('After balance:        {:.18f} Ether'.format(afterBalanceEther))
		print('Min. after balance:   {:.18f} Ether'.format(minAfterBalanceEther))

		confirm = input('Confirm transaction? (please type "yes", case insensitive): ')
		if confirm.lower() != 'yes':
			raise RuntimeError('Transaction cancelled')

	logger.info(
		'Signing transaction with max cost of {} wei'.format(maxCost)
	)
	signedTx = w3.eth.account.sign_transaction(tx, privKey)

	return signedTx


def _DoTransaction(
	w3: Web3,
	executable: Union[ ContractConstructor, ContractFunction ],
	privKey: Union[ None, str ],
	gas: Union[ None, int ],
	value: int,
	confirmPrompt: bool,
) -> TxReceipt:
	logger = logging.getLogger(__name__ + '.' + _DoTransaction.__name__)

	gas = _DetermineGas(executable, gas, value)
	msg = _FillMessage(w3, gas, value, privKey)

	if privKey is None:
		# no signing needed
		txHash = executable.transact(msg)
	else:
		# need to sign
		tx = executable.build_transaction(msg)
		signedTx = _SignTx(w3, tx, privKey, confirmPrompt)
		txHash = w3.eth.send_raw_transaction(signedTx.rawTransaction)

	receipt = w3.eth.wait_for_transaction_receipt(txHash)

	receiptJson = json.dumps(json.loads(Web3.to_json(receipt)), indent=4)
	logger.info('Transaction receipt: {}'.format(receiptJson))

	logger.info('Balance after transaction: {} Ether'.format(
		w3.from_wei(
			w3.eth.get_balance(w3.eth.default_account),
			'ether'
		)
	))

	return receipt


def _FindConstructorAbi(
	abiList: List[ dict ],
) -> dict:
	for abi in abiList:
		if abi['type'] == 'constructor':
			return abi

	raise ValueError('No constructor found in ABI')


def DeployContract(
	w3: Web3,
	contract: Contract,
	arguments: list,
	privKey: Union[str, None] = None,
	gas: Union[int, None] = None,
	value: int = 0,
	confirmPrompt: bool = True,
) -> TxReceipt:
	logger = logging.getLogger(__name__ + '.' + DeployContract.__name__)

	constrAbi = _FindConstructorAbi(contract.abi)
	isPayable = constrAbi['stateMutability'] == 'payable'
	executable = contract.constructor(*arguments)

	receipt = _DoTransaction(
		w3=w3,
		executable=executable,
		privKey=privKey,
		gas=gas,
		value=value if isPayable else 0,
		confirmPrompt=confirmPrompt,
	)
	logger.info('Contract deployed at {}'.format(receipt.contractAddress))

	return receipt


def _FindFuncAbi(
	abiList: List[ dict ],
	funcName: str,
) -> dict:
	for abi in abiList:
		if (
			(abi['type'] == 'function') and
			(abi['name'] == funcName)
		):
			return abi

	raise ValueError('Function "{}" not found in ABI'.format(funcName))


def CallContractFunc(
	w3: Web3,
	contract: Contract,
	funcName: str,
	arguments: list,
	privKey: Union[str, None] = None,
	gas: Union[int, None] = None,
	value: int = 0,
	confirmPrompt: bool = True,
) -> Union[TxReceipt, Any]:
	logger = logging.getLogger(__name__ + '.' + CallContractFunc.__name__)

	funcAbi = _FindFuncAbi(contract.abi, funcName)
	isViewFunc = funcAbi['stateMutability'] == 'view'
	isPayable = funcAbi['stateMutability'] == 'payable'
	executable = contract.functions[funcName](*arguments)

	if isViewFunc:
		logger.info('Calling view function "{}"'.format(funcName))
		result = executable.call()
		logger.info('Type:{}; Result: {}'.format(type(result), result))

		return result
	else:
		receipt = _DoTransaction(
			w3=w3,
			executable=executable,
			privKey=privKey,
			gas=gas,
			value=value if isPayable else 0,
			confirmPrompt=confirmPrompt,
		)

		return receipt


def ConvertValToWei(val: int, unit: str) -> int:
	logger = logging.getLogger(__name__ + '.' + ConvertValToWei.__name__)

	valueToSend = Web3.to_wei(val, unit)
	valueToSendEth = Web3.from_wei(valueToSend, 'ether')
	if valueToSend > 0:
		logger.warning(
			'Value to be sent: {:.18f} ether (or {} wei)'.format(
				valueToSendEth,
				valueToSend
			)
		)

	return int(valueToSend)


def _LoadAccountCredentials(
	keyJson: os.PathLike,
	index: int
) -> Tuple[str, str]:
	with open(keyJson, 'r') as f:
		keyJson: Dict[str, Dict[str, str]] = json.load(f)

	if index >= len(keyJson['addresses']):
		raise IndexError('Cannot find address at index {}'.format(index))

	address = [
		a for i, a in enumerate(keyJson['addresses'].keys()) if i == index
	][0]

	for addr, priv in keyJson['private_keys'].items():
		if addr.lower() == address.lower():
			return address, priv

	raise KeyError('Cannot find private key for address {}'.format(address))


def SetupSendingAccount(
	w3: Web3,
	account: int,
	keyJson: Union[ None, os.PathLike ] = None,
) -> Union[ str, None ]:
	logger = logging.getLogger(__name__ + '.' + SetupSendingAccount.__name__)

	if keyJson is not None:
		addr, privKey = _LoadAccountCredentials(keyJson, account)
		w3.eth.default_account = addr
	else:
		w3.eth.default_account = w3.eth.accounts[0]
		privKey = None

	logger.info(
		'The address of the account to be used: {}'.format(
			w3.eth.default_account
		)
	)

	return privKey


def ChecksumGanacheKeysFile(dest: os.PathLike, src: os.PathLike):
	with open(src, 'r') as f:
		keysJson: Dict[str, Dict[str, str]] = json.load(f)

	addrs = keysJson['addresses']
	addrs = {
		Web3.to_checksum_address(k): Web3.to_checksum_address(v)
			for k, v in addrs.items()
	}
	keysJson['addresses'] = addrs

	privKeys = keysJson['private_keys']
	privKeys = {
		Web3.to_checksum_address(k): v for k, v in privKeys.items()
	}
	keysJson['private_keys'] = privKeys

	with open(dest, 'w') as f:
		json.dump(keysJson, f, indent='\t')


def main():
	argParser = argparse.ArgumentParser(
		description='Deploy contracts to Ethereum blockchain'
	)
	argParser.add_argument(
		'--config', '-c', type=str, default='project_conf.json', required=False,
		help='Path to the project configuration file'
	)
	argParser.add_argument(
		'--verbose', action='store_true',
		help='Verbose logging'
	)
	argParser.add_argument(
		'--http', type=str, default='http://localhost:7545', required=False,
		help='HTTP provider URL'
	)
	argParser.add_argument(
		'--key-json', type=str, default=None, required=False,
		help='Path to keys.json'
	)
	argParser.add_argument(
		'--account', type=int, default=0, required=False,
		help='Index of the account to use'
	)
	argParser.add_argument(
		'--release', type=str, default=None, required=False,
		help='Use prebuilt version from GitHub Release of given git version tag'
			'(if not set, local built version will be used)'
	)
	argParser.add_argument(
		'--contract', type=str, required=True,
		help='Contract name'
	)
	argParser.add_argument(
		'--gas', type=int, default=None, required=False,
		help='Gas limit'
	)
	argParser.add_argument(
		'--value', type=int, default=0, required=False,
		help='Value to be sent along with the transaction'
	)
	argParser.add_argument(
		'--value-unit', type=str, default='wei', required=False,
		choices=['ether', 'gwei', 'wei'],
		help='Unit of value (ether, gwei, wei)'
	)
	argParser.add_argument(
		'--no-confirm', action='store_true',
		help='Do not ask for confirmation'
	)

	# two operations: deploy and call
	argParserSubOp = argParser.add_subparsers(
		help='Operation to be performed',
		dest='operation',
		required=True
	)

	argParserSubOpDeploy = argParserSubOp.add_parser('deploy')
	argParserSubOpDeploy.add_argument(
		'--args', type=str, nargs='*', default=[], required=False,
		help='Constructor/function arguments'
	)

	argParserSubOpCall = argParserSubOp.add_parser('call')
	argParserSubOpCall.add_argument(
		'--address', type=str, default=None, required=True,
		help='Address of the contract to be called'
	)
	argParserSubOpCall.add_argument(
		'--function', type=str, required=True,
		help='Call function'
	)
	argParserSubOpCall.add_argument(
		'--args', type=str, nargs='*', default=[], required=False,
		help='Constructor/function arguments'
	)

	args = argParser.parse_args()

	address = None if args.operation != 'call' else args.address

	# logging configuration
	loggingFormat = '%(asctime)s %(levelname)s %(message)s'
	if args.verbose:
		logging.basicConfig(level=logging.DEBUG, format=loggingFormat)
	else:
		logging.basicConfig(level=logging.INFO, format=loggingFormat)
	logger = logging.getLogger(__name__ + main.__name__)

	# connect to Ethereum node
	w3 = Web3(Web3.HTTPProvider(args.http))
	if not w3.is_connected():
		raise RuntimeError(
			'Failed to connect to Ethereum node at %s' % args.http
		)

	valueToSend = ConvertValToWei(args.value, args.value_unit)
	privKey = SetupSendingAccount(w3, args.account, args.key_json)
	contract = LoadContract(
		w3=w3,
		projConf=args.config,
		contractName=args.contract,
		release=args.release,
		address=address
	)

	# deploy or call contract
	if args.operation == 'deploy':
		DeployContract(
			w3=w3,
			contract=contract,
			arguments=args.args,
			privKey=privKey,
			gas=args.gas,
			value=valueToSend,
			confirmPrompt=(not args.no_confirm)
		)
	elif args.operation == 'call':
		CallContractFunc(
			w3=w3,
			contract=contract,
			funcName=args.function,
			arguments=args.args,
			privKey=privKey,
			gas=args.gas,
			value=valueToSend,
			confirmPrompt=(not args.no_confirm)
		)


if __name__ == '__main__':
	main()
