// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

interface IRacp {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address who) external view returns (uint256);
}

/// @notice Opt-in, signed allocations. One grant per authenticated eligibility ID AND wallet.
/// Wallet/account uniqueness is not proof of unique human identity.
contract RacpAirdrop {
    uint256 public constant GRANT = 500 ether;
    uint256 public constant BUDGET = 1_000_000 ether;
    bytes32 public constant CLAIM_TYPEHASH = keccak256("Claim(address recipient,bytes32 eligibilityId,uint256 deadline)");
    IRacp public immutable token;
    address public immutable owner;
    address public immutable signer;
    uint256 private immutable initialChainId;
    bytes32 private immutable initialDomain;
    mapping(address => bool) public claimed;
    mapping(bytes32 => bool) public claimedIdentity;
    uint256 public totalClaimed;
    bool public paused;

    event Claimed(address indexed recipient, bytes32 indexed eligibilityId, uint256 amount);
    event Paused(bool paused);
    error InvalidClaim();
    error Unauthorized();

    constructor(address token_, address signer_, address owner_) {
        if (token_ == address(0) || signer_ == address(0) || owner_ == address(0)) revert InvalidClaim();
        token = IRacp(token_); signer = signer_; owner = owner_;
        initialChainId = block.chainid;
        initialDomain = _domain();
    }
    function _domain() private view returns (bytes32) {
        return keccak256(abi.encode(
            keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
            keccak256("ANCAP rACP Airdrop"), keccak256("1"), block.chainid, address(this)
        ));
    }
    function claimDigest(address recipient, bytes32 eligibilityId, uint256 deadline) public view returns (bytes32) {
        bytes32 domain = block.chainid == initialChainId ? initialDomain : _domain();
        return keccak256(abi.encodePacked("\x19\x01", domain, keccak256(abi.encode(CLAIM_TYPEHASH, recipient, eligibilityId, deadline))));
    }
    /// Anyone may relay; the signed recipient always receives the fixed grant.
    function claim(address recipient, bytes32 eligibilityId, uint256 deadline, bytes calldata signature) external {
        if (paused || recipient == address(0) || eligibilityId == bytes32(0) || block.timestamp > deadline
            || claimed[recipient] || claimedIdentity[eligibilityId] || totalClaimed + GRANT > BUDGET) revert InvalidClaim();
        if (ECDSA.recover(claimDigest(recipient, eligibilityId, deadline), signature) != signer) revert Unauthorized();
        claimed[recipient] = true; claimedIdentity[eligibilityId] = true; totalClaimed += GRANT;
        require(token.transfer(recipient, GRANT), "token transfer");
        emit Claimed(recipient, eligibilityId, GRANT);
    }
    function setPaused(bool value) external {
        if (msg.sender != owner) revert Unauthorized();
        paused = value; emit Paused(value);
    }
    /// Recover only undistributed tokens when the campaign is explicitly stopped.
    function recoverUnclaimed() external {
        if (msg.sender != owner || !paused) revert Unauthorized();
        require(token.transfer(owner, token.balanceOf(address(this))), "token transfer");
    }
}
