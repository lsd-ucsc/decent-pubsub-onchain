#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Roy Shadmon, Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import json
import os
import random
import signal
import subprocess
import sys
import time

from web3 import Web3
from typing import List, Tuple


BASE_DIR_PATH       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'build')
UTILS_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'utils')
PYHELPER_DIR        = os.path.join(UTILS_DIR_PATH, 'PyEthHelper')
PROJECT_CONFIG_PATH = os.path.join(UTILS_DIR_PATH, 'project_conf.json')
CHECKSUM_KEYS_PATH  = os.path.join(BUILD_DIR_PATH, 'ganache_keys_checksum.json')
GANACHE_KEYS_PATH   = os.path.join(BUILD_DIR_PATH, 'ganache_keys.json')
GANACHE_PORT        = 7545
NUM_OF_ACCOUNTS     = 100
GANACHE_NET_ID      = 1337


sys.path.append(PYHELPER_DIR)
from PyEthHelper import EthContractHelper
from PyEthHelper import GanacheAccounts


def StartGanache() -> subprocess.Popen:
	cmd = [
		'ganache-cli',
		'-p', str(GANACHE_PORT),
		'-d',
		'-a', str(NUM_OF_ACCOUNTS),
		'--network-id', str(GANACHE_NET_ID),
		'--chain.hardfork', 'shanghai',
		'--wallet.accountKeysPath', str(GANACHE_KEYS_PATH),
	]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	return proc


def SelectRandomAccount(
	w3: Web3,
	numAccounts: int = NUM_OF_ACCOUNTS
) -> str:
	accountIdx = random.randint(0, numAccounts - 1)
	# accountIdx = 0
	return EthContractHelper.SetupSendingAccount(
		w3=w3,
		account=accountIdx,
		keyJson=CHECKSUM_KEYS_PATH
	)


def RunTests() -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
	maxNumPublishers = 20

	# connect to ganache
	ganacheUrl = 'http://localhost:{}'.format(GANACHE_PORT)
	w3 = Web3(Web3.HTTPProvider(ganacheUrl))
	while not w3.is_connected():
		print('Attempting to connect to ganache...')
		time.sleep(1)
	print('Connected to ganache')

	# checksum keys
	GanacheAccounts.ChecksumGanacheKeysFile(
		CHECKSUM_KEYS_PATH,
		GANACHE_KEYS_PATH
	)

	# setup account
	privKey = SelectRandomAccount(w3)


	registerCost = []
	subscribeCost = []


	for numPublishers in range(1, maxNumPublishers + 1):
		print()
		print(f'Running test with {numPublishers} subscribers')
		print()

		# deploy PubSub contract
		print('Deploying PubSub contract...')
		pubSubContract = EthContractHelper.LoadContract(
			w3=w3,
			projConf=PROJECT_CONFIG_PATH,
			contractName='PubSubService',
			release=None, # use locally built contract
			address=None, # deploy new contract
		)
		pubSubReceipt = EthContractHelper.DeployContract(
			w3=w3,
			contract=pubSubContract,
			arguments=[ ],
			privKey=privKey,
			gas=None, # let web3 estimate
			value=0,
			confirmPrompt=False # don't prompt for confirmation
		)
		pubSubAddr = pubSubReceipt.contractAddress
		print('PubSub contract deployed at {}'.format(pubSubAddr))

		# load deployed PubSub contract
		pubSubContract = EthContractHelper.LoadContract(
			w3=w3,
			projConf=PROJECT_CONFIG_PATH,
			contractName='PubSubService',
			release=None, # use locally built contract
			address=pubSubAddr, # use deployed contract
		)

		publishers = []
		regCosts = []
		print('Deploying {} publishers...'.format(numPublishers))
		for pubIndex in range(0, numPublishers):
			# choose a random account to deploy from
			privKey = SelectRandomAccount(w3)

			# deploy Publisher contract
			# print('Deploying publisher contract...')
			publisherContract = EthContractHelper.LoadContract(
				w3=w3,
				projConf=PROJECT_CONFIG_PATH,
				contractName='HelloWorldPublisher',
				release=None, # use locally built contract
				address=None, # deploy new contract
			)
			publisherReceipt = EthContractHelper.DeployContract(
				w3=w3,
				contract=publisherContract,
				arguments=[ ],
				privKey=privKey,
				gas=None, # let web3 estimate
				value=0,
				confirmPrompt=False # don't prompt for confirmation
			)
			publisherAddr = publisherReceipt.contractAddress
			# print('Publisher contract deployed at {}'.format(publisherAddr))

			# load deployed Publisher contract
			publisherContract = EthContractHelper.LoadContract(
				w3=w3,
				projConf=PROJECT_CONFIG_PATH,
				contractName='HelloWorldPublisher',
				release=None, # use locally built contract
				address=publisherAddr, # use deployed contract
			)

			# register publisher
			# print('Registering publisher...')
			regTxReceipt = EthContractHelper.CallContractFunc(
				w3=w3,
				contract=publisherContract,
				funcName='register',
				arguments=[ pubSubAddr ],
				privKey=privKey,
				gas=None, # let web3 estimate
				value=0,
				confirmPrompt=False # don't prompt for confirmation
			)
			regCosts.append(regTxReceipt.gasUsed)
			print('Register gas used: {}'.format(regTxReceipt.gasUsed))

			publishers.append(publisherContract)

		# record register gas used
		registerCost.append((
			numPublishers,
			sum(regCosts) / len(regCosts), # average gas cost
		))

		subsCosts = []
		for publisherContract in publishers:
			publisherAddr = publisherContract.address

			# choose a random account to deploy from
			privKey = SelectRandomAccount(w3)

			# deploy Subscriber contract
			# print('Deploying subscriber contract...')
			subscriberContract = EthContractHelper.LoadContract(
				w3=w3,
				projConf=PROJECT_CONFIG_PATH,
				contractName='HelloWorldSubscriber',
				release=None, # use locally built contract
				address=None, # deploy new contract
			)
			subscriberReceipt = EthContractHelper.DeployContract(
				w3=w3,
				contract=subscriberContract,
				arguments=[ pubSubAddr ],
				privKey=privKey,
				gas=None, # let web3 estimate
				value=0,
				confirmPrompt=False # don't prompt for confirmation
			)
			subscriberAddr = subscriberReceipt.contractAddress

			# load deployed Subscriber contract
			subscriberContract = EthContractHelper.LoadContract(
				w3=w3,
				projConf=PROJECT_CONFIG_PATH,
				contractName='HelloWorldSubscriber',
				release=None, # use locally built contract
				address=subscriberAddr, # use deployed contract
			)

			# subscribe
			# print('Subscribing...')
			subTxReceipt = EthContractHelper.CallContractFunc(
				w3=w3,
				contract=subscriberContract,
				funcName='subscribe',
				arguments=[ publisherAddr ],
				privKey=privKey,
				gas=None, # let web3 estimate
				value=10000000000000000, # 0.01 ether
				confirmPrompt=False # don't prompt for confirmation
			)

			# check if the subscriber was successfully subscribed
			subscribedEvMgrAddr = EthContractHelper.CallContractFunc(
				w3=w3,
				contract=subscriberContract,
				funcName='m_eventMgrAddr',
				arguments=[ ],
				privKey=None,
				gas=None,
				value=0,
				confirmPrompt=False # don't prompt for confirmation
			)
			registeredEvMgrAddr = EthContractHelper.CallContractFunc(
				w3=w3,
				contract=publisherContract,
				funcName='m_eventMgrAddr',
				arguments=[ ],
				privKey=None,
				gas=None,
				value=0,
				confirmPrompt=False # don't prompt for confirmation
			)
			if subscribedEvMgrAddr != registeredEvMgrAddr:
				raise RuntimeError('Subscriber was not subscribed to publisher')

			print('Subscriber@{} subscribed to publisher@{}'.format(
				subscriberAddr,
				publisherAddr
			))

			subsCosts.append(subTxReceipt.gasUsed)
			print('Gas used: {}'.format(subTxReceipt.gasUsed))

		# record subscribe gas used
		subscribeCost.append((
			numPublishers,
			sum(subsCosts) / len(subsCosts), # average gas cost
		))

	return registerCost, subscribeCost


def StopGanache(ganacheProc: subprocess.Popen) -> None:
	print('Shutting down ganache (it may take ~15 seconds)...')
	waitEnd = time.time() + 20
	ganacheProc.terminate()
	while ganacheProc.poll() is None:
		try:
			if time.time() > waitEnd:
				print('Force to shut down ganache')
				ganacheProc.kill()
			else:
				print('Still waiting for ganache to shut down...')
				ganacheProc.send_signal(signal.SIGINT)
			ganacheProc.wait(timeout=2)
		except subprocess.TimeoutExpired:
			continue
	print('Ganache has been shut down')


def main():
	ganacheProc = StartGanache()

	try:
		regGasResults = []
		subsGasResults = []

		for _ in range(3):
			registerCost, subscribeCost = RunTests()

			# print('Subscribe gas cost results:')
			# for cost in subscribeCost:
			# 	print('{:03} publishers: {:010.2f} gas'.format(cost[0], cost[1]))

			regGasResults.append(registerCost)
			subsGasResults.append(subscribeCost)

		# save results
		outputFile = os.path.join(BUILD_DIR_PATH, 'subscribe_gas_cost.json')
		with open(outputFile, 'w') as f:
			json.dump(subsGasResults, f, indent='\t')
		outputFile = os.path.join(BUILD_DIR_PATH, 'register_gas_cost.json')
		with open(outputFile, 'w') as f:
			json.dump(regGasResults, f, indent='\t')

	finally:
		# finish and exit
		StopGanache(ganacheProc)

if __name__ == "__main__":
	main()
