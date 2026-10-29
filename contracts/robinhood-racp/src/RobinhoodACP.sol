// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @notice Custodial ACP receipt: 10 rACP per native ACP. No trustless cross-chain proof.
/// Reserve custody and ACP payouts are off-chain responsibilities of the issuer.
contract RobinhoodACP is ERC20 {
    uint256 public constant MAX_ISSUANCE = 10_000_000 ether;
    uint256 public constant RESERVE_ACP = 1_000_000;
    uint256 public constant RACP_PER_ACP = 10;
    address public immutable issuer;
    address public immutable recipient;
    bytes32 public reserveEvidence;
    bool public issued;
    uint256 public nextRedemptionId;

    event ReserveAttestedAndIssued(bytes32 indexed evidence, address indexed recipient, uint256 amount);
    event RedemptionRequested(uint256 indexed id, address indexed holder, uint256 amount, string acpAddress);
    error Unauthorized();
    error InvalidInput();
    error AlreadyIssued();

    constructor(address issuer_, address recipient_) ERC20("Robinhood ACP", "rACP") {
        if (issuer_ == address(0) || recipient_ == address(0)) revert InvalidInput();
        issuer = issuer_;
        recipient = recipient_;
    }

    /// @dev Single lifetime issuance. Evidence is an issuer attestation, not an on-chain ACP proof.
    /// Never call until 1,000,000 ACP is independently reserved exclusively for this issuance.
    function issueAgainstReserve(bytes32 evidence) external {
        if (msg.sender != issuer) revert Unauthorized();
        if (issued) revert AlreadyIssued();
        if (evidence == bytes32(0)) revert InvalidInput();
        issued = true;
        reserveEvidence = evidence;
        _mint(recipient, MAX_ISSUANCE);
        emit ReserveAttestedAndIssued(evidence, recipient, MAX_ISSUANCE);
    }

    /// @notice Burns rACP and requests a supervised ACP payout. Does not execute that payout.
    /// No re-mint after burn: total lifetime issuance cannot exceed MAX_ISSUANCE.
    function requestRedemption(uint256 amount, string calldata acpAddress) external {
        if (amount == 0 || bytes(acpAddress).length == 0 || bytes(acpAddress).length > 128) revert InvalidInput();
        // Native ACP has 8 decimals; prevent irredeemable fractional native amounts.
        if (amount % 100_000_000_000 != 0) revert InvalidInput();
        _burn(msg.sender, amount);
        emit RedemptionRequested(++nextRedemptionId, msg.sender, amount, acpAddress);
    }
}
