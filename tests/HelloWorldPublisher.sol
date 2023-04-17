// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;


import {Interface_EventManager} from "../PubSub/Interface_EventManager.sol";
import {Interface_PubSubService} from "../PubSub/Interface_PubSubService.sol";


contract HelloWorldPublisher {

	address public m_eventMgrAddr = address(0);
	string public m_sendData = "Hello World!";

	constructor() {
	}

	function register(address pubSubServiceAddr) external {
		require(m_eventMgrAddr == address(0), "Already registered");

		m_eventMgrAddr =
			Interface_PubSubService(pubSubServiceAddr).register();
	}

	function publish() external {
		Interface_EventManager(
			m_eventMgrAddr
		).notifySubscribers(bytes(m_sendData));
	}

	function setSendData(string memory data) external {
		m_sendData = data;
	}

}
