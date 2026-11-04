# Research Operations Onboarding Template

> Status: reusable template | Added: 2026-11-04 (ROP-05)
> Purpose: copy-only settings, source categories and packet templates for new client onboarding
> Constraints: never include previous client documents, credentials, identifiers or personal data

## Reusable Settings (copy to each new project)

### Project configuration defaults
```json
{
  "project_name_pattern": "{client_name} Research",
  "retention_days_default": 30,
  "max_sources_per_project": 10,
  "max_snapshots_per_source": 20,
  "max_claims_per_source": 50,
  "check_cooldown_seconds": 60,
  "enabled_by_default": true
}
```

### Source categories (copy to each new project)
- Technology companies: `https://example-tech.com/`, `https://tech-news.example.org/`
- Crypto agencies: `https://crypto-agency.example.com/`, `https://blockchain-daily.example.net/`
- General tech news: `https://tech-weekly.example.org/`, `https://industry-insights.example.com/`

### Packet template structure (copy to each new project)
```json
{
  "format": "ancap-research-client-packet/v1",
  "research": {
    "project_id": "<uuid>",
    "project_name": "<client_project_name>",
    "sources": [
      {
        "id": "<source_uuid>",
        "title": "<source_title>",
        "url": "<source_url>",
        "status": "baseline",
        "latest_hash": "<sha256>",
        "checked_at": "<ISO timestamp>",
        "expires_at": "<ISO timestamp>"
      }
    ],
    "claims": []
  },
  "result": {
    "items": [
      {
        "summary": "<report_summary>",
        "details": "<optional details>",
        "hash": "<sha256 of report>"
      }
    ]
  }
}
```

## Onboarding Checklist (manual review required)

- [ ] Copy reusable settings to new project configuration
- [ ] Select appropriate source categories for client vertical
- [ ] Create initial source list (max 10 sources per project)
- [ ] Set retention period based on client agreement
- [ ] Configure delivery channel and revision round count
- [ ] Review packet template structure with client
- [ ] Document any custom constraints or exclusions

## Client-specific customization notes

> Fill in client-specific details here. Never copy previous client data.

- Client name:
- Vertical/industry:
- Preferred delivery method:
- Revision policy:
- Special compliance requirements:

## Next steps after onboarding

1. Run initial source collection (bounded by project quotas)
2. Create first research packet draft
3. Schedule regular check intervals per ROP-03
4. Set up webhook for outbox notifications (optional)
5. Document client-specific constraints in project notes
