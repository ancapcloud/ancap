use acp_mobile_ffi::{
    acp_address_from_keystore, acp_address_from_mnemonic, acp_create_wallet, acp_import_wallet,
    acp_validate_address, CreatedWallet,
};

#[test]
fn encrypted_backup_roundtrip_and_wrong_password() {
    use acp_mobile_ffi::{acp_encrypt_keystore, acp_decrypt_keystore};
    let wallet = acp_create_wallet().expect("create");
    let password = "test-only-long-password".to_string();
    let encrypted = acp_encrypt_keystore(wallet.keystore_json.clone(), password.clone())
        .unwrap_or_else(|e| panic!("encrypt {} bytes: {e}", wallet.keystore_json.len()));
    assert!(!encrypted.contains("spend_ed25519_seed32"));
    assert!(!encrypted.contains("spend_dilithium_sk"));
    assert!(acp_decrypt_keystore(encrypted.clone(), "wrong-password".into()).is_err());
    let plain = acp_decrypt_keystore(encrypted.clone(), password.clone()).expect("decrypt");
    assert_eq!(acp_address_from_keystore(plain).expect("address"), wallet.address);
    let mut corrupted: serde_json::Value = serde_json::from_str(&encrypted).unwrap();
    corrupted["crypto"]["ciphertext_b64"] = serde_json::json!("AAAA");
    assert!(acp_decrypt_keystore(corrupted.to_string(), password.clone()).is_err());
    assert!(acp_encrypt_keystore(wallet.keystore_json, "short".into()).is_err());
    corrupted["crypto"]["mem_kib"] = serde_json::json!(1);
    assert!(acp_decrypt_keystore(corrupted.to_string(), password).is_err());
}

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
