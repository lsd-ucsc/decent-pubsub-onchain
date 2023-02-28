// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfaceEventManager {
    function notify(address member) external;
}

contract Publisher {

    event MemberRemoved(address member, address eventManager);

    struct EventManager {
        address[] memberList; // keep list of registered publishers
        mapping(address => bool) members; // easy lookup into in memberList (publisher => bool)
        bool registered; // keep track if EventManager was registered
    }

    mapping(address => EventManager) EventManagers; // Keep track of EventManagers (eventManagerAddr => EventManager)
    address[] eventManagersList; // List of EventManagers

    // Note -- I don't think we need a constructor
    // constructor(address member1, address member2) {
        // members[member1] = true;
        // members[member2] = true;
    // }


    function registerEventManager(address eventManager) external {
        require(EventManagers[eventManager].registered == false, "Event manager already registered");
        EventManagers[eventManager].registered = true;
        eventManagersList.push(eventManager);
    }

    function addPublisher(address publisher, address eventManager) external {
        require(EventManagers[eventManager].registered == true, "Event manager not registered");
        require(EventManagers[eventManager].members[publisher] == false, "Publisher already added");
        EventManagers[eventManager].memberList.push(publisher);
        EventManagers[eventManager].members[publisher] == true;
    }

    function removePublisher(address member, address eventManager) external {
        require(EventManagers[eventManager].registered == true, "Event manager not registered");
        require(EventManagers[eventManager].members[publisher] == true, "Publisher not registered with EventManager");

        EventManagers[eventManager].memberList = remove(EventManagers[eventManager].memberList, member);
        EventManagers[eventManager].members[member] = false;
        emit MemberRemoved(member, eventManager);

        for (uint i = 0; i < EventManagers[eventManager].length; i++) {
            InterfaceEventManager(EventManagers[eventManager].memberList[i]).notify(member);
        }

    }

    // helper function to remove element from array
    function remove(address[] publisherList, address publisher)  returns(address[]) internal {
        require(publisherList.length > 0, "Received empty publisher list");
        for (uint i = 0; i < publisherList.length; i++){
            if (publisherList[i] == publisher) {
                publisherList[i] = publisherList[i+1]; // remove element by overwriting previous index and removing the last index
            }
        }
        delete publisherList[publisherList.length-1];
        publisherList.length--;
        return publisherList;
    }
}
