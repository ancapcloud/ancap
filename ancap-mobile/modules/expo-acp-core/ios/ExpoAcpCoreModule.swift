import ExpoModulesCore

#if canImport(acp_mobile_ffiFFI)
import acp_mobile_ffiFFI
#endif

private func acpNativeAvailabilityMessage() -> String {
  "ACP native core is not linked on iOS yet. Run ancap-mobile/scripts/build-ios-native.ps1 on macOS to stage the UniFFI bindings and package acp_mobile_ffiFFI.xcframework, then rebuild the Expo dev client. Use Import wallet until native iOS wiring is finished."
}

private func requireAcpNativeLinked() throws {
  #if canImport(acp_mobile_ffiFFI)
  return
  #else
  throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
  #endif
}

#if canImport(acp_mobile_ffiFFI)
private func mapWalletError(_ error: AcpWalletException) -> Exception {
  switch error {
  case .InvalidAddress:
    return Exception(name: "ERR_INVALID_ADDRESS", description: error.localizedDescription)
  case .InvalidMnemonic:
    return Exception(name: "ERR_INVALID_MNEMONIC", description: error.localizedDescription)
  case .InvalidAmount:
    return Exception(name: "ERR_INVALID_AMOUNT", description: error.localizedDescription)
  case .InsufficientFunds:
    return Exception(name: "ERR_INSUFFICIENT_FUNDS", description: error.localizedDescription)
  case .Rpc(let message):
    return Exception(name: "ERR_RPC", description: message)
  case .Internal(let message):
    return Exception(name: "ERR_INTERNAL", description: message)
  @unknown default:
    return Exception(name: "ERR_INTERNAL", description: error.localizedDescription)
  }
}
#endif

public class ExpoAcpCoreModule: Module {
  public func definition() -> ModuleDefinition {
    Name("ExpoAcpCore")

    AsyncFunction("encryptKeystore") { (keystoreJson: String, password: String) -> String in
      try requireAcpNativeLinked()
      #if canImport(acp_mobile_ffiFFI)
      do { return try acpEncryptKeystoreFfi(keystoreJson: keystoreJson, password: password) }
      catch let error as AcpWalletException { throw mapWalletError(error) }
      #else
      throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
      #endif
    }

    AsyncFunction("decryptKeystore") { (backupJson: String, password: String) -> String in
      try requireAcpNativeLinked()
      #if canImport(acp_mobile_ffiFFI)
      do { return try acpDecryptKeystoreFfi(backupJson: backupJson, password: password) }
      catch let error as AcpWalletException { throw mapWalletError(error) }
      #else
      throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
      #endif
    }

    AsyncFunction("createWallet") { () -> [String: Any] in
      try requireAcpNativeLinked()
      #if canImport(acp_mobile_ffiFFI)
      do {
        let wallet = try acpCreateWalletFfi()
        return [
          "address": wallet.address,
          "mnemonic": wallet.mnemonic,
          "keystoreJson": wallet.keystoreJson,
        ]
      } catch let error as AcpWalletException {
        throw mapWalletError(error)
      }
      #else
      throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
      #endif
    }

    Function("validateAddress") { (address: String) -> Bool in
      #if canImport(acp_mobile_ffiFFI)
      return acpValidateAddressFfi(address: address)
      #else
      return false
      #endif
    }

    AsyncFunction("addressFromKeystore") { (keystoreJson: String) -> String in
      try requireAcpNativeLinked()
      #if canImport(acp_mobile_ffiFFI)
      do {
        return try acpAddressFromKeystoreFfi(keystoreJson: keystoreJson)
      } catch let error as AcpWalletException {
        throw mapWalletError(error)
      }
      #else
      throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
      #endif
    }

    AsyncFunction("estimateFeeDefault") { () -> [String: Any] in
      try requireAcpNativeLinked()
      #if canImport(acp_mobile_ffiFFI)
      do {
        let fee = try acpEstimateFeeDefaultFfi()
        return [
          "feeAcp": fee.feeAcp,
          "feeUnits": NSNumber(value: fee.feeUnits),
        ]
      } catch let error as AcpWalletException {
        throw mapWalletError(error)
      }
      #else
      throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
      #endif
    }

    AsyncFunction("signTransfer") { (rpcUrl: String, keystoreJson: String, toAddress: String, amountAcp: String, feeAcp: String?) -> [String: Any] in
      try requireAcpNativeLinked()
      #if canImport(acp_mobile_ffiFFI)
      do {
        let signed = try acpSignTransferFfi(
          rpcUrl: rpcUrl,
          keystoreJson: keystoreJson,
          toAddress: toAddress,
          amountAcp: amountAcp,
          feeAcp: feeAcp
        )
        return [
          "rawTx": signed.rawTx,
          "txid": signed.txid,
        ]
      } catch let error as AcpWalletException {
        throw mapWalletError(error)
      }
      #else
      throw Exceptions.NotImplemented(acpNativeAvailabilityMessage())
      #endif
    }
  }
}
