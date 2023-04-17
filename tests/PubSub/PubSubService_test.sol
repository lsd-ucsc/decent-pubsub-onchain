// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;

// This import is automatically injected by Remix
import "remix_tests.sol";

// This import is required to use custom transaction context
// Although it may fail compilation in 'Solidity Compiler' plugin
// But it will work fine in 'Solidity Unit Testing' plugin
import "remix_accounts.sol";

import {PubSubService} from "../../PubSub/PubSubService.sol";
import {Interface_EventManager} from "../../PubSub/Interface_EventManager.sol";
import {Interface_PubSubService} from "../../PubSub/Interface_PubSubService.sol";
import {TestPublisher, TestSubscriber} from "./TestUtils.sol";


// File name has to end with '_test.sol', this file can contain more than one testSuite contracts
contract PubSubService_testSuite {

    /// 'beforeAll' runs before all other tests
    /// More special functions are: 'beforeEach', 'beforeAll', 'afterEach' & 'afterAll'
    function beforeAll() public {
    }

    function constructAndOwnerActions() public {
        try new PubSubService() {
            Assert.ok(true, "PubSubService deployed");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(false, "PubSubService deployment failed");
        }
    }

    function registerPublisher() public {
        PubSubService pubSubService = new PubSubService();
        address pubSubServiceAddr = address(pubSubService);

        // first publisher

        address publisherAddr1 = address(new TestPublisher());
        address expEventMgrAddr1;

        try TestPublisher(publisherAddr1).register(pubSubServiceAddr)
            returns (address addr)
        {
            expEventMgrAddr1 = addr;
            Assert.ok(true, "Publisher registered");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(false, "Publisher registration failed");
        }

        address actEventMgrAddr1;

        try Interface_PubSubService(
            pubSubServiceAddr
        ).getEventManagerAddr(publisherAddr1) returns (address addr) {
            actEventMgrAddr1 = addr;
            Assert.ok(true, "Event manager address retrieved");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(false, "Event manager address retrieval failed");
        }

        Assert.equal(
            actEventMgrAddr1,
            expEventMgrAddr1,
            "Event manager address matches"
        );

        // second publisher

        address publisherAddr2 = address(new TestPublisher());
        address expEventMgrAddr2;

        try TestPublisher(publisherAddr2).register(pubSubServiceAddr)
            returns (address addr)
        {
            expEventMgrAddr2 = addr;
            Assert.ok(true, "Publisher registered");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(false, "Publisher registration failed");
        }

        address actEventMgrAddr2;

        try Interface_PubSubService(
            pubSubServiceAddr
        ).getEventManagerAddr(publisherAddr2) returns (address addr) {
            actEventMgrAddr2 = addr;
            Assert.ok(true, "Event manager address retrieved");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(false, "Event manager address retrieval failed");
        }

        Assert.equal(
            actEventMgrAddr2,
            expEventMgrAddr2,
            "Event manager address matches"
        );

        // two event managers are different
        Assert.notEqual(
            actEventMgrAddr1,
            actEventMgrAddr2,
            "Event manager addresses should be different"
        );

        // publisher 1 cannot register for another event manager
        try TestPublisher(publisherAddr1).register(pubSubServiceAddr) {
            Assert.ok(false, "Publisher 1 should not be able to register again");
        } catch Error(string memory reason) {
            Assert.equal(reason, "Publisher already registered", reason);
        } catch (bytes memory) {
            Assert.ok(
                false,
                "Unexpected error occurred while registering publisher 1 again"
            );
        }

        // getting event manager address for unrecognized publisher
        try Interface_PubSubService(
            pubSubServiceAddr
        ).getEventManagerAddr(address(this)) {
            Assert.ok(
                false,
                "Unrecognized publisher should not have event manager address"
            );
        } catch Error(string memory reason) {
            Assert.equal(reason, "Publisher not registered", reason);
        } catch (bytes memory) {
            Assert.ok(
                false,
                "Unexpected error occurred while getting event manager address "
                "for unrecognized publisher"
            );
        }
    }

    /// #value: 200000000
    function subscribe() public payable {
        Assert.equal(msg.value, 200000000, "msg.value not set correctly");

        // PubSubService
        PubSubService pubSubService = new PubSubService();
        address pubSubServiceAddr = address(pubSubService);

        // Publisher
        TestPublisher publisher = new TestPublisher();
        publisher.register(pubSubServiceAddr);
        address publisherAddr = address(publisher);

        // Subscriber
        TestSubscriber subscriber = new TestSubscriber();

        // A sccessful subscription
        try subscriber.subscribe{
            value: 100000000
        }(pubSubServiceAddr, publisherAddr) {
            Assert.ok(true, "Subscriber subscribed");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(false, "Unexpected error occurred while subscribing");
        }
        // check subscriber balance
        try Interface_EventManager(
            Interface_PubSubService(pubSubServiceAddr).getEventManagerAddr(
                publisherAddr
            )
        ).subscriberCheckBalance(address(subscriber)) returns (uint256 balance) {
            Assert.equal(balance, 100000000, "Subscriber balance is correct");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch (bytes memory) {
            Assert.ok(
                false,
                "Unexpected error occurred while getting subscriber balance"
            );
        }

        // subscribe to unknown publisher
        try subscriber.subscribe{
            value: 100000000
        }(pubSubServiceAddr, address(this)) {
            Assert.ok(
                false,
                "Subscriber should not be able to subscribe to unknown publisher"
            );
        } catch Error(string memory reason) {
            Assert.equal(reason, "Publisher not registered", reason);
        } catch (bytes memory) {
            Assert.ok(
                false,
                "Unexpected error occurred while subscribing to unknown publisher"
            );
        }
    }
}
