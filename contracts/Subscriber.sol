// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfacePublisher {
    function subscribe(uint balance) external;
    function notify(address member) external;
}

contract Subscriber {
    address publisher;
    
    event SubscribedEvent(address member);

    constructor(address defaultPublisher) {
        publisher = defaultPublisher;
        InterfacePublisher(publisher).subscribe(1337);
    }

    function publish(address member) external {
        emit SubscribedEvent(member);
    }
}

