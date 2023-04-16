// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;


import {Interface_PubSubService} from "../../PubSub/Interface_PubSubService.sol";


contract DummyContract {
    constructor() {
    }
}


contract TestSubscriber{
    bytes public m_recvData;

    constructor() {
    }

    function onNotify(bytes memory data) external {
        m_recvData = data;
    }

    function subscribe(address pubSubServiceAddr, address publisherAddr)
        external
        payable
    {
        Interface_PubSubService(pubSubServiceAddr).subscribe{
            value: msg.value
        }(publisherAddr);
    }
}


contract TestPublisher{
    address public m_eventMgrAddr;

    constructor(address pubSubServiceAddr) {
        m_eventMgrAddr = Interface_PubSubService(pubSubServiceAddr).register();
    }

    function register(address pubSubServiceAddr) external returns (address) {
        m_eventMgrAddr = Interface_PubSubService(pubSubServiceAddr).register();
        return m_eventMgrAddr;
    }
}
