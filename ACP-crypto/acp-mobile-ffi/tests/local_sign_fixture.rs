//! Positive local-sign proof with synthetic UTXOs. No real node or broadcast.
use acp_crypto::{
    address_v0_from_pubkey_wire,
    protocol_params::{MIN_FEE_UNITS, UNITS_PER_ACP},
    TxHex,
};
use acp_mobile_ffi::{acp_create_wallet, acp_sign_transfer};
use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Read, Write},
    net::TcpListener,
    thread,
    time::{Duration, Instant},
};

#[test]
fn local_sign_binds_sender_recipient_amount_fee_and_network_without_funding() {
    let wallet = acp_create_wallet().expect("fixture wallet");
    let recipient = acp_create_wallet().expect("recipient").address;
    let listener = TcpListener::bind("127.0.0.1:0").expect("loopback only");
    listener.set_nonblocking(true).unwrap();
    let url = format!("http://{}", listener.local_addr().unwrap());
    let address = wallet.address.clone();
    let server = thread::spawn(move || {
        let deadline = Instant::now() + Duration::from_secs(20);
        let mut methods = Vec::new();
        let mut throttled = false;
        while methods.len() < 5 && Instant::now() < deadline {
            let (mut stream, _) = match listener.accept() {
                Ok(pair) => pair,
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(Duration::from_millis(5));
                    continue;
                }
                Err(e) => panic!("fixture accept: {e}"),
            };
            stream.set_nonblocking(false).unwrap();
            stream
                .set_read_timeout(Some(Duration::from_secs(5)))
                .unwrap();
            let mut reader = BufReader::new(stream.try_clone().unwrap());
            let mut content_length = 0;
            loop {
                let mut line = String::new();
                assert!(
                    reader.read_line(&mut line).unwrap() > 0,
                    "fixture client closed before headers"
                );
                if line == "\r\n" {
                    break;
                }
                if let Some((name, value)) = line.split_once(':') {
                    if name.eq_ignore_ascii_case("content-length") {
                        content_length = value.trim().parse::<usize>().unwrap();
                    }
                }
            }
            assert!(content_length < 4096);
            let mut bytes = vec![0; content_length];
            reader.read_exact(&mut bytes).unwrap();
            let request: Value = serde_json::from_slice(&bytes).unwrap();
            let method = request["method"].as_str().unwrap();
            if !throttled {
                assert_eq!(method, "getbestblockhash");
                write!(stream, "HTTP/1.1 503 Service Unavailable\r\nContent-Length: 4\r\nConnection: close\r\n\r\nbusy").unwrap();
                throttled = true;
                continue;
            }
            let result = match method {
                "getblock" if request["params"]["verbose"] == true => json!({"chain_id": 4242}),
                "getblockcount" => json!(1),
                "getbestblockhash" | "getblockhash" => json!("88".repeat(32)),
                "getblock" => json!({"tx": [{"txid": "11".repeat(32), "vin": [],
                    "vout": [{"recipient_address": address, "amount": 3 * UNITS_PER_ACP}]}]}),
                other => panic!("unexpected RPC, especially any broadcast: {other}"),
            };
            methods.push(method.to_string());
            let body = json!({"jsonrpc": "2.0", "id": 1, "result": result}).to_string();
            write!(stream, "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}", body.len(), body).unwrap();
        }
        methods
    });
    let signed = acp_sign_transfer(
        url,
        wallet.keystore_json,
        recipient.clone(),
        "1".into(),
        None,
    )
    .expect("sign synthetic UTXO locally");
    assert_eq!(
        server.join().unwrap(),
        [
            "getbestblockhash",
            "getblock",
            "getblockcount",
            "getblockhash",
            "getblock"
        ]
    );
    let tx = TxHex::decode_tx(&signed.raw_tx).expect("decode native output");
    tx.verify()
        .expect("independent hybrid signature verification");
    assert_eq!(tx.chain_id, 4242);
    assert_eq!(tx.inputs[0].prev_txid, [0x11; 32]);
    assert_eq!(tx.inputs[0].amount, 3 * UNITS_PER_ACP);
    assert_eq!(tx.outputs[0].recipient_address_bech32().unwrap(), recipient);
    assert_eq!(tx.outputs[0].amount, UNITS_PER_ACP);
    assert_eq!(tx.fee().unwrap(), MIN_FEE_UNITS);
    assert_eq!(
        tx.outputs[1].recipient_address_bech32().unwrap(),
        wallet.address
    );
    assert_eq!(
        address_v0_from_pubkey_wire(&tx.sender_pubkey_wire)
            .unwrap()
            .encode()
            .unwrap(),
        wallet.address
    );
    assert_eq!(TxHex::encode_txid(&tx.txid().unwrap()), signed.txid);
    let mut tampered = tx;
    tampered.chain_id += 1;
    assert!(
        tampered.verify().is_err(),
        "signature must bind the network"
    );
}
