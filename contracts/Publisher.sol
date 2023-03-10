// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

// interface InterfaceeventManager {
//     function notify(address member) external;
// }

import {PubSubService} from "./PubSubService.sol";
import {EventManager} from "./EventManager.sol";

// interface InterfacePubSubService {
//     function register() external;
// }

contract Publisher {


    struct BlackList {
        address[] memberList; // keep list of registered publishers
        mapping(address => bool) members; // easy lookup into in memberList (publisher => bool)
    }

    bool public registeredToPubSub = false;
    address public PubSubAddress;
    address public eventManagerAddress;
    PubSubService pubService;

    BlackList officialBL;


    // mapping(address => eventManager) eventManagers; // Keep track of eventManagers (eventManagerAddr => eventManager)
    // address[] eventManagersList; // List of eventManagers


    function registerToPubSubService(address pubSubAddr, uint deposit) payable external returns(address) {
        require(deposit == msg.value, "Amount sent is different than specified");
        require(registeredToPubSub == false, "Publisher already registered to PubSubService"); // Assumes publisher can only register to a single pubsub service
        pubService = PubSubService(pubSubAddr);
        eventManagerAddress = address(pubService.register{value:msg.value}(deposit));
        registeredToPubSub = true;
        PubSubAddress = pubSubAddr;
        return eventManagerAddress;
    }


    function addToBlackList(address user) external payable {
        // require(registeredToPubSub == true, "Publisher not registered yet");
        // require(officialBL.members[user] == false, "User is already in blacklist");
        officialBL.memberList.push(user);
        officialBL.members[user] = true;
        EventManager(eventManagerAddress).notifyAddedToBlackList(user);
    }

    // From the white board, the state department will run this function
    function removeFromBlackList(address member) external payable {
        // require(registeredToPubSub == true, "Publisher not registered yet");
        // require(officialBL.members[member] == true, "User is not on blacklist");
        remove(officialBL.memberList, member);
        officialBL.members[member] = false;
        EventManager(eventManagerAddress).notifyRemoveFromBlackList(member);
    }

    // helper function to remove element from array
    function remove(address[] storage publisherList, address publisher) private  {
        require(publisherList.length > 0, "Received empty publisher list");
        for (uint i = 0; i < publisherList.length; i++){
            if (publisherList[i] == publisher) {
                publisherList[i] = publisherList[publisherList.length-1]; // remove element by overwriting previous index and removing the last index
                publisherList.pop();
            }
        }
    }
}
