package expo.modules.acpcore

import expo.modules.kotlin.exception.CodedException
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import uniffi.acp_mobile_ffi.AcpWalletException
import uniffi.acp_mobile_ffi.acpAddressFromKeystoreFfi
import uniffi.acp_mobile_ffi.acpCreateWalletFfi
import uniffi.acp_mobile_ffi.acpEncryptKeystoreFfi
import uniffi.acp_mobile_ffi.acpDecryptKeystoreFfi
import uniffi.acp_mobile_ffi.acpEstimateFeeDefaultFfi
import uniffi.acp_mobile_ffi.acpSignTransferFfi
import uniffi.acp_mobile_ffi.acpValidateAddressFfi

private fun mapWalletError(e: AcpWalletException): CodedException {
  val code = when (e) {
    is AcpWalletException.InvalidAddress -> "ERR_INVALID_ADDRESS"
    is AcpWalletException.InvalidMnemonic -> "ERR_INVALID_MNEMONIC"
    is AcpWalletException.InvalidAmount -> "ERR_INVALID_AMOUNT"
    is AcpWalletException.InsufficientFunds -> "ERR_INSUFFICIENT_FUNDS"
    is AcpWalletException.Rpc -> "ERR_RPC"
    is AcpWalletException.Internal -> "ERR_INTERNAL"
  }
  return CodedException(code, e.message ?: "ACP wallet error", e)
}

class ExpoAcpCoreModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("ExpoAcpCore")

    AsyncFunction("encryptKeystore") { keystoreJson: String, password: String ->
      try { acpEncryptKeystoreFfi(keystoreJson, password) }
      catch (e: AcpWalletException) { throw mapWalletError(e) }
    }

    AsyncFunction("decryptKeystore") { backupJson: String, password: String ->
      try { acpDecryptKeystoreFfi(backupJson, password) }
      catch (e: AcpWalletException) { throw mapWalletError(e) }
    }

    AsyncFunction("createWallet") {
      try {
        val w = acpCreateWalletFfi()
        mapOf(
          "address" to w.`address`,
          "mnemonic" to w.`mnemonic`,
          "keystoreJson" to w.`keystoreJson`,
        )
      } catch (e: AcpWalletException) {
        throw mapWalletError(e)
      }
    }

    Function("validateAddress") { address: String ->
      acpValidateAddressFfi(address)
    }

    AsyncFunction("addressFromKeystore") { keystoreJson: String ->
      try {
        acpAddressFromKeystoreFfi(keystoreJson)
      } catch (e: AcpWalletException) {
        throw mapWalletError(e)
      }
    }

    AsyncFunction("estimateFeeDefault") {
      try {
        val fee = acpEstimateFeeDefaultFfi()
        mapOf(
          "feeAcp" to fee.`feeAcp`,
          "feeUnits" to fee.`feeUnits`.toLong(),
        )
      } catch (e: AcpWalletException) {
        throw mapWalletError(e)
      }
    }

    AsyncFunction("signTransfer") { rpcUrl: String, keystoreJson: String, toAddress: String, amountAcp: String, feeAcp: String? ->
      try {
        val signed = acpSignTransferFfi(rpcUrl, keystoreJson, toAddress, amountAcp, feeAcp)
        mapOf(
          "rawTx" to signed.`rawTx`,
          "txid" to signed.`txid`,
        )
      } catch (e: AcpWalletException) {
        throw mapWalletError(e)
      }
    }
  }
}
