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

from typing import Dict, Tuple, Union
from web3 import Web3 # python3 -m pip install web3
from web3.contract import Contract

RELEASE_URL_BASE = 'https://github.com/lsd-ucsc/decent-pubsub-onchain/releases/download/{version}/{contract}'
LOCAL_BUILD_DIR = 'build'
CONTRACT_MODULE_MAP = {
	'PubSubService'       : 'PubSub',
	'EventManager'        : 'PubSub',
	'HelloWorldPublisher' : 'tests',
	'HelloWorldSubscriber': 'tests',
}


def LoadBytesFromRelease(release: str, contract: str) -> Tuple[str, str]:

	urlAbi = RELEASE_URL_BASE.format(version=release, contract=contract + '.abi')
	with urllib.request.urlopen(urlAbi) as f:
		abiBytes = f.read().decode()

	urlBin = RELEASE_URL_BASE.format(version=release, contract=contract + '.bin')
	with urllib.request.urlopen(urlBin) as f:
		binBytes = f.read().decode()

	return abiBytes, binBytes


def LoadBytesFromLocal(contract: str) -> Tuple[str, str]:

	module = CONTRACT_MODULE_MAP[contract]

	pathAbi = os.path.join(LOCAL_BUILD_DIR, module, contract + '.abi')
	with open(pathAbi, 'r') as f:
		abiBytes = f.read()

	pathBin = os.path.join(LOCAL_BUILD_DIR, module, contract + '.bin')
	with open(pathBin, 'r') as f:
		binBytes = f.read()

	return abiBytes, binBytes


def LoadPrivateKey(keyJson: os.PathLike, address: str) -> str:
	with open(keyJson, 'r') as f:
		keyJson: Dict[str, Dict[str, str]] = json.load(f)

	for addr, priv in keyJson['private_keys'].items():
		if addr.lower() == address.lower():
			return priv

	raise KeyError('Cannot find private key for address {}'.format(address))


def DeployContract(
	w3: Web3,
	contract: Contract,
	arguments: list,
	# account: str,
	# privKey: str,
	gas: Union[int, None] = None,
	value: int = 0,
) -> str:
	logger = logging.getLogger(__name__ + DeployContract.__name__)

	if gas is None:
		gas = contract.constructor(*(arguments)).estimateGas({
			'value': value,
		})
		logger.info('Estimated gas: {}'.format(gas))
		# add a little bit flexibility
		gas = int(gas * 1.1)

	logger.debug('Gas: {}; Value: {}'.format(gas, value))

	txHash = contract.constructor(*arguments).transact({
		'gas': gas,
		'value': value,
	})
	receipt = w3.eth.wait_for_transaction_receipt(txHash)

	receiptJson = json.dumps(json.loads(Web3.toJSON(receipt)), indent=4)
	logger.info('Transaction receipt: {}'.format(receiptJson))
	logger.info('Contract deployed at {}'.format(receipt.contractAddress))


def CallContractFunc(
	w3: Web3,
	contract: Contract,
	funcName: str,
	arguments: list,
	# account: str,
	# privKey: str,
	gas: Union[int, None] = None,
	value: int = 0,
) -> str:
	logger = logging.getLogger(__name__ + CallContractFunc.__name__)

	if gas is None:
		gas = contract.functions[funcName](*arguments).estimateGas({
			'value': value,
		})
		logger.info('Estimated gas: {}'.format(gas))
		# add a little bit flexibility
		gas = int(gas * 1.1)

	logger.debug('Gas: {}; Value: {}'.format(gas, value))

	txHash = contract.functions[funcName](*arguments).transact({
		'gas': gas,
		'value': value,
	})
	receipt = w3.eth.wait_for_transaction_receipt(txHash)

	receiptJson = json.dumps(json.loads(Web3.toJSON(receipt)), indent=4)
	logger.info('Transaction receipt: {}'.format(receiptJson))


def main():
	argParser = argparse.ArgumentParser(
		description='Deploy contracts to Ethereum blockchain'
	)
	argParser.add_argument(
		'--verbose', action='store_true',
		help='Verbose logging'
	)
	argParser.add_argument(
		'--http', type=str, default='http://localhost:7545', required=False,
		help='HTTP provider URL'
	)
	# argParser.add_argument(
	# 	'--keys', type=str, default='build/keys.json', required=False,
	# 	help='Path to keys.json'
	# )

	argParserGrpSrc = argParser.add_mutually_exclusive_group(required=True)
	argParserGrpSrc.add_argument(
		'--release', type=str, default=None,
		help='Use prebuilt version from GitHub Release of given git version tag'
	)
	argParserGrpSrc.add_argument(
		'--local', action='store_true',
		help='Use locally built version'
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
		'--address', type=str, required=True,
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

	# logging configuration
	loggingFormat = '%(asctime)s %(levelname)s %(message)s'
	if args.verbose:
		logging.basicConfig(level=logging.DEBUG, format=loggingFormat)
	else:
		logging.basicConfig(level=logging.INFO, format=loggingFormat)
	logger = logging.getLogger(__name__ + main.__name__)

	# convert value to wei
	valueToSend = Web3.toWei(args.value, args.value_unit)
	valueToSendEth = Web3.fromWei(valueToSend, 'ether')
	if valueToSend > 0:
		logger.warning(
			'Value to be sent: {:.18f} ether (or {} wei)'.format(
				valueToSendEth,
				valueToSend
			)
		)

	# connect to Ethereum node
	w3 = Web3(Web3.HTTPProvider(args.http))
	if not w3.isConnected():
		raise RuntimeError(
			'Failed to connect to Ethereum node at %s' % args.http
		)

	# set pre-funded account as sender
	w3.eth.default_account = w3.eth.accounts[0]
	# privKey = LoadPrivateKey(args.keys, str(w3.eth.default_account))
	# print account address
	logger.info(
		'The address of the account to be used: {}'.format(
			w3.eth.default_account
		)
	)

	# load contract ABI and bytecode
	if args.local:
		abiBytes, binBytes = LoadBytesFromLocal(args.contract)
	else:
		abiBytes, binBytes = LoadBytesFromRelease(args.release, args.contract)

	# construct contract object
	if args.operation == 'call':
		contract = w3.eth.contract(address=args.address, abi=abiBytes)
	else:
		contract = w3.eth.contract(abi=abiBytes, bytecode=binBytes)

	# deploy or call contract
	if args.operation == 'deploy':
		DeployContract(
			w3=w3,
			contract=contract,
			arguments=args.args,
			# account=w3.eth.default_account,
			# privKey=privKey,
			gas=args.gas,
			value=valueToSend
		)
	elif args.operation == 'call':
		CallContractFunc(
			w3=w3,
			contract=contract,
			funcName=args.function,
			arguments=args.args,
			# account=w3.eth.default_account,
			# privKey=privKey,
			gas=args.gas,
			value=valueToSend
		)


if __name__ == '__main__':
	main()
