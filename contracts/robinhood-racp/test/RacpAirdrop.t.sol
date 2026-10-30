// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {RobinhoodACP} from "../src/RobinhoodACP.sol";
import {RacpAirdrop} from "../src/RacpAirdrop.sol";

interface VmAirdrop {
    function addr(uint256 key) external returns (address);
    function sign(uint256 key, bytes32 digest) external returns (uint8 v, bytes32 r, bytes32 s);
    function warp(uint256 time) external;
}
contract RacpAirdropTest {
    VmAirdrop constant vm = VmAirdrop(address(uint160(uint256(keccak256("hevm cheat code")))));
    RobinhoodACP token;
    RacpAirdrop pool;
    uint256 constant KEY = 12345;
    function setUp() public {
        token = new RobinhoodACP(address(this), address(this));
        token.issueAgainstReserve(bytes32(uint256(1)));
        pool = new RacpAirdrop(address(token), vm.addr(KEY), address(this));
        token.transfer(address(pool), 1_000_000 ether);
    }
    function signature(RacpAirdrop target, address recipient, bytes32 id, uint256 deadline) internal returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(KEY, target.claimDigest(recipient, id, deadline));
        return abi.encodePacked(r, s, v);
    }
    function testRelayerCannotRedirectAndReplayFails() public {
        address recipient = address(123);
        bytes memory sig = signature(pool, recipient, bytes32(uint256(1)), block.timestamp + 100);
        (bool ok,) = address(pool).call(abi.encodeCall(pool.claim, (address(456), bytes32(uint256(1)), block.timestamp + 100, sig)));
        require(!ok);
        pool.claim(recipient, bytes32(uint256(1)), block.timestamp + 100, sig);
        require(token.balanceOf(recipient) == 500 ether && pool.totalClaimed() == 500 ether);
        (ok,) = address(pool).call(abi.encodeCall(pool.claim, (recipient, bytes32(uint256(1)), block.timestamp + 100, sig)));
        require(!ok);
    }
    function testIdentityCannotClaimToSecondWallet() public {
        bytes32 id = bytes32(uint256(7));
        pool.claim(address(1), id, block.timestamp + 100, signature(pool, address(1), id, block.timestamp + 100));
        (bool ok,) = address(pool).call(abi.encodeCall(pool.claim, (address(2), id, block.timestamp + 100, signature(pool, address(2), id, block.timestamp + 100))));
        require(!ok);
    }
    function testCrossContractAndExpiredSignatureFail() public {
        uint256 deadline = block.timestamp + 100;
        bytes memory sig = signature(pool, address(1), bytes32(uint256(1)), deadline);
        RacpAirdrop other = new RacpAirdrop(address(token), vm.addr(KEY), address(this));
        (bool ok,) = address(other).call(abi.encodeCall(other.claim, (address(1), bytes32(uint256(1)), deadline, sig)));
        require(!ok);
        vm.warp(deadline + 1);
        (ok,) = address(pool).call(abi.encodeCall(pool.claim, (address(1), bytes32(uint256(1)), deadline, sig)));
        require(!ok);
    }
    function testPauseAndUnfundedTransferDoNotConsumeClaim() public {
        bytes memory sig = signature(pool, address(1), bytes32(uint256(1)), block.timestamp + 100);
        pool.setPaused(true);
        (bool ok,) = address(pool).call(abi.encodeCall(pool.claim, (address(1), bytes32(uint256(1)), block.timestamp + 100, sig)));
        require(!ok && !pool.claimed(address(1)));
        pool.recoverUnclaimed(); pool.setPaused(false);
        (ok,) = address(pool).call(abi.encodeCall(pool.claim, (address(1), bytes32(uint256(1)), block.timestamp + 100, sig)));
        require(!ok && !pool.claimed(address(1)) && pool.totalClaimed() == 0);
    }
    function testBudgetStopsAtTwoThousandEvenIfOverfunded() public {
        token.transfer(address(pool), 500 ether);
        uint256 deadline = block.timestamp + 100;
        for (uint256 i = 1; i <= 2000; i++) {
            address recipient = address(uint160(i + 10000));
            pool.claim(recipient, bytes32(i), deadline, signature(pool, recipient, bytes32(i), deadline));
        }
        address next = address(30000);
        (bool ok,) = address(pool).call(abi.encodeCall(pool.claim, (next, bytes32(uint256(2001)), deadline,
            signature(pool, next, bytes32(uint256(2001)), deadline))));
        require(!ok && !pool.claimed(next) && pool.totalClaimed() == 1_000_000 ether);
        require(token.balanceOf(address(pool)) == 500 ether);
    }
}
