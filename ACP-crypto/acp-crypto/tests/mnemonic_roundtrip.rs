//! BIP39 mnemonic → seed roundtrip.

use acp_crypto::Mnemonic;

#[test]
fn mnemonic_seed_remains_compatible_with_bip39_vector() {
    let mnemonic = Mnemonic::parse(
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
    )
    .expect("valid recovery phrase");
    assert_eq!(
        hex::encode(mnemonic.to_seed("TREZOR").as_bytes()),
        concat!(
            "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e5349553",
            "1f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04",
        ),
    );
}

#[test]
fn mnemonic_to_seed_roundtrip() {
    let m = Mnemonic::generate_12().expect("mnemonic");
    let words = m.words();
    let m2 = Mnemonic::parse(&words).expect("parse");
    let s1 = m.to_seed("");
    let s2 = m2.to_seed("");
    assert_eq!(s1.as_bytes(), s2.as_bytes());
}
