# UniFFI resolves Rust exports by Java method name through JNA Native.load.
# JNA Structure.FieldOrder also refers to the original field names.
-keepattributes *Annotation*
-keep class uniffi.acp_mobile_ffi.** { *; }
-keep interface uniffi.acp_mobile_ffi.** { *; }
-keep class com.sun.jna.** { *; }
-keep interface com.sun.jna.** { *; }
