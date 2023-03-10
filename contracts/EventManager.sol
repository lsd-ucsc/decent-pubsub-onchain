// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {Subscriber as SubscribeContract} from "./Subscriber.sol";


contract EventManager {

    struct Subscriber {
        address addr;
        // address user;
        address publisher;
        uint balance;
        bool init;
        bool notified;
    }


    event addedToBlackList(address user);
    event removeFromBlackList(address user);


    address[] subscriber_addrs;
    mapping (address => Subscriber) subscribers; // quick look up

    uint incentive = 1000; // default incentive is 10000 Wei
    address owner; // initialize owner variable

    constructor(uint256 deposit) payable {
        require(msg.value == deposit); // deposit is in Wei
        require(msg.value > 0);
        deposit = msg.value;
        owner = msg.sender; // owner is the address that deployed the smart contract
    }



    function addSubscriber(address publisher_addr, address payable user, address subscribeContractAddr) external payable{
        // need to "require" msg.sender is a smart contract with the publish function
        require(msg.value > 0, "You need to send more than 0 Wei");
        // require(msg.value == deposit, "Message value doesn't equal defined deposit"); // Ensure subscriber is sending amount equal to the balance they want to deposit
        // uint gas_cost = gasleft();
        subscriber_addrs.push(subscribeContractAddr);
        subscribers[subscribeContractAddr] = Subscriber(subscribeContractAddr, publisher_addr, msg.value, true, false); // add subscriber to map
        user.transfer(msg.value);  // transfer
    }


    function notifyAddedToBlackList(address user) external payable {
        uint balanceAfterIncentive = 0;
        uint toCompensate = 0; // maintain running track of how much to compensate msg.sender
        uint startGas = 0;
        uint endGas = 0;
        uint gasUsed = 0;

        for (uint i = 0; i < subscriber_addrs.length; i++) {
            if (subscribers[subscriber_addrs[i]].balance - incentive > 0) {      // only notify subscriber if they have enough balance   (TODO: Maybe we should require a minimum balance? i.e., what is the max cost of this transaction?)
                // calculate how much notification costs
                startGas = gasleft();
                SubscribeContract(subscriber_addrs[i]).addedUserToBlackList(user);  // This is the notification
                endGas = gasleft();
                toCompensate = toCompensate + startGas - endGas;
                balanceAfterIncentive = subscribers[subscriber_addrs[i]].balance - incentive - gasUsed;
            }
        }
        // transfer compensate funds for notifications to the user that initiated the "add to blacklist" function
        // toCompensate = 100;
        payable(msg.sender).transfer(toCompensate);
        // return(toCompensate);
    }


    function notifyRemoveFromBlackList(address user) external payable {
        uint balanceAfterIncentive = 0;
        uint toCompensate = 0; // maintain running track of how much to compensate msg.sender
        uint startGas = 0;
        uint endGas = 0;
        uint gasUsed = 0;

        for (uint i = 0; i < subscriber_addrs.length; i++) {
            if (subscribers[subscriber_addrs[i]].balance - incentive > 0) {      // only notify subscriber if they have enough balance   (TODO: Maybe we should require a minimum balance? i.e., what is the max cost of this transaction?)
                // calculate how much notification costs
                startGas = gasleft();
                SubscribeContract(subscriber_addrs[i]).removeFromBlackList(user);  // This is the notification
                endGas = gasleft();
                toCompensate = toCompensate + startGas - endGas;
                balanceAfterIncentive = subscribers[subscriber_addrs[i]].balance - incentive - gasUsed;
            }
        }
        // transfer compensate funds for notifications to the user that initiated the "add to blacklist" function
        payable(msg.sender).transfer(toCompensate);
    }


    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }


    function subscriberAddBalance(address subscriber, uint amount) payable external {
        require (subscribers[subscriber].init, "You have not subscribed to the system"); // Require subscriber to be part of the system
        require (amount == msg.value, "Amount specified does not equal amount sent"); // make sure amount is the same as the message amount
        require (msg.sender == subscribers[subscriber].addr, "You did not initialize subscriber");
        subscribers[subscriber].balance += msg.value;
    }

    // Subscriber can check its balance but not the balance of others
    function checkSubscriberBalance(address subscriber) external view returns(uint) {
        require(subscribers[subscriber].init, "Subscriber not subscribed");
        return subscribers[subscriber].balance;
    }


    //since incentive is statically set, function to enable smart contract owner to update the incentive value
    function updateIncentive(uint new_incentive) external {
        require(msg.sender == owner);
        incentive = new_incentive;
    }

    function viewSubscriberList() public view returns(address[] memory){
            return subscriber_addrs;
    }

}
