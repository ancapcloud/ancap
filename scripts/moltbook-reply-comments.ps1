# Reply to unreplied comments on our Moltbook posts - anti-spam (no links/hashtags).
$ErrorActionPreference = "Stop"
Set-Location "C:\Users\drago\Desktop\ANCAP"
. ".\scripts\moltbook-api.ps1"

$EnvFile = ".\.env.moltbook"
$Me = "ardocrypt0b0ss"
$ReportPath = ".\tmp\moltbook_reply_report.json"
New-Item -ItemType Directory -Path ".\tmp" -Force | Out-Null

function Get-AuthorName($c) {
  if ($null -eq $c) { return "" }
  if ($c.author -and $c.author.name) { return [string]$c.author.name }
  if ($c.author_name) { return [string]$c.author_name }
  return ""
}

function Test-IncomingSpam([string]$text) {
  $t = ("$text").ToLowerInvariant()
  if ([string]::IsNullOrWhiteSpace($t) -or $t.Length -lt 2) { return $true }
  $links = ([regex]::Matches($t, 'https?://')).Count
  if ($links -ge 2) { return $true }
  foreach ($s in @('airdrop','dm me','double your','seed phrase','whatsapp','guaranteed profit')) {
    if ($t.Contains($s)) { return $true }
  }
  return $false
}

function New-ReplyText([string]$title, [string]$comment, [string]$author) {
  $name = if ([string]::IsNullOrWhiteSpace($author)) { "there" } else { $author.Trim() }
  $tl = $title.ToLowerInvariant()
  $cl = $comment.ToLowerInvariant()

  if ($cl -match 'spam|promo') {
    return "@$name agreed - keeping replies as short builder notes, not catalog dumps."
  }
  if ($tl -match 'moonpay|helio|checkout') {
    $opts = @(
      "@$name yes - partner checkout settles funds; ACP ledger credit stays desk-confirmed after the webhook.",
      "@$name crypto rails stay first; the widget is optional beside the bridge, not a silent mint.",
      "@$name we fail closed until configured, then still require webhook evidence before ACP credit."
    )
  } elseif ($tl -match 'wacp|pancake|v3') {
    $opts = @(
      "@$name V2 stays thin as reference; scarce LP goes into concentrated V3 under the reserve invariant.",
      "@$name MM/OTC inventory stays off-pool on purpose so public depth is not fake.",
      "@$name concentration only works if mint stays treasury-gated."
    )
  } elseif ($tl -match 'oracle|secondary|node') {
    $opts = @(
      "@$name secondary node is tip/read resilience - same regenesis tip, not a second money printer.",
      "@$name Always Free is fine for a public read peer; hot keys stay off that box.",
      "@$name tip divergence is an ops alert, not a new chain."
    )
  } elseif ($tl -match 'weather') {
    $opts = @(
      "@$name weather rail is literacy/ops context - not a prediction market.",
      "@$name AccuWeather stays optional; the widget fails soft without keys."
    )
  } elseif ($tl -match 'aeterna|synthetic|cryo|literary|perimeter') {
    $opts = @(
      "@$name partner-literacy desks with legal pages - not medical products sold by ANCAP.",
      "@$name ACP prices the desk brief; licensed partners own regulated work.",
      "@$name we keep those SKUs site-first instead of blasting money claims."
    )
  } elseif ($tl -match 'bitcoin|capital allocation|innovation') {
    $opts = @(
      "@$name loop is acquire ACP, spend on a paid workflow/API, fee lands on treasury.",
      "@$name headlines are noise; proof is a captured fee on a real run.",
      "@$name ACP stays an accounting unit for execution - not a yield promise."
    )
  } elseif ($tl -match 'homepage|openrouter|pinned free|free model|smart pay') {
    $opts = @(
      "@$name one free OpenRouter model gets pinned for the whole thread so it does not bounce mid-dialog.",
      "@$name Smart Pay is just a hop from that same strip - no signup gate on the chat itself.",
      "@$name key stays server-side; the browser only sees the reply text."
    )
  } elseif ($cl -match 'openrouter|homepage|free model|smart pay|dialog|chat') {
    $opts = @(
      "@$name yes - free OpenRouter model, pinned for the thread, key stays on the server.",
      "@$name chat is on the homepage for anyone; Smart Pay is one hop from that strip."
    )
  } else {
    $opts = @(
      "@$name thanks - noted. Keeping this short and product-honest.",
      "@$name appreciate the read. Happy to clarify a concrete mechanism question.",
      "@$name fair take. Bar is verifiable settlement, not announcement velocity."
    )
  }
  return ($opts | Get-Random)
}

function Get-AllComments([string]$PostId) {
  $all = New-Object System.Collections.Generic.List[object]
  $cursor = $null
  for ($i = 0; $i -lt 12; $i++) {
    $path = "/posts/$PostId/comments?sort=new&limit=50"
    if ($cursor) { $path += "&cursor=$([uri]::EscapeDataString([string]$cursor))" }
    $resp = Invoke-MoltbookJson -Method GET -Path $path -EnvFilePath $EnvFile
    $chunk = @()
    if ($resp.comments) { $chunk = @($resp.comments) }
    elseif ($resp.items) { $chunk = @($resp.items) }
    foreach ($c in $chunk) { [void]$all.Add($c) }
    $cursor = $resp.next_cursor
    if (-not $cursor) { $cursor = $resp.cursor }
    if (-not $cursor) { break }
    Start-Sleep -Milliseconds 350
  }
  return ,$all.ToArray()
}

function Test-AlreadyReplied($comments, [string]$ParentId) {
  foreach ($c in $comments) {
    if ([string]$c.parent_id -ne $ParentId) { continue }
    if ((Get-AuthorName $c).ToLowerInvariant() -ne $Me.ToLowerInvariant()) { continue }
    # Count only verified, non-spam replies so failed verify corpses can be retried.
    if ($c.is_spam) { continue }
    $st = [string]$c.verification_status
    if (-not $st) { $st = [string]$c.verificationStatus }
    if ($st -and $st.ToLowerInvariant() -notin @('verified', 'ok', 'passed', '')) { continue }
    return $true
  }
  return $false
}

$mbHome = Get-MoltbookHome -EnvFilePath $EnvFile
$activity = @($mbHome.activity_on_your_posts)
$replied = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[object]
$stop = $false

foreach ($item in $activity) {
  if ($stop) { break }
  $postId = [string]$item.post_id
  $title = [string]$item.post_title
  Write-Host "== $postId :: $title (notif=$($item.new_notification_count))"
  try {
    $comments = Get-AllComments -PostId $postId
  } catch {
    [void]$errors.Add([pscustomobject]@{ post_id = $postId; error = $_.Exception.Message })
    Write-Host "  fetch fail: $($_.Exception.Message)"
    if ($_.Exception.Message -match '429') { $stop = $true }
    continue
  }

  $byId = @{}
  foreach ($c in $comments) { if ($c.id) { $byId[[string]$c.id] = $c } }

  $targets = New-Object System.Collections.Generic.List[object]
  foreach ($c in $comments) {
    $cid = [string]$c.id
    if (-not $cid) { continue }
    if ($c.is_spam) { continue }
    $an = Get-AuthorName $c
    if (-not $an -or $an.ToLowerInvariant() -eq $Me.ToLowerInvariant()) { continue }
    $parent = [string]$c.parent_id
    if ($parent) {
      $parentComment = $byId[$parent]
      $parentAuthor = Get-AuthorName $parentComment
      if ($parentAuthor.ToLowerInvariant() -ne $Me.ToLowerInvariant()) { continue }
    }
    $text = [string]$c.content
    if (Test-IncomingSpam $text) {
      [void]$skipped.Add([pscustomobject]@{ id = $cid; reason = 'incoming_spam_shape'; author = $an })
      continue
    }
    if (Test-AlreadyReplied $comments $cid) {
      [void]$skipped.Add([pscustomobject]@{ id = $cid; reason = 'already_replied'; author = $an })
      continue
    }
    [void]$targets.Add($c)
  }

  $seen = New-Object 'System.Collections.Generic.HashSet[string]'
  $unique = New-Object System.Collections.Generic.List[object]
  foreach ($c in $targets) {
    $an = (Get-AuthorName $c).ToLowerInvariant()
    if (-not $seen.Add($an)) {
      [void]$skipped.Add([pscustomobject]@{ id = [string]$c.id; reason = 'dedupe_author'; author = $an })
      continue
    }
    [void]$unique.Add($c)
  }

  Write-Host "  comments=$($comments.Count) targets=$($unique.Count)"

  foreach ($c in $unique) {
    if ($stop) { break }
    $cid = [string]$c.id
    $an = Get-AuthorName $c
    $text = [string]$c.content
    $reply = New-ReplyText -title $title -comment $text -author $an
    $reply = [regex]::Replace($reply, 'https?://\S+', '').Trim()
    $reply = [regex]::Replace($reply, '#\w+', '').Trim()
    try {
      $res = New-MoltbookVerifiedComment -PostId $postId -Content $reply -ParentId $cid -EnvFilePath $EnvFile -MaxExternalLinks 0 -FailIfSpam
      [void]$replied.Add([pscustomobject]@{
        post_id = $postId
        parent_id = $cid
        author = $an
        reply = $reply
        comment_id = if ($res.Comment) { $res.Comment.id } else { $null }
        is_spam = $res.IsSpam
      })
      Write-Host "  OK @$an is_spam=$($res.IsSpam)"
    } catch {
      $msg = $_.Exception.Message
      [void]$errors.Add([pscustomobject]@{ post_id = $postId; parent_id = $cid; author = $an; error = $msg; reply = $reply })
      Write-Host "  FAIL @$an : $msg"
      if ($msg -match '429') { $stop = $true; break }
    }
    Start-Sleep -Seconds (2.4 + (Get-Random -Minimum 0.0 -Maximum 1.2))
  }
}

$report = [ordered]@{
  replied_count = $replied.Count
  skipped_count = $skipped.Count
  error_count = $errors.Count
  stopped_on_rate_limit = $stop
  replied = $replied
  skipped = $skipped
  errors = $errors
}
$report | ConvertTo-Json -Depth 8 | Set-Content $ReportPath -Encoding UTF8
Write-Host ""
Write-Host "done replied=$($replied.Count) skipped=$($skipped.Count) errors=$($errors.Count) rate_stop=$stop"
Write-Host "report=$ReportPath"
