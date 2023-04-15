// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

// Import EventManager Code
import {EventManager} from "./EventManager.sol";


contract PubSubService {

    //===== structs =====

    struct MappedEventManager {
        bool    init;
        address addr;
    }

    //===== Member variables =====

    mapping(address => MappedEventManager) m_eventManagerMap;

    //===== Events =====

    event ServiceDeployed(address indexed serviceAddr);
    event PublisherRegistered(address pubAddr, address eventMgrAddr);

    //===== Constructor =====

    constructor() {
        emit ServiceDeployed(address(this));
    }

    //===== external Functions =====

    /**
     * Register a publisher with the PubSubService and spawn a new
     * corresponding EventManager contract
     * @return address The address of the newly created EventManager contract
     * @dev The publisher must call this function to register
     */
    function register() external returns (address) {
        // 1. publisher address
        address publisherAddr = msg.sender;

        // 2. make sure the publisher has not already registered
        require(
            m_eventManagerMap[publisherAddr].init == false,
            "Publisher already registered"
        );

        // 3. Create a new EventManager contract
        EventManager eventMgrInst = new EventManager(publisherAddr);
        address eventMgrAddr = address(eventMgrInst);

        // 4. update the mapping
        m_eventManagerMap[publisherAddr] = MappedEventManager({
            init: true,
            addr: eventMgrAddr
        });

        // 5. emit event
        emit PublisherRegistered(publisherAddr, eventMgrAddr);

        // 6. return the EventManager contract address
        return eventMgrAddr;
    }

    /**
     * Subscribe a subscriber to a publisher's event manager
     * @param publisherAddr The address of the publisher
     * @param deposit The amount of ETH to deposit
     */
    function subscribe(address publisherAddr, uint256 deposit) external payable {
        // 1. make sure the publisher has already registered
        require(
            m_eventManagerMap[publisherAddr].init == true,
            "Publisher not registered"
        );

        // 2. make sure the subscriber has deposited the correct amount
        require(msg.value > 0, "Deposity > 0");
        require(msg.value == deposit, "Deposit what you specify");

        // 3. get the EventManager contract address
        address eventMgrAddr = m_eventManagerMap[publisherAddr].addr;
        address subscriberAddr = msg.sender;

        // 4. add the subscriber to the event manager
        EventManager(eventMgrAddr).addSubscriber{
            value: msg.value
        }(subscriberAddr);
    }

    /**
     * Get the EventManager contract address for a publisher
     * @param publisherAddr The address of the publisher
     * @return address The address of the EventManager contract
     */
    function getEventManagerAddr(address publisherAddr) external view returns (address) {
        // 1. make sure the publisher has already registered
        require(
            m_eventManagerMap[publisherAddr].init == true,
            "Publisher not registered"
        );

        // 2. return the EventManager contract address
        return m_eventManagerMap[publisherAddr].addr;
    }

}
