//! ACP mobile wallet core — UniFFI exports for iOS/Android.

mod wallet_core;

pub use wallet_core::{
    acp_address_from_keystore, acp_address_from_mnemonic, acp_create_wallet, acp_estimate_fee_default,
    acp_import_mnemonic, acp_import_wallet, acp_sign_transfer, acp_validate_address,
    acp_encrypt_keystore, acp_decrypt_keystore, AcpWalletException,
    CreatedWallet, FeeEstimate, SignedTransfer,
};

#[uniffi::export]
fn acp_encrypt_keystore_ffi(keystore_json: String, password: String) -> Result<String, AcpWalletException> {
    wallet_core::acp_encrypt_keystore(keystore_json, password)
}

#[uniffi::export]
fn acp_decrypt_keystore_ffi(backup_json: String, password: String) -> Result<String, AcpWalletException> {
    wallet_core::acp_decrypt_keystore(backup_json, password)
}

#[uniffi::export]
fn acp_create_wallet_ffi() -> Result<CreatedWallet, AcpWalletException> {
    wallet_core::acp_create_wallet()
}

#[uniffi::export]
fn acp_validate_address_ffi(address: String) -> bool {
    wallet_core::acp_validate_address(address)
}

#[uniffi::export]
fn acp_address_from_keystore_ffi(keystore_json: String) -> Result<String, AcpWalletException> {
    wallet_core::acp_address_from_keystore(keystore_json)
}

#[uniffi::export]
fn acp_estimate_fee_default_ffi() -> Result<FeeEstimate, AcpWalletException> {
    wallet_core::acp_estimate_fee_default()
}

#[uniffi::export]
fn acp_sign_transfer_ffi(
    rpc_url: String,
    keystore_json: String,
    to_address: String,
    amount_acp: String,
    fee_acp: Option<String>,
) -> Result<SignedTransfer, AcpWalletException> {
    wallet_core::acp_sign_transfer(rpc_url, keystore_json, to_address, amount_acp, fee_acp)
}

uniffi::setup_scaffolding!();
