// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;



interface InterfacePubSubService {
    function register() external returns(InterfaceEventManager);
}


interface InterfaceEventManager {
    function addSubscriber(address publisher_addr, uint subscribeContractAddr) external payable;
    function notify(bytes memory data) external;
}

contract Publisher {
    enum Action { ADD_TO_BLACKLIST, DELETE_FROM_BLACKLIST } // Types of actions

    struct BlackList {
        address[] memberList; // keep list of blacklist addresses
        mapping(address => bool) members; // easy lookup into in memberList (publisher => bool)
    }

    bool public registeredToPubSub = false;
    address public PubSubAddress;
    address public eventManagerAddress;
    InterfacePubSubService pubService;

    BlackList officialBL; // getting weird errors, so the key is eventManagerAddress


    // mapping(address => eventManager) eventManagers; // Keep track of eventManagers (eventManagerAddr => eventManager)
    // address[] eventManagersList; // List of eventManagers

    function registerToPubSubService(address pubSubAddr) payable external returns(address) {

        require(registeredToPubSub == false, "Publisher already registered to PubSubService"); // Assumes publisher can only register to a single pubsub service
        pubService = InterfacePubSubService(pubSubAddr);
        eventManagerAddress = address(pubService.register()); // TODO: Specify what kind of event types. e.g.,
        registeredToPubSub = true;
        PubSubAddress = pubSubAddr;
        return eventManagerAddress;
    }


    function addToBlackList(address user) public  {
        require(registeredToPubSub == true, "Publisher not registered yet");
        require(officialBL.members[user] == false, "User is already in blacklist");
        officialBL.memberList.push(user);
        officialBL.members[user] = true;
        InterfaceEventManager(eventManagerAddress).notify(encodeAction(Action.ADD_TO_BLACKLIST, user));
    }

    function viewBlackList() public view returns(address[] memory) {
        return officialBL.memberList;
    }


    function removeFromBlackList(address member) public {
        require(registeredToPubSub == true, "Publisher not registered yet");
        require(officialBL.members[member] == true, "User is not on blacklist");
        remove(officialBL.memberList, member);
        officialBL.members[member] = false;
        InterfaceEventManager(eventManagerAddress).notify(encodeAction(Action.DELETE_FROM_BLACKLIST, member));
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
        officialBL.members[publisher] = false;
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function encodeAction(Action action, address user) internal pure returns (bytes memory) {
        bytes memory data = abi.encode(action, user);
        return data;
    }


    // Receive function - called when ether is sent directly to the contract address
    receive() external payable {
        // payable(owen_wallet).transfer(msg.value);
    }

    //     // Fallback function - called when no other function matches the function signature
    // fallback() external payable {}
}
