use acp_mobile_ffi::{
    acp_address_from_keystore, acp_address_from_mnemonic, acp_create_wallet, acp_import_wallet,
    acp_validate_address, CreatedWallet,
};

#[test]
fn create_wallet_roundtrip_via_keystore() {
    let CreatedWallet {
        address,
        mnemonic: _mnemonic,
        keystore_json,
    } = acp_create_wallet().expect("create");
    assert!(address.starts_with("acp1"));
    assert!(acp_validate_address(address.clone()));
    let again = acp_address_from_keystore(keystore_json).expect("keystore derive");
    assert_eq!(again, address);
}

/// Hybrid PQC Dilithium keygen is RNG-seeded once into keystore v3.
/// Mnemonic alone must NOT be treated as a full restore path (see WALLET_SPEC.md).
#[test]
fn mnemonic_alone_is_not_stable_restore() {
    let CreatedWallet {
        address,
        mnemonic,
        keystore_json,
    } = acp_create_wallet().expect("create");
    let from_ks = acp_address_from_keystore(keystore_json).expect("keystore");
    assert_eq!(from_ks, address);

    let from_mnemonic = acp_address_from_mnemonic(mnemonic.clone()).expect("mnemonic address");
    assert_ne!(
        from_mnemonic, address,
        "mnemonic-only derivation must stay distinct until Dilithium is deterministic"
    );
    let rebuilt = acp_import_wallet(mnemonic).expect("rebuild");
    assert_ne!(rebuilt.address, address);
}
