#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Roy Shadmon, Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import os
import signal
import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

from web3 import Web3
from typing import List, Tuple


BASE_DIR_PATH       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'build')
UTILS_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'utils')
PROJECT_CONFIG_PATH = os.path.join(UTILS_DIR_PATH, 'project_conf.json')
CHECKSUM_KEYS_PATH  = os.path.join(UTILS_DIR_PATH, 'ganache_keys_checksum.json')
GANACHE_KEYS_PATH   = os.path.join(UTILS_DIR_PATH, 'ganache_keys.json')
GANACHE_PORT        = 7545

sys.path.append(UTILS_DIR_PATH)
import EthContractHelper


def StartGanache() -> subprocess.Popen:
	cmd = [
		'ganache-cli',
		'-p', str(GANACHE_PORT),
		'-d',
		'-a', '20',
		'--network-id', '1337',
		'--wallet.accountKeysPath', GANACHE_KEYS_PATH,
	]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	return proc


def RunTests() -> List[Tuple[int, int]]:
	maxNumPublishers = 20

	# connect to ganache
	ganacheUrl = 'http://localhost:{}'.format(GANACHE_PORT)
	w3 = Web3(Web3.HTTPProvider(ganacheUrl))
	while not w3.is_connected():
		print('Attempting to connect to ganache...')
		time.sleep(1)
	print('Connected to ganache')

	# setup account
	privKey = EthContractHelper.SetupSendingAccount(
		w3=w3,
		account=0, # use account 0
		keyJson=CHECKSUM_KEYS_PATH
	)


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
		for pubIndex in range(0, numPublishers):
			# deploy Publisher contract
			print('Deploying publisher contract...')
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
			print('Publisher contract deployed at {}'.format(publisherAddr))

			# load deployed Publisher contract
			publisherContract = EthContractHelper.LoadContract(
				w3=w3,
				projConf=PROJECT_CONFIG_PATH,
				contractName='HelloWorldPublisher',
				release=None, # use locally built contract
				address=publisherAddr, # use deployed contract
			)

			# register publisher
			print('Registering publisher...')
			EthContractHelper.CallContractFunc(
				w3=w3,
				contract=publisherContract,
				funcName='register',
				arguments=[ pubSubAddr ],
				privKey=privKey,
				gas=None, # let web3 estimate
				value=0,
				confirmPrompt=False # don't prompt for confirmation
			)

			publishers.append(publisherContract)

		costs = []
		for publisherContract in publishers:
			publisherAddr = publisherContract.address

			# deploy Subscriber contract
			print('Deploying subscriber contract...')
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
			print('Subscribing...')
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
			print('Subscriber@{} subscribed to publisher@{}'.format(
				subscriberAddr,
				publisherAddr
			))

			costs.append(subTxReceipt.gasUsed)
			print('Gas used: {}'.format(subTxReceipt.gasUsed))

		# record gas used
		subscribeCost.append((
			numPublishers,
			sum(costs) / len(costs), # average gas cost
		))

	return subscribeCost


def DrawGraph(
	dest: os.PathLike,
	data: List[Tuple[int, int]],
	scaleBy: int,
	title: str,
	xlabel: str = 'Number of subscribers',
	ylabel: str = 'Gas cost',
) -> None:

	scale = np.power(10, scaleBy)
	axes = plt.subplot()
	axes.plot(
		np.arange(1, len(data) + 1),
		np.array([ cost for _, cost in data ]) / scale,
	)

	# set y-axis limits
	dataAvg = sum([ cost for _, cost in data ])
	dataAvg = dataAvg / len(data)
	ymax = (dataAvg + (dataAvg * 0.0001)) / scale
	ymin = (dataAvg - (dataAvg * 0.0001)) / scale
	axes.set_ylim([ymin, ymax])

	# avoid scientific notation
	current_values = axes.get_yticks()
	axes.set_yticklabels(
		['{:.04f}'.format(x) for x in current_values]
	)

	plt.xticks(np.arange(1, len(data) + 1))
	plt.title(title)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel + f' (1e{scaleBy})')
	plt.savefig(dest)


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
		subscribeCost = RunTests()

		print('Subscribe gas cost results:')
		for cost in subscribeCost:
			print('{:03} publishers: {:010.2f} gas'.format(cost[0], cost[1]))

		DrawGraph(
			dest=os.path.join(BUILD_DIR_PATH, 'subscribe_gas_cost.svg'),
			data=subscribeCost,
			scaleBy=5,
			title='Gas cost of subscribing',
		)
	finally:
		# finish and exit
		StopGanache(ganacheProc)

if __name__ == "__main__":
	main()
