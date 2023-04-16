// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;

// This import is automatically injected by Remix
import "remix_tests.sol";

// This import is required to use custom transaction context
// Although it may fail compilation in 'Solidity Compiler' plugin
// But it will work fine in 'Solidity Unit Testing' plugin
import "remix_accounts.sol";

import {EventManager, Interface_Subscriber} from "../../PubSub/EventManager.sol";
import {Interface_EventManager} from "../../PubSub/Interface_EventManager.sol";
import {DummyContract, TestSubscriber} from "./TestUtils.sol";


// File name has to end with '_test.sol', this file can contain more than one testSuite contracts
contract EventManager_testSuite {

    /// 'beforeAll' runs before all other tests
    /// More special functions are: 'beforeEach', 'beforeAll', 'afterEach' & 'afterAll'
    function beforeAll() public {
    }

    function constructAndOwnerActions() public {
        // Create a new EventManager contract
        EventManager eventMgrInst1 = new EventManager(address(this));
        address eventMgr1Addr = address(eventMgrInst1);
        DummyContract dummyContract1 = new DummyContract();
        address dummyAddr1 = address(dummyContract1);

        // update incentive
        try Interface_EventManager(eventMgr1Addr).updateIncentive(1000) {
            Assert.ok(true, "Owner can update incentive");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Unexpected error occurred while updating incentive");
        }
        // add publisher
        try Interface_EventManager(eventMgr1Addr).addPublisher(address(this)) {
            Assert.ok(true, "Owner can add publishers");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Unexpected error occurred while adding publisher");
        }

        // Not owner -> should fail
        EventManager eventMgrInst2 = new EventManager(dummyAddr1);
        address eventMgr2Addr = address(eventMgrInst2);

        // update incentive
        try Interface_EventManager(eventMgr2Addr).updateIncentive(1000) {
            Assert.ok(false, "Only the owner can update incentive");
        } catch Error(string memory reason) {
            Assert.equal(reason, "Only the owner can update the incentive", reason);
        } catch {
            Assert.ok(false, "Unexpected error occurred while updating incentive");
        }

        // add publisher
        try Interface_EventManager(eventMgr2Addr).addPublisher(address(this)) {
            Assert.ok(false, "Only the owner can add publishers");
        } catch Error(string memory reason) {
            Assert.equal(reason, "Only the owner can add publishers", reason);
        } catch {
            Assert.ok(false, "Unexpected error occurred while adding publisher");
        }
    }

    /// #value: 900000000
    function addSubscriber() public payable {
        Assert.equal(msg.value, 900000000, "Incorrect value sent to contract");

        // Create a new EventManager contract
        EventManager eventMgrInst1 = new EventManager(address(this));
        address eventMgr1Addr = address(eventMgrInst1);

        // add subscriber with low deposit -> should fail
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: (100000000 - 1)
        }(address(this)) {
            Assert.ok(false, "Successfully added subscriber with low deposit");
        } catch Error(string memory reason) {
            Assert.equal(reason, "You need to send at least the minimum deposit", reason);
        } catch {
            Assert.ok(false, "Unexpected error occurred while adding subscriber");
        }

        // add subscriber
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: 100000000
        }(address(this)) {
            Assert.ok(true, "Subscriber added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Failed to add subscriber");
        }
        // the balance of the event manager should be 100000000
        Assert.equal(
            address(eventMgrInst1).balance, 100000000,
            "Incorrect contract balance after add subscriber"
        );

        // add subscriber again -> should fail
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: 100000000
        }(address(this)) {
            Assert.ok(false, "Successfully added subscriber twice");
        } catch Error(string memory reason) {
            Assert.equal(reason, "Subscriber already added", reason);
        } catch {
            Assert.ok(false, "Unexpected error occurred while adding subscriber");
        }

        Assert.equal(
            address(eventMgrInst1).balance, 100000000,
            "contract balance should remain the same after failed operations"
        );
    }

    /// #value: 900000000
    function subscriberAddAndCheckBalance() public payable {
        Assert.equal(msg.value, 900000000, "Incorrect value sent to contract");

        // Create a new EventManager contract
        EventManager eventMgrInst1 = new EventManager(address(this));
        address eventMgr1Addr = address(eventMgrInst1);
        DummyContract dummyContract1 = new DummyContract();
        address dummyAddr1 = address(dummyContract1);
        DummyContract dummyContract2 = new DummyContract();
        address dummyAddr2 = address(dummyContract2);
        DummyContract dummyContract3 = new DummyContract();
        address dummyAddr3 = address(dummyContract3);

        // add subscriber 1
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: 100000000
        }(dummyAddr1) {
            Assert.ok(true, "Subscriber added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Failed to add subscriber");
        }
        Assert.equal(
            address(eventMgrInst1).balance, 100000000,
            "Incorrect contract balance after add subscriber"
        );
        // add subscriber 2
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: 100000000
        }(dummyAddr2) {
            Assert.ok(true, "Subscriber added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Failed to add subscriber");
        }
        Assert.equal(
            address(eventMgrInst1).balance, 200000000,
            "Incorrect contract balance after add subscriber"
        );

        // add balance to subscriber 1
        try Interface_EventManager(eventMgr1Addr).subscriberAddBalance{
            value: 100000000
        }(dummyAddr1) {
            Assert.ok(true, "Balance added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Failed to add balance");
        }
        Assert.equal(
            address(eventMgrInst1).balance, 300000000,
            "Incorrect contract balance after subscriber add balance"
        );
        // add balance to subscriber 2
        try Interface_EventManager(eventMgr1Addr).subscriberAddBalance{
            value: 100000000
        }(dummyAddr2) {
            Assert.ok(true, "Balance added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Failed to add balance");
        }
        Assert.equal(
            address(eventMgrInst1).balance, 400000000,
            "Incorrect contract balance after subscriber add balance"
        );

        // check balance of subscriber 1
        uint balance = Interface_EventManager(
            eventMgr1Addr
        ).subscriberCheckBalance(dummyAddr1);
        Assert.equal(
            balance, 200000000,
            "Incorrect balance after subscriber checking balance"
        );
        // check balance of subscriber 2
        balance = Interface_EventManager(
            eventMgr1Addr
        ).subscriberCheckBalance(dummyAddr2);
        Assert.equal(
            balance, 200000000,
            "Incorrect balance after subscriber checking balance"
        );

        // add balance to subscriber 3 -> should fail
        try Interface_EventManager(eventMgr1Addr).subscriberAddBalance{
            value: 100000000
        }(dummyAddr3) {
            Assert.ok(false, "Balance should not be added to unknown subscriber");
        } catch Error(string memory reason) {
            Assert.equal(reason, "Subscriber is not found", reason);
        } catch {
            Assert.ok(
                false,
                "Unexpected error when adding balance to unknown subscriber"
            );
        }

        // check balance of subscriber 3 -> should fail
        try Interface_EventManager(
            eventMgr1Addr
        ).subscriberCheckBalance(dummyAddr3) {
            Assert.ok(
                false,
                "Successfully checked balance for an unknown subscriber"
            );
        } catch Error(string memory reason) {
            Assert.equal(reason, "Subscriber is not found", reason);
        } catch {
            Assert.ok(
                false,
                "Unexpected error when checking balance to unknown subscriber"
            );
        }

        Assert.equal(
            address(eventMgrInst1).balance, 400000000,
            "contract balance should remain the same after failed operations"
        );
    }

    /// #value: 2000000000000000000
    function notifySubscribers() public payable {
        Assert.equal(
            msg.value,
            2000000000000000000,
            "Incorrect value sent to contract"
        );

        // Create a new EventManager contract
        EventManager eventMgrInst1 = new EventManager(address(this));
        address eventMgr1Addr = address(eventMgrInst1);
        TestSubscriber testSubscriber1 = new TestSubscriber();
        address subsAddr1 = address(testSubscriber1);
        TestSubscriber testSubscriber2 = new TestSubscriber();
        address subsAddr2 = address(testSubscriber2);

        // testing input bytes
        bytes memory testInput = "Hello World";

        // add subscriber 1
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: 1000000000000000000
        }(subsAddr1) {
            Assert.ok(true, "Subscriber added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Unexpected error when adding subscriber 1");
        }
        // add subscriber 2
        try Interface_EventManager(eventMgr1Addr).addSubscriber{
            value: 1000000000000000000
        }(subsAddr2) {
            Assert.ok(true, "Subscriber added");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Unexpected error when adding subscriber 2");
        }

        // get expected gas cost of the onNotify function
        uint expGasCost = 0;
        Interface_Subscriber(subsAddr1).onNotify(""); // reset recvData
        Interface_Subscriber(subsAddr2).onNotify(""); // reset recvData
        expGasCost = gasleft();
        Interface_Subscriber(subsAddr1).onNotify(testInput);
        expGasCost -= gasleft();
        Interface_Subscriber(subsAddr1).onNotify(""); // reset recvData
        Interface_Subscriber(subsAddr2).onNotify(""); // reset recvData
        // calculate expected total cost (gas cost + incentive)
        // uint expCostWei = (expGasCost * tx.gasprice) + (1000000 / 2);

        uint senderOriBalance = payable(tx.origin).balance;

        // notify subscribers
        try Interface_EventManager(eventMgr1Addr).notifySubscribers(testInput) {
            Assert.ok(true, "Subscribers notified");
        } catch Error(string memory reason) {
            Assert.ok(false, reason);
        } catch {
            Assert.ok(false, "Unexpected error when notifying subscribers");
        }

        uint senderNewBalance = payable(tx.origin).balance;

        // check if subscribers received the notification
        Assert.ok(
            keccak256(testSubscriber1.m_recvData()) == keccak256(testInput),
            "Subscriber 1 did not receive the notification"
        );
        Assert.ok(
            keccak256(testSubscriber2.m_recvData()) == keccak256(testInput),
            "Subscriber 2 did not receive the notification"
        );

        // check balance of subscriber 1
        uint balance = Interface_EventManager(
            eventMgr1Addr
        ).subscriberCheckBalance(subsAddr1);
        uint actCost1Wei = 1000000000000000000 - balance;
        // check balance of subscriber 2
        balance = Interface_EventManager(
            eventMgr1Addr
        ).subscriberCheckBalance(subsAddr2);
        uint actCost2Wei = 1000000000000000000 - balance;
        uint actTotalCostWei = 2000000000000000000 - address(eventMgrInst1).balance;

        Assert.ok(actCost1Wei > 0, "Subscriber 1 has not cost");
        Assert.ok(actCost2Wei > 0, "Subscriber 2 has not cost");
        Assert.ok(actTotalCostWei > 0, "Contract has not cost");
        Assert.equal(actTotalCostWei, actCost1Wei + actCost2Wei, "Total cost not match");
        Assert.ok(
            senderNewBalance > senderOriBalance,
            "The sender didn't get reimbursed"
        );
        Assert.equal(
            actTotalCostWei,
            senderNewBalance - senderOriBalance,
            "Reimbursement amount doesn't match"
        );
        // Assert.equal(actCost1Wei, actCost2Wei, "Subscriber 1 & 2 have different cost");
        // Assert.equal(
        //     actCost1Wei, expCostWei,
        //     "Incorrect balance after subscriber 1 received the notification"
        // );
        // Assert.equal(
        //     actCost2Wei, expCostWei,
        //     "Incorrect balance after subscriber 2 received the notification"
        // );
    }
}
