# UniFFI 0.28 emits a field named message and an Exception.message override for
# the same error variant. Rename only its Kotlin payload field; wire bytes and
# Rust/Swift API names are unchanged. Apply after every Kotlin regeneration.
param([Parameter(Mandatory = $true)][string]$SourcePath)
$ErrorActionPreference = "Stop"
$source = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $SourcePath))
$field = 'val `message`: kotlin.String'
if ($source.Contains($field)) {
  if (($source.Split(@($field), [StringSplitOptions]::None).Length - 1) -ne 2) {
    throw "Unexpected UniFFI error layout; review Kotlin payload rename manually."
  }
  $source = $source.Replace($field, 'val `details`: kotlin.String')
  $source = $source.Replace('${ `message` }', '${ `details` }')
  $source = $source.Replace('value.`message`', 'value.`details`')
}
if ($source.Contains($field) -or $source.Contains('value.`message`') -or $source.Contains('${ `message` }')) {
  throw "Conflicting UniFFI Kotlin message payload remains."
}
if (-not $source.Contains('val `details`: kotlin.String')) { throw "Expected wallet error payload not found." }
$normalized = (($source -split '\r?\n' | ForEach-Object { $_.TrimEnd() }) -join "`n").TrimEnd() + "`n"
[IO.File]::WriteAllText((Resolve-Path -LiteralPath $SourcePath), $normalized, [Text.UTF8Encoding]::new($false))
