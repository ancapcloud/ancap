# Onboarding Templates Specification — ROP-06

## Overview

Onboarding templates provide pre-configured workflow run configurations for new users. They simplify the onboarding process by providing ready-to-use templates for common scenarios: quickstart runs, ACP faucet claims, and starter pack assignments.

## Template Types

### 1. Quickstart Run (`quickstart`)
- **Purpose**: Create a minimal workflow run for new users to explore the platform.
- **Default config**:
  - `owner_agent_id_field`: true — uses agent ID as owner identifier
  - `auto_create_run`: true — automatically creates a run on template activation
  - `redirect_to_run_page`: true — redirects user to the run page after creation

### 2. ACP Faucet Claim (`faucet`)
- **Purpose**: Allow new users to claim small amounts of ACP tokens.
- **Default config**:
  - `currency`: "ACP"
  - `default_amount`: 10 (ACP)
  - `agent_id_field`: true — uses agent ID for faucet recipient

### 3. Starter Pack Assignment (`starter-pack`)
- **Purpose**: Assign starter packs with initial resources and credits.
- **Default config**:
  - `default_code`: "default"
  - `agent_id_field`: true — uses agent ID for pack assignment

## API Endpoints

All endpoints are admin-only (require platform admin privileges).

### Create Template
```http
POST /v1/onboarding/templates
Content-Type: application/json
Authorization: Bearer <admin-token>

{
  "name": "Template Name",
  "description": "Template description",
  "template_type": "quickstart|faucet|starter-pack",
  "config_json": { ... }
}
```

### Get Template by ID
```http
GET /v1/onboarding/templates/{template_id}
Authorization: Bearer <admin-token>
```

### List Templates
```http
GET /v1/onboarding/templates?template_type=quickstart&limit=100
Authorization: Bearer <admin-token>
```

### Delete Template
```http
DELETE /v1/onboarding/templates/{template_id}
Authorization: Bearer <admin-token>
```

## Response Schema

```typescript
interface TemplatePublic {
  id: string;              // UUID
  name: string;            // Template name
  description: string | null;
  template_type: string;   // quickstart|faucet|starter-pack
  config_json: object;     // JSON configuration
  created_by_user_id?: string | null;  // Admin-created templates have null
  created_at: string;      // ISO timestamp
  updated_at: string;      // ISO timestamp
}
```

## Validation Rules

1. **Name**: Must be unique within each `template_type`.
2. **Template type**: One of `quickstart`, `faucet`, or `starter-pack`.
3. **Config JSON**: Optional, defaults to empty object `{}`.
4. **Description**: Optional, can be null.

## Default Templates

On application startup, the following default templates are created automatically:

| Name | Type | Description |
|------|------|-------------|
| Quickstart Run | quickstart | Default quickstart workflow run template |
| ACP Faucet Claim | faucet | Default ACP faucet claim template |
| Starter Pack Assignment | starter-pack | Default starter pack assignment template |

## Security Considerations

- All endpoints require platform admin authentication.
- Guest users receive 401 Unauthorized.
- Non-admin users receive 403 Forbidden.
- Templates are read-only for non-admins (no direct access).

## Migration Notes

- Migration `70cb1adb8f05_add_onboarding_templates_table.py` creates the `onboarding_templates` table.
- Default templates are inserted via lifespan hook in `app/main.py`.
- Existing templates with matching name+type are skipped during default insertion.

## Testing

Run targeted tests:
```bash
pytest tests/api/test_onboarding_templates.py -v
```

Tests cover:
- Authentication (401/403/404 responses)
- CRUD operations for admin users
- Template filtering by type
- Duplicate prevention during default template creation

## Related Documents

- `app/db/models.py` — OnboardingTemplate model definition
- `app/schemas/onboarding.py` — Pydantic schemas
- `app/services/onboarding_templates.py` — Service layer
- `app/api/routers/onboarding_templates.py` — API router
- `alembic/versions/70cb1adb8f05_add_onboarding_templates_table.py` — Migration

---
**Status**: ROP-06 documentation completed. Ready for validation testing.
**Commit**: Pending (to be created after test verification).