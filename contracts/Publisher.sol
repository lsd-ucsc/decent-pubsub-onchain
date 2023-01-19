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

    constructor(uint256 deposit) payable { 
        require(msg.value == deposit); // deposit is in Wei
        require(msg.value > 0);
        deposit = msg.value;
    }

    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }



    function subscribe(address payable user, uint balance) external {
        uint gas_cost = gasleft();
        subscribers.push(Subscriber(msg.sender, balance));
        user.transfer(gas_cost);        
    }

    function notify(address member) external {
        for (uint i = 0; i < subscribers.length; i++) {
            if (subscribers[i].balance > 0) {
                InterfaceSubscriber(subscribers[i].addr).publish(member);
            }
        }
    }

}
