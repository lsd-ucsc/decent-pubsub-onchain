// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfacePublisher {
    function subscribe(address user, uint balance) external;
    function notify(address member) external;
}

contract Subscriber {
    address publisher;
    
    event SubscribedEvent(address member);

    constructor(address defaultPublisher) {        
        publisher = defaultPublisher;
        InterfacePublisher(publisher).subscribe(msg.sender, 1337); 
    }

    function publish(address member) external {
        emit SubscribedEvent(member);
    }


    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
