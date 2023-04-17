// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;


import {Interface_PubSubService} from "../../PubSub/Interface_PubSubService.sol";
import {Interface_EventManager} from "../../PubSub/Interface_EventManager.sol";


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


contract FailingSubscriber{

    bytes public m_recvData = "before notify";

    constructor() {
    }

    function onNotify(bytes memory data) external {
        // this should always fail and consume all remaining gases
        assert(false);
        m_recvData = data;
    }

}


contract HungrySubscriber{

    bytes public m_recvData = "before notify";

    constructor() {
    }

    function onNotify(bytes memory data) external {
        // this should consume all remaining gases
        uint i = 0;
        while(gasleft() > 0) {
            i++;
            if (i >= 1000000) {
                i = 0;
            }
        }
        m_recvData = data;
    }

}


contract ImcompatibleSubscriber{

    bytes public m_recvData = "before notify";

    constructor() {
    }

    function onNotifyyyyy(bytes memory data) external {
        m_recvData = data;
    }

}


contract ReentrySubscriber{

    address public m_eventMgrAddr;
    bytes public m_recvData = "before notify";

    constructor(address eventMrgAddr) {
        m_eventMgrAddr = eventMrgAddr;
    }

    function onNotify(bytes memory data) external {
        Interface_EventManager(m_eventMgrAddr).notifySubscribers(data);
        m_recvData = data;
    }

}


contract TestPublisher{
    address public m_eventMgrAddr;

    constructor() {
    }

    function register(address pubSubServiceAddr) external returns (address) {
        m_eventMgrAddr = Interface_PubSubService(pubSubServiceAddr).register();
        return m_eventMgrAddr;
    }

    function setEventMgrAddr(address eventMgrAddr) external {
        m_eventMgrAddr = eventMgrAddr;
    }

    function notifySubscribers(bytes memory data) external {
        Interface_EventManager(m_eventMgrAddr).notifySubscribers(data);
    }
}
