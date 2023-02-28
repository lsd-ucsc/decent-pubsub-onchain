// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfacePubSubService {
    function publish(address member) external;
}


contract EventManager {
    struct Subscriber {
        address subscriberSMC;
        address user;
        uint balance;
        bool init;
        bool notified;
    }

    struct SubscriberKey {
        address addr;
    }

    SubscriberKey[] subscriber_keys;
    mapping (address => Subscriber) subscribers; // quick look up

    uint incentive = 1000; // default incentive is 10000 Wei
    address owner; // initialize owner variable

    constructor(uint256 deposit) payable {
        require(msg.value == deposit); // deposit is in Wei
        require(msg.value > 0);
        deposit = msg.value;
        owner = msg.sender; // owner is the address that deployed the smart contract
    }

    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }



    function subscribe(address payable user, uint deposit) external payable{
        // need to "require" msg.sender is a smart contract with the publish function
        require(msg.value > 0, "You need to send more than 0 Wei");
        require(msg.value == deposit, "Message value doesn't equal defined deposit"); // Ensure subscriber is sending amount equal to the balance they want to deposit
        uint gas_cost = gasleft();
        subscriber_keys.push(SubscriberKey(msg.sender));
        subscribers[msg.sender] = Subscriber(msg.sender, user, deposit, true, false); // add subscriber to map
        user.transfer(gas_cost);  // transfer
    }


    function notify(address member) external payable {
        require(subscribers[member].init == true); // verify subscriber exists
        require(subscribers[member].notified == false); // verify subscriber hasn't been notified about
        subscribers[member].notified = true;

        // It's cheaper to declare and reallocate variables outside of for loop
        uint balanceAfterIncentive = 0;
        uint toCompensate = 0; // maintain running track of how much to compensate msg.sender
        uint startGas = 0;
        uint endGas = 0;
        uint gasUsed = 0;
        for (uint i = 0; i < subscriber_keys.length; i++) {
            if (subscribers[subscriber_keys[i].addr].balance - incentive > 0) {      // only notify subscriber if they have enough balance
                balanceAfterIncentive = subscribers[subscriber_keys[i].addr].balance - incentive;
                // calculate how much notification costs
                startGas = gasleft();
                InterfacePubSubService(subscribers[subscriber_keys[i].addr].subscriberSMC).publish(member);
                endGas = gasleft();
                gasUsed = startGas - endGas;

                // Note -- I wrote this based on the PR comment but I'm not sure this if/else is sound.
                // e.g., subscriber[i].balance - gasUsed could be < 0
                // also checking if gasUsed == balanceAfterIncentive will probably never be true
                if (gasUsed == balanceAfterIncentive) {
                    toCompensate += subscribers[subscriber_keys[i].addr].balance;
                    subscribers[subscriber_keys[i].addr].balance = 0;
                }
                else {
                    toCompensate += subscribers[subscriber_keys[i].addr].balance - gasUsed;
                    subscribers[subscriber_keys[i].addr].balance = subscribers[subscriber_keys[i].addr].balance - gasUsed;
                }
            }
        }
        // transfer compensate funds
        payable(msg.sender).transfer(toCompensate);
    }

    // subscriber add balance
    function subscriberAddBalance(address subscriber, uint amount) payable external {
        require (subscribers[subscriber].init, "You have not subscribed to the system"); // Require subscriber to be part of the system
        require (amount == msg.value, "Amount specified does not equal amount sent"); // make sure amount is the same as the message amount
        require (msg.sender == subscribers[subscriber].user, "You did not initialize subscriber");
        subscribers[subscriber].balance += msg.value;
    }

    // Subscriber can check its balance but not the balance of others
    function checkSubscriberBalance(address subscriber) external view returns(uint) {
        require(msg.sender == subscribers[subscriber].user, "You did not initialize subscriber");
        require(subscribers[subscriber].init, "Subscriber not subscribed");
        return subscribers[subscriber].balance;
    }

    function checkSubscriberNotified(address subscriber) external view returns(bool) {
        require(msg.sender == subscribers[subscriber].user, "You did not initialize subscriber");
        require(subscribers[subscriber].init, "Subscriber not initialized");
        if (subscribers[subscriber].notified) {
            return true;
        }
        return false;
    }

    //since incentive is statically set, function to enable smart contract owner to update the incentive value
    function updateIncentive(uint new_incentive) external {
        require(msg.sender == owner);
        incentive = new_incentive;
    }

}
