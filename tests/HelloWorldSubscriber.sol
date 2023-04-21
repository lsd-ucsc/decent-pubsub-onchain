// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;


import {Interface_EventManager} from "../PubSub/Interface_EventManager.sol";
import {Interface_PubSubService} from "../PubSub/Interface_PubSubService.sol";


contract HelloWorldSubscriber {

	address public m_pubSubServiceAddr;
	address public m_eventMgrAddr = address(0);
	string public m_recvData;

	constructor(address pubSubServiceAddr) {
		m_pubSubServiceAddr = pubSubServiceAddr;
	}

	function onNotify(bytes memory data) external {
		require(m_eventMgrAddr != address(0), "Not subscribed");
		require(msg.sender == m_eventMgrAddr, "Unauthorized");
		m_recvData = string(data);
	}

	function subscribe(address publisherAddr) external payable {
		require(m_eventMgrAddr == address(0), "Already subscribed");

		m_eventMgrAddr = Interface_PubSubService(
			m_pubSubServiceAddr
		).getEventManagerAddr(publisherAddr);

		Interface_EventManager(
			m_eventMgrAddr
		).addSubscriber{
			value: msg.value
		}(
			address(this)
		);
	}
}
