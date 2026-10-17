//! Dev-only helper: write keystore JSON to a path; print address only (never seed).
//! Usage: cargo run -p acp-mobile-ffi --example export_keystore_smoke -- <out.json>

use acp_mobile_ffi::{acp_address_from_keystore, acp_create_wallet};
use std::env;
use std::fs;
use std::process::ExitCode;

fn main() -> ExitCode {
    let out = match env::args().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: export_keystore_smoke <out.json>");
            return ExitCode::from(2);
        }
    };
    let wallet = match acp_create_wallet() {
        Ok(w) => w,
        Err(e) => {
            eprintln!("create failed: {e:?}");
            return ExitCode::from(1);
        }
    };
    if let Err(e) = fs::write(&out, wallet.keystore_json.as_bytes()) {
        eprintln!("write failed: {e}");
        return ExitCode::from(1);
    }
    let again = match acp_address_from_keystore(wallet.keystore_json) {
        Ok(a) => a,
        Err(e) => {
            eprintln!("keystore derive failed: {e:?}");
            return ExitCode::from(1);
        }
    };
    if again != wallet.address {
        eprintln!("keystore roundtrip mismatch");
        return ExitCode::from(1);
    }
    println!("{}", wallet.address);
    println!("keystore_roundtrip=ok");
    ExitCode::SUCCESS
}
