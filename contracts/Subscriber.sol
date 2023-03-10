// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {PubSubService} from "./PubSubService.sol";

contract Subscriber {

    constructor(address publisher_addr, address pubsub_addr, uint deposit) payable {
        require(deposit == msg.value, "Deposit must equal sent amount");
        PubSubService(pubsub_addr).subscribe{value: msg.value}(publisher_addr, msg.value, address(this));
    }

    address[] blackList;
    mapping(address => bool) blLookup;

    function addedUserToBlackList(address user) external {
        blackList.push(user);
        blLookup[user] = true;

    }

    function removeFromBlackList(address user) external {
        remove(blackList, user);
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
    }

    function viewBlackList() public view returns(address[] memory) {
        return blackList;
    }


}
