// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_Subscriber {
    function addedUserToBlackList(address user) external;
    function removeFromBlackList(address user) external;
    function notify(bytes memory data) external;
}

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

    uint incentive = 1000000; // default incentive is 10000 Wei
    uint256 min_deposit = 100000000;
    address owner; // initialize owner variable

    constructor() {
        owner = msg.sender; // owner is the address that deployed the smart contract
    }


    function addSubscriber(address publisher_addr, address subscribeContractAddr) public payable{
        // need to "require" msg.sender is a smart contract with the publish function
        require(msg.value > min_deposit, "You need to send at least the minimum deposit");
        subscriber_addrs.push(subscribeContractAddr);
        subscribers[subscribeContractAddr] = Subscriber(subscribeContractAddr, publisher_addr, msg.value, true, false); // add subscriber to map

    }


    function notify(bytes memory data) public {
        require(gasleft() <= address(this).balance, "Contract doesn't have enough funds");
        uint256 toCompensate = 0; // maintain running track of how much to compensate msg.sender
        uint startGas = 0;
        uint endGas = 0;

        uint numSubscribers = subscriber_addrs.length;
        uint incentiveCharge = incentive / numSubscribers;

        for (uint i = 0; i < subscriber_addrs.length; i++) {
            if (subscribers[subscriber_addrs[i]].balance - incentive > 0) {      // only notify subscriber if they have enough balance   (TODO: Maybe we should require a minimum balance? i.e., what is the max cost of this transaction?)
                // calculate how much notification costs
                startGas = gasleft();
                Interface_Subscriber(subscriber_addrs[i]).notify(data);  // This is the notification
                endGas = gasleft();
                toCompensate = toCompensate + startGas - endGas;
                subscribers[subscriber_addrs[i]].balance = subscribers[subscriber_addrs[i]].balance - (incentiveCharge + (startGas-endGas));
            }
        }
        // transfer compensate funds for notifications to the user that initiated the "add to blacklist" function
        require(toCompensate < address(this).balance, "Contract doesn't have enough funds");

        (bool success, ) = payable(msg.sender).call{value: toCompensate}("");  //.call is required to transfer funds to a smart contract. Transferring funds back to a smart contract costs more than the maximum gas cost of 2300 for .transfer. https://stackoverflow.com/questions/66112452/how-to-transfer-fund-from-msg-senderamount-to-recipient-address-without-using#:~:text=These%20examples%20work%20on%20Solidity%200.8.%20Some%20previous,uint256%20bonus%20%3D%20calculateBonus%20%28%29%3B%20payable%20%28msg.sender%29.transfer%20%28bonus%29%3B
        require(success, "Reimbursement failed.");
    }


    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }


    function subscriberAddBalance(address subscriber, uint amount) payable public {
        require (subscribers[subscriber].init, "You have not subscribed to the system"); // Require subscriber to be part of the system
        require (amount == msg.value, "Amount specified does not equal amount sent"); // make sure amount is the same as the message amount
        require (msg.sender == subscribers[subscriber].addr, "You did not initialize subscriber");
        subscribers[subscriber].balance += msg.value;
    }

    // Subscriber can check its balance but not the balance of others
    function checkSubscriberBalance(address subscriber) public view returns(uint) {
        require(subscribers[subscriber].init, "Subscriber not subscribed");
        return subscribers[subscriber].balance;
    }


    //since incentive is statically set, function to enable smart contract owner to update the incentive value
    function updateIncentive(uint new_incentive) public {
        require(msg.sender == owner);
        incentive = new_incentive;
    }

    function viewSubscriberList() public view returns(address[] memory){
            return subscriber_addrs;
    }

}
