// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {RobinhoodACP} from "../src/RobinhoodACP.sol";

contract OtherCaller {
    function issue(RobinhoodACP token) external { token.issueAgainstReserve(bytes32(uint256(1))); }
}

contract RobinhoodACPTest {
    function testZeroSupplyBeforeReserve() public {
        RobinhoodACP token = new RobinhoodACP(address(this), address(this));
        require(token.totalSupply() == 0);
        require(keccak256(bytes(token.symbol())) == keccak256("rACP"));
    }
    function testIssueOnceAndRedeemWithoutRemint() public {
        RobinhoodACP token = new RobinhoodACP(address(this), address(this));
        token.issueAgainstReserve(bytes32(uint256(1)));
        require(token.totalSupply() == 10_000_000 ether);
        token.requestRedemption(10 ether, "acp-reserve-payout-test");
        require(token.totalSupply() == 9_999_990 ether);
        (bool ok,) = address(token).call(abi.encodeCall(token.issueAgainstReserve, (bytes32(uint256(2)))));
        require(!ok);
    }
    function testRejectUnauthorizedAndEmptyEvidence() public {
        RobinhoodACP token = new RobinhoodACP(address(this), address(this));
        OtherCaller other = new OtherCaller();
        (bool ok,) = address(other).call(abi.encodeCall(other.issue, (token)));
        require(!ok);
        (ok,) = address(token).call(abi.encodeCall(token.issueAgainstReserve, (bytes32(0))));
        require(!ok);
        require(token.totalSupply() == 0);
    }
    function testTransfersAndInvalidRedemptions() public {
        RobinhoodACP token = new RobinhoodACP(address(this), address(this));
        token.issueAgainstReserve(bytes32(uint256(1)));
        token.transfer(address(123), 1 ether);
        require(token.balanceOf(address(123)) == 1 ether);
        (bool ok,) = address(token).call(abi.encodeCall(token.requestRedemption, (uint256(1), "acp-test")));
        require(!ok);
        (ok,) = address(token).call(abi.encodeCall(token.requestRedemption, (uint256(1 ether), "")));
        require(!ok);
    }
}
