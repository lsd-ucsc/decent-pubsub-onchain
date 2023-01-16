// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfaceSubscriber {
    function publish(address member) external;
}

contract Publisher {
    struct Subscriber {
        address addr;
        uint balance;
    }

    Subscriber[] subscribers;

    function subscribe(uint balance) external {
        subscribers.push(Subscriber(msg.sender, balance));
    }

    function notify(address member) external {
        for (uint i = 0; i < subscribers.length; i++) {
            if (subscribers[i].balance > 0) {
                InterfaceSubscriber(subscribers[i].addr).publish(member);
            }
        }
    }
}

