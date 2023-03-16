// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_PubSubService {
    function subscribe(address publisher_addr, uint256 deposit, address subscribeContractAddr) external payable;
}

// Enum interface?

contract Subscriber {
    event BlackListAdd(address member);
    event BlackListRemoved(address member);

    constructor(address publisher_addr, address pubsub_addr, uint256 deposit) payable {
        require(deposit == msg.value, "Deposit must equal sent amount");
        Interface_PubSubService(pubsub_addr).subscribe{value: msg.value}(publisher_addr, msg.value, address(this));
    }

    address[] blackList;
    mapping(address => bool) blLookup;

    enum Action { ADD_TO_BLACKLIST, DELETE_FROM_BLACKLIST } // Types of actions

    function addedUserToBlackList(address user) public {
        blackList.push(user);
        blLookup[user] = true;
    }

    function removeFromBlackList(address user) public {
        remove(blackList, user);
    }

    function notify(bytes memory data) public {
        (Action action, address user) = abi.decode(data, (Action, address));
        if (action == Action.ADD_TO_BLACKLIST) {
            addedUserToBlackList(user);
            emit BlackListAdd(user);
        } else if (action == Action.DELETE_FROM_BLACKLIST) {
            removeFromBlackList(user);
            emit BlackListRemoved(user);
        }
    }

    // helper function to remove element from array
    // Find the element, copy the last element to its spot in the array and then pop the last element (not keeping order)
    function remove(address[] storage bList, address member) internal   {
        require(bList.length > 0, "Received empty publisher list");
        require(blLookup[member] == true, "User not in list");

        for (uint i = 0; i < bList.length; i++){
            if (bList[i] == member) {
                bList[i] = bList[bList.length-1]; // remove element by overwriting previous index and removing the last index
                bList.pop();
            }
        }
        blLookup[member] = false;
    }

    function viewBlackList() public view returns(address[] memory) {
        return blackList;
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }

}
