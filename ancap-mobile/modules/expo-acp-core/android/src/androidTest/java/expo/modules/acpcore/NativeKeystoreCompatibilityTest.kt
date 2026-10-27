package expo.modules.acpcore

import android.os.Bundle
import android.system.Os
import android.system.OsConstants
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.sun.jna.Native
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import uniffi.acp_mobile_ffi.AcpWalletException
import uniffi.acp_mobile_ffi.acpAddressFromKeystoreFfi
import uniffi.acp_mobile_ffi.acpCreateWalletFfi
import uniffi.acp_mobile_ffi.acpDecryptKeystoreFfi
import uniffi.acp_mobile_ffi.acpEncryptKeystoreFfi
import uniffi.acp_mobile_ffi.acpValidateAddressFfi

/** Exercises the packaged JNA/Rust boundary; never reads an app vault or uses RPC. */
@RunWith(AndroidJUnit4::class)
class NativeKeystoreCompatibilityTest {
  @Test
  fun localEncryptedBackupRoundTrip() {
    val instrumentation = InstrumentationRegistry.getInstrumentation()
    instrumentation.sendStatus(0, Bundle().apply {
      putLong("pageSize", Os.sysconf(OsConstants._SC_PAGESIZE))
      putString("jnaVersion", Native.VERSION)
    })
    val wallet = acpCreateWalletFfi()
    assertTrue("Generated address must validate", acpValidateAddressFfi(wallet.address))
    val password = "disposable-instrumentation-test-only"
    val backup = acpEncryptKeystoreFfi(wallet.keystoreJson, password)
    assertFalse("Backup must not contain a plaintext recovery phrase", backup.contains(wallet.mnemonic))
    val restored = acpDecryptKeystoreFfi(backup, password)
    assertEquals(wallet.address, acpAddressFromKeystoreFfi(restored))
    var wrongPasswordRejected = false
    try {
      acpDecryptKeystoreFfi(backup, "incorrect-test-password")
    } catch (_: AcpWalletException) {
      wrongPasswordRejected = true
    }
    assertTrue("Wrong backup passwords must fail closed", wrongPasswordRejected)
    // Keys and phrase remain in this disposable process; no logging, persistence or funding.
  }
}
