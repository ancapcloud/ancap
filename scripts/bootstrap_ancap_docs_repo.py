from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_DIR = REPO_ROOT / ".github" / "bootstrap"
LABELS_PATH = BOOTSTRAP_DIR / "ancap-docs-labels.json"
MILESTONES_PATH = BOOTSTRAP_DIR / "ancap-docs-milestones.json"
DISCUSSIONS_PATH = BOOTSTRAP_DIR / "ancap-docs-discussions.json"
PROJECT_BOARD_PATH = BOOTSTRAP_DIR / "ancap-docs-project-board.json"
INITIAL_ISSUES_PATH = BOOTSTRAP_DIR / "ancap-docs-initial-issues.json"
REPO_SETTINGS_PATH = BOOTSTRAP_DIR / "ancap-docs-repo-settings.json"
UPDATE_CADENCE_PATH = BOOTSTRAP_DIR / "ancap-docs-update-cadence.json"
CI_PATH = BOOTSTRAP_DIR / "ancap-docs-ci.json"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_keys(mapping: dict[str, Any], keys: set[str], *, label: str) -> None:
    missing = sorted(key for key in keys if key not in mapping)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{label} is missing required keys: {joined}")


def validate_repo_argument(repo: str) -> str:
    normalized = repo.strip()
    if normalized.count("/") != 1:
        raise ValueError("--repo requires OWNER/REPO format")
    owner, name = normalized.split("/", 1)
    if not owner or not name:
        raise ValueError("--repo requires OWNER/REPO format")
    return normalized


def load_bootstrap_plan() -> dict[str, Any]:
    labels = _read_json(LABELS_PATH)
    milestones = _read_json(MILESTONES_PATH)
    discussions = _read_json(DISCUSSIONS_PATH)
    project_board = _read_json(PROJECT_BOARD_PATH)
    initial_issues = _read_json(INITIAL_ISSUES_PATH)
    repo_settings = _read_json(REPO_SETTINGS_PATH)
    update_cadence = _read_json(UPDATE_CADENCE_PATH)
    ci_seed = _read_json(CI_PATH)

    if not isinstance(labels, list) or not labels:
        raise ValueError("labels seed must be a non-empty list")
    for index, label in enumerate(labels, start=1):
        if not isinstance(label, dict):
            raise ValueError(f"labels[{index}] must be an object")
        _require_keys(label, {"name", "color", "description"}, label=f"labels[{index}]")

    if not isinstance(milestones, list) or not milestones:
        raise ValueError("milestones seed must be a non-empty list")
    for index, milestone in enumerate(milestones, start=1):
        if not isinstance(milestone, dict):
            raise ValueError(f"milestones[{index}] must be an object")
        _require_keys(milestone, {"title", "description"}, label=f"milestones[{index}]")

    if not isinstance(discussions, dict):
        raise ValueError("discussions seed must be an object")
    _require_keys(discussions, {"categories", "moderationNotes", "pinnedTopics"}, label="discussions seed")
    discussion_categories = discussions["categories"]
    if not isinstance(discussion_categories, list) or not discussion_categories:
        raise ValueError("discussions seed categories must be a non-empty list")
    for index, category in enumerate(discussion_categories, start=1):
        if not isinstance(category, dict):
            raise ValueError(f"discussions.categories[{index}] must be an object")
        _require_keys(category, {"name", "emoji", "description"}, label=f"discussions.categories[{index}]")

    discussion_pinned_topics = discussions["pinnedTopics"]
    if not isinstance(discussion_pinned_topics, list) or not discussion_pinned_topics:
        raise ValueError("discussions seed pinnedTopics must be a non-empty list")
    for index, topic in enumerate(discussion_pinned_topics, start=1):
        if not isinstance(topic, dict):
            raise ValueError(f"discussions.pinnedTopics[{index}] must be an object")
        _require_keys(topic, {"title", "categoryName", "purpose", "starterBody"}, label=f"discussions.pinnedTopics[{index}]")
        category_name = topic.get("categoryName")
        if not isinstance(category_name, str) or not category_name:
            raise ValueError(f"discussions.pinnedTopics[{index}].categoryName must be a non-empty string")

    if not isinstance(project_board, dict):
        raise ValueError("project board seed must be an object")
    _require_keys(project_board, {"name", "scope", "fields", "views", "notes"}, label="project board seed")

    if not isinstance(initial_issues, list) or not initial_issues:
        raise ValueError("initial issues seed must be a non-empty list")
    for index, issue in enumerate(initial_issues, start=1):
        if not isinstance(issue, dict):
            raise ValueError(f"initial_issues[{index}] must be an object")
        _require_keys(issue, {"title", "bodySummary", "milestone", "labels", "boardFields"}, label=f"initial_issues[{index}]")
        if not isinstance(issue["labels"], list) or not issue["labels"] or not all(
            isinstance(label, str) and label for label in issue["labels"]
        ):
            raise ValueError(f"initial_issues[{index}].labels must be a non-empty list of non-empty strings")
        if not isinstance(issue["boardFields"], dict) or not issue["boardFields"]:
            raise ValueError(f"initial_issues[{index}].boardFields must be a non-empty object")
        expected_state = issue.get("expectedState")
        if expected_state is not None and expected_state not in {"OPEN", "CLOSED"}:
            raise ValueError(f"initial_issues[{index}].expectedState must be OPEN or CLOSED when provided")
        status_note = issue.get("statusNote")
        if status_note is not None and (not isinstance(status_note, str) or not status_note.strip()):
            raise ValueError(f"initial_issues[{index}].statusNote must be a non-empty string when provided")

    if not isinstance(repo_settings, dict):
        raise ValueError("repo settings seed must be an object")
    _require_keys(
        repo_settings,
        {
            "visibility",
            "description",
            "homepage",
            "defaultBranch",
            "features",
            "mergePolicy",
            "branchProtection",
            "security",
            "notes",
        },
        label="repo settings seed",
    )
    visibility = repo_settings["visibility"]
    if visibility not in {"public", "private", "internal"}:
        raise ValueError("repo settings seed visibility must be one of: public, private, internal")

    if not isinstance(update_cadence, dict):
        raise ValueError("update cadence seed must be an object")
    _require_keys(update_cadence, {"cadences", "postTemplate", "rules"}, label="update cadence seed")

    if not isinstance(ci_seed, dict):
        raise ValueError("CI seed must be an object")
    _require_keys(ci_seed, {"workflowName", "workflowSourcePath", "targetWorkflowPath", "jobs", "checks", "notes"}, label="CI seed")
    jobs = ci_seed["jobs"]
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("CI seed jobs must be a non-empty list")
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise ValueError(f"CI seed jobs[{index}] must be an object")
        _require_keys(job, {"id", "name", "expectedStatusCheckContext"}, label=f"CI seed jobs[{index}]")

    default_status_check_contexts = repo_settings["branchProtection"].get("defaultStatusCheckContexts", [])
    if default_status_check_contexts:
        if not isinstance(default_status_check_contexts, list) or not all(
            isinstance(context, str) and context for context in default_status_check_contexts
        ):
            raise ValueError("repo settings seed defaultStatusCheckContexts must be a list of non-empty strings")
        ci_status_check_contexts = [job["expectedStatusCheckContext"] for job in jobs]
        if _dedupe_status_check_contexts(default_status_check_contexts) != _dedupe_status_check_contexts(ci_status_check_contexts):
            raise ValueError(
                "repo settings seed defaultStatusCheckContexts must stay aligned with CI seed expectedStatusCheckContext values"
            )

    return {
        "labels": labels,
        "milestones": milestones,
        "discussions": discussions,
        "project_board": project_board,
        "initial_issues": initial_issues,
        "repo_settings": repo_settings,
        "update_cadence": update_cadence,
        "ci": ci_seed,
    }


def build_discussion_automation_boundary() -> dict[str, Any]:
    return {
        "confirmedBy": "GitHub GraphQL schema introspection via gh api graphql",
        "supportedMutations": [
            {
                "name": "createDiscussion",
                "inputType": "CreateDiscussionInput",
                "requiredFields": ["repositoryId", "title", "body", "categoryId"],
                "optionalFields": ["clientMutationId"],
                "supports": ["create missing seeded discussion topics"],
            },
            {
                "name": "updateDiscussion",
                "inputType": "UpdateDiscussionInput",
                "requiredFields": ["discussionId"],
                "optionalFields": ["title", "body", "categoryId", "clientMutationId"],
                "supports": [
                    "retitle seeded discussion topics",
                    "re-edit seeded discussion bodies",
                    "move seeded discussion topics between categories",
                ],
            },
        ],
        "manualOnlyFlows": [
            "Discussion category create/remove/description alignment",
            "Discussion pin/unpin controls",
        ],
        "splitActions": [
            {
                "kind": "createAndPinDiscussionTopic",
                "automatablePortion": "Create the missing discussion topic via createDiscussion.",
                "manualPortion": "Pin the topic in the GitHub UI after creation.",
            }
        ],
    }


def build_discussion_graphql_mutation_command(
    *,
    mutation: str,
    repository_id: str | None = None,
    discussion_id: str | None = None,
    category_id: str | None = None,
    title: str | None = None,
    body: str | None = None,
) -> str | None:
    if mutation == "createDiscussion":
        if not repository_id or not category_id or not title or body is None:
            return None
        input_fields = [
            f"repositoryId:{json.dumps(repository_id, ensure_ascii=False)}",
            f"categoryId:{json.dumps(category_id, ensure_ascii=False)}",
            f"title:{json.dumps(title, ensure_ascii=False)}",
            f"body:{json.dumps(body, ensure_ascii=False)}",
        ]
        query = "mutation{createDiscussion(input:{" + ",".join(input_fields) + "}){discussion{id url title}}}"
    elif mutation == "updateDiscussion":
        if not discussion_id:
            return None
        input_fields = [f"discussionId:{json.dumps(discussion_id, ensure_ascii=False)}"]
        if title is not None:
            input_fields.append(f"title:{json.dumps(title, ensure_ascii=False)}")
        if body is not None:
            input_fields.append(f"body:{json.dumps(body, ensure_ascii=False)}")
        if category_id is not None:
            input_fields.append(f"categoryId:{json.dumps(category_id, ensure_ascii=False)}")
        if len(input_fields) == 1:
            return None
        query = "mutation{updateDiscussion(input:{" + ",".join(input_fields) + "}){discussion{id url title}}}"
    else:
        return None

    return format_command(["gh", "api", "graphql", "--raw-field", f"query={query}"])


def build_discussion_admin_action_automation_summary(
    actions: list[dict[str, Any]],
    *,
    categories: dict[str, dict[str, Any]] | None,
    discussion_topics_by_title: dict[str, dict[str, Any]] | None,
    repository_id: str | None = None,
) -> list[dict[str, Any]]:
    live_categories = categories if isinstance(categories, dict) else {}
    live_topics = discussion_topics_by_title if isinstance(discussion_topics_by_title, dict) else {}
    summary: list[dict[str, Any]] = []

    for item in actions:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        target = item.get("categoryName") if isinstance(item.get("categoryName"), str) else item.get("title")
        if not isinstance(target, str) or not target:
            target = kind if isinstance(kind, str) and kind else "discussion-action"
        entry: dict[str, Any] = {
            "kind": kind,
            "target": target,
        }

        if kind == "createMissingCategory":
            entry.update(
                {
                    "status": "manual_only",
                    "mutation": None,
                    "reason": "GitHub's public gh/API surface does not expose Discussion category creation or description mutations.",
                }
            )
        elif kind == "removeUnexpectedCategory":
            entry.update(
                {
                    "status": "manual_only",
                    "mutation": None,
                    "reason": "GitHub's public gh/API surface does not expose Discussion category removal admin mutations.",
                }
            )
        elif kind == "updateCategoryDescription":
            entry.update(
                {
                    "status": "manual_only",
                    "mutation": None,
                    "reason": "GitHub's public gh/API surface does not expose Discussion category description mutations.",
                }
            )
        elif kind == "createAndPinDiscussionTopic":
            expected_category_name = (
                item.get("expectedCategoryName") if isinstance(item.get("expectedCategoryName"), str) else None
            )
            live_category = live_categories.get(expected_category_name) if expected_category_name else None
            category_id = (
                live_category.get("id")
                if isinstance(live_category, dict) and isinstance(live_category.get("id"), str) and live_category.get("id")
                else None
            )
            title = item.get("title") if isinstance(item.get("title"), str) else None
            body = item.get("body") if isinstance(item.get("body"), str) else None
            blockers: list[str] = []
            if repository_id is None:
                blockers.append("live GitHub repository id")
            if expected_category_name is None:
                blockers.append("expected seeded category name")
            if category_id is None:
                blockers.append("live GitHub discussion category id")
            if title is None:
                blockers.append("seeded discussion title")
            if body is None:
                blockers.append("seeded discussion body")
            entry.update(
                {
                    "status": "split_action" if not blockers else "blocked",
                    "mutation": "createDiscussion",
                    "reason": "createDiscussion can create the seeded discussion topic body in a live Discussions category, but pinning still requires the GitHub UI.",
                    "requirements": ["repositoryId", "title", "body", "categoryId"],
                    "blockers": blockers,
                    "manualRemainder": ["pin discussion topic in GitHub UI"],
                }
            )
            if expected_category_name is not None:
                entry["expectedCategoryName"] = expected_category_name
            if repository_id is not None:
                entry["repositoryId"] = repository_id
            if category_id is not None:
                entry["categoryId"] = category_id
            if title is not None:
                entry["title"] = title
            if body is not None:
                entry["body"] = body
            mutation_command = build_discussion_graphql_mutation_command(
                mutation="createDiscussion",
                repository_id=repository_id,
                category_id=category_id,
                title=title,
                body=body,
            )
            if mutation_command is not None:
                entry["command"] = mutation_command
        elif kind == "moveDiscussionTopicCategory":
            title = item.get("title") if isinstance(item.get("title"), str) else None
            live_topic = live_topics.get(title) if title else None
            discussion_id = (
                live_topic.get("id")
                if isinstance(live_topic, dict) and isinstance(live_topic.get("id"), str) and live_topic.get("id")
                else None
            )
            expected_category_name = (
                item.get("expectedCategoryName") if isinstance(item.get("expectedCategoryName"), str) else None
            )
            live_category = live_categories.get(expected_category_name) if expected_category_name else None
            category_id = (
                live_category.get("id")
                if isinstance(live_category, dict) and isinstance(live_category.get("id"), str) and live_category.get("id")
                else None
            )
            blockers = []
            if discussion_id is None:
                blockers.append("live GitHub discussion id")
            if category_id is None:
                blockers.append("live GitHub discussion category id")
            entry.update(
                {
                    "status": "automatable" if not blockers else "blocked",
                    "mutation": "updateDiscussion",
                    "reason": "updateDiscussion can move a seeded discussion topic between live Discussions categories when both ids are known.",
                    "requirements": ["discussionId", "categoryId"],
                    "blockers": blockers,
                }
            )
            if title is not None:
                entry["title"] = title
            if expected_category_name is not None:
                entry["expectedCategoryName"] = expected_category_name
            if discussion_id is not None:
                entry["discussionId"] = discussion_id
            if category_id is not None:
                entry["categoryId"] = category_id
            mutation_command = build_discussion_graphql_mutation_command(
                mutation="updateDiscussion",
                discussion_id=discussion_id,
                category_id=category_id,
            )
            if mutation_command is not None:
                entry["command"] = mutation_command
        elif kind == "updateDiscussionTopicBody":
            title = item.get("title") if isinstance(item.get("title"), str) else None
            live_topic = live_topics.get(title) if title else None
            discussion_id = (
                live_topic.get("id")
                if isinstance(live_topic, dict) and isinstance(live_topic.get("id"), str) and live_topic.get("id")
                else None
            )
            body = item.get("body") if isinstance(item.get("body"), str) else None
            blockers = []
            if discussion_id is None:
                blockers.append("live GitHub discussion id")
            if body is None:
                blockers.append("seeded discussion body")
            entry.update(
                {
                    "status": "automatable" if not blockers else "blocked",
                    "mutation": "updateDiscussion",
                    "reason": "updateDiscussion can re-edit a seeded discussion topic body when the live discussion id is known.",
                    "requirements": ["discussionId", "body"],
                    "blockers": blockers,
                }
            )
            if title is not None:
                entry["title"] = title
            if discussion_id is not None:
                entry["discussionId"] = discussion_id
            if body is not None:
                entry["body"] = body
            mutation_command = build_discussion_graphql_mutation_command(
                mutation="updateDiscussion",
                discussion_id=discussion_id,
                body=body,
            )
            if mutation_command is not None:
                entry["command"] = mutation_command
        elif kind == "pinDiscussionTopic":
            entry.update(
                {
                    "status": "manual_only",
                    "mutation": None,
                    "reason": "GitHub's public gh/API surface does not expose discussion pin/unpin admin mutations.",
                }
            )
        else:
            entry.update(
                {
                    "status": "unknown",
                    "mutation": None,
                    "reason": "No discussion automation mapping is recorded for this admin action yet.",
                }
            )

        summary.append(entry)

    return summary


def build_repo_edit_command(repo: str, repo_settings: dict[str, Any]) -> list[str]:
    features = repo_settings["features"]
    merge_policy = repo_settings["mergePolicy"]
    security = repo_settings["security"]

    return [
        "gh",
        "repo",
        "edit",
        repo,
        "--description",
        repo_settings["description"],
        "--homepage",
        repo_settings["homepage"],
        "--default-branch",
        repo_settings["defaultBranch"],
        f"--enable-issues={'true' if features['issues'] else 'false'}",
        f"--enable-discussions={'true' if features['discussions'] else 'false'}",
        f"--enable-projects={'true' if features['projects'] else 'false'}",
        f"--enable-wiki={'true' if features['wiki'] else 'false'}",
        f"--enable-merge-commit={'true' if merge_policy['mergeCommits'] else 'false'}",
        f"--enable-squash-merge={'true' if merge_policy['squashMerge'] else 'false'}",
        f"--enable-rebase-merge={'true' if merge_policy['rebaseMerge'] else 'false'}",
        f"--delete-branch-on-merge={'true' if merge_policy['autoDeleteHeadBranches'] else 'false'}",
        "--enable-secret-scanning" if security["secretScanning"] else "--enable-secret-scanning=false",
        "--enable-secret-scanning-push-protection"
        if security["pushProtection"]
        else "--enable-secret-scanning-push-protection=false",
    ]


def build_repo_edit_notes(repo_settings: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if repo_settings["features"].get("releases") is False:
        notes.append("GitHub releases cannot be disabled via gh repo edit; keep this repo release-capable.")
    return notes


def build_repo_create_command(repo: str, repo_settings: dict[str, Any]) -> list[str]:
    features = repo_settings["features"]
    visibility = repo_settings["visibility"]

    command = [
        "gh",
        "repo",
        "create",
        repo,
        f"--{visibility}",
        "--description",
        repo_settings["description"],
        "--homepage",
        repo_settings["homepage"],
    ]
    if features.get("issues") is False:
        command.append("--disable-issues")
    if features.get("wiki") is False:
        command.append("--disable-wiki")
    return command


def build_repo_create_notes(repo_settings: dict[str, Any]) -> list[str]:
    notes = [
        "Create the repo empty so the exported docs bundle can become the first push without merge noise.",
        "Follow the create step with gh repo edit / vulnerability alerts / labels / milestones from the same checked-in seeds.",
        "For the first public launch, the helper can run this create step with --apply --create-repo; do not combine that first-run creation step with branch-protection apply before the initial bundle push exists.",
    ]
    features = repo_settings["features"]
    if features.get("discussions"):
        notes.append("Enable GitHub Discussions immediately after creation so the seeded categories and pinned topics have a live home.")
    if features.get("projects"):
        notes.append("Enable GitHub Projects after creation before applying the project-board seed when the owner/account plan supports it.")
    return notes


def _slug_placeholder(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "value"



def build_project_board_issue_seed_commands(
    repo: str,
    project_board: dict[str, Any],
    initial_issues: list[dict[str, Any]],
    *,
    issue_urls_by_title: dict[str, str] | None = None,
) -> dict[str, Any]:
    owner, _ = repo.split("/", 1)
    project_number_placeholder = "<project-number>"
    project_id_placeholder = "<project-id>"
    item_id_placeholder = "<item-id>"
    lookup_commands = {
        "view": format_command(
            [
                "gh",
                "project",
                "view",
                project_number_placeholder,
                "--owner",
                owner,
                "--format",
                "json",
            ]
        ),
        "fieldList": format_command(
            [
                "gh",
                "project",
                "field-list",
                project_number_placeholder,
                "--owner",
                owner,
                "--format",
                "json",
            ]
        ),
    }
    field_kinds = {
        str(field.get("name")): field.get("kind")
        for field in project_board["fields"]
        if isinstance(field, dict) and isinstance(field.get("name"), str) and field.get("name")
    }
    items: list[dict[str, Any]] = []
    issue_urls_by_title = issue_urls_by_title or {}
    for issue in initial_issues:
        title = issue["title"]
        issue_url = issue_urls_by_title.get(title)
        issue_url_value = issue_url or "<issue-url>"
        add_command = format_command(
            [
                "gh",
                "project",
                "item-add",
                project_number_placeholder,
                "--owner",
                owner,
                "--url",
                issue_url_value,
                "--format",
                "json",
            ]
        )
        field_assignments: list[dict[str, Any]] = []
        for field_name, value in issue["boardFields"].items():
            kind = field_kinds.get(field_name)
            if kind == "single_select":
                field_slug = _slug_placeholder(str(field_name))
                value_slug = _slug_placeholder(str(value))
                field_assignments.append(
                    {
                        "field": field_name,
                        "kind": kind,
                        "value": value,
                        "command": format_command(
                            [
                                "gh",
                                "project",
                                "item-edit",
                                "--id",
                                item_id_placeholder,
                                "--project-id",
                                project_id_placeholder,
                                "--field-id",
                                f"<{field_slug}-field-id>",
                                "--single-select-option-id",
                                f"<{field_slug}-{value_slug}-option-id>",
                            ]
                        ),
                    }
                )
                continue

            if kind == "linked_seed":
                field_assignments.append(
                    {
                        "field": field_name,
                        "kind": kind,
                        "value": value,
                        "command": None,
                        "note": (
                            f"`{field_name}` should follow the seeded issue milestone `{issue['milestone']}` once the linked milestone "
                            "field exists on the project; no separate gh project item-edit command is emitted here."
                        ),
                    }
                )
                continue

            field_assignments.append(
                {
                    "field": field_name,
                    "kind": kind,
                    "value": value,
                    "command": None,
                    "note": (
                        f"Set `{field_name}` to `{value}` manually after the item exists because seed kind `{kind}` is not "
                        "currently emitted as a gh project item-edit command."
                    ),
                }
            )

        items.append(
            {
                "title": title,
                "milestone": issue["milestone"],
                "issueUrl": issue_url,
                "issueUrlPlaceholder": issue_url is None,
                "addCommand": add_command,
                "fieldAssignments": field_assignments,
            }
        )

    return {
        "projectIdPlaceholder": project_id_placeholder,
        "itemIdPlaceholder": item_id_placeholder,
        "lookupCommands": lookup_commands,
        "notes": [
            "Run the project item-add command with --format json and capture the returned item id before applying field values.",
            "Run the project view command with --format json to capture the stable project id needed by gh project item-edit.",
            "Run the field-list command with --format json to map field ids and single-select option ids before applying the item-edit commands.",
            "The seeded starter issues already carry milestone routing via gh issue create, so the linked milestone board dimension should follow the issue milestone automatically once the issue is added.",
            "Use the live issue URL when one is already known; otherwise replace <issue-url> after creating the seeded starter issue.",
        ],
        "items": items,
    }



def build_project_board_setup(
    repo: str,
    project_board: dict[str, Any],
    initial_issues: list[dict[str, Any]],
    *,
    issue_urls_by_title: dict[str, str] | None = None,
) -> dict[str, Any]:
    owner, _ = repo.split("/", 1)
    project_number_placeholder = "<project-number>"
    create_command = format_command(
        [
            "gh",
            "project",
            "create",
            "--owner",
            owner,
            "--title",
            project_board["name"],
            "--format",
            "json",
        ]
    )
    edit_description_command = format_command(
        [
            "gh",
            "project",
            "edit",
            project_number_placeholder,
            "--owner",
            owner,
            "--description",
            project_board["scope"],
        ]
    )
    link_repo_command = format_command(
        [
            "gh",
            "project",
            "link",
            project_number_placeholder,
            "--owner",
            owner,
            "--repo",
            repo,
        ]
    )

    field_commands: list[dict[str, Any]] = []
    manual_steps: list[str] = []
    data_type_map = {
        "single_select": "SINGLE_SELECT",
        "text": "TEXT",
        "date": "DATE",
        "number": "NUMBER",
    }
    for field in project_board["fields"]:
        name = field.get("name")
        kind = field.get("kind")
        if kind == "linked_seed":
            field_commands.append(
                {
                    "name": name,
                    "kind": kind,
                    "command": None,
                    "source": field.get("source"),
                }
            )
            manual_steps.append(
                f"Use repository issue milestones from {field.get('source')} as the board milestone dimension for `{name}`; gh project field-create does not create linked-seed milestone fields."
            )
            continue

        data_type = data_type_map.get(kind)
        if data_type is None:
            field_commands.append(
                {
                    "name": name,
                    "kind": kind,
                    "command": None,
                    "source": field.get("source"),
                }
            )
            manual_steps.append(
                f"Create or map project field `{name}` manually because seed kind `{kind}` is not currently emitted as a gh project field-create command."
            )
            continue

        command = [
            "gh",
            "project",
            "field-create",
            project_number_placeholder,
            "--owner",
            owner,
            "--name",
            str(name),
            "--data-type",
            data_type,
        ]
        options = field.get("options")
        if data_type == "SINGLE_SELECT" and isinstance(options, list) and options:
            command.extend(["--single-select-options", ",".join(str(option) for option in options)])
        field_commands.append(
            {
                "name": name,
                "kind": kind,
                "command": format_command(command),
                "source": field.get("source"),
            }
        )

    manual_steps.append(
        "Create the seeded project views in the GitHub UI after the fields exist; gh project CLI does not currently expose view creation."
    )

    starter_issue_boarding = build_project_board_issue_seed_commands(
        repo,
        project_board,
        initial_issues,
        issue_urls_by_title=issue_urls_by_title,
    )

    return {
        "ownerLogin": owner,
        "projectNumberPlaceholder": project_number_placeholder,
        "commands": {
            "create": create_command,
            "editDescription": edit_description_command,
            "linkRepo": link_repo_command,
        },
        "fieldCommands": field_commands,
        "notes": [
            "The create command uses --format json so the new project number/id can be captured for the follow-up gh project edit/link/field-create commands.",
            "Replace <project-number> in the follow-up commands with the project number returned by gh project create or gh project list/view once project-capable auth exists.",
            "These commands require project-capable auth; the live verification probe may still report missing read:project scope until that auth is refreshed.",
        ],
        "manualSteps": manual_steps,
        "starterIssueBoarding": starter_issue_boarding,
    }


def build_dependabot_alerts_command(repo: str) -> list[str]:
    return ["gh", "api", "--method", "PUT", f"repos/{repo}/vulnerability-alerts"]


def build_label_commands(repo: str, labels: list[dict[str, Any]]) -> list[list[str]]:
    commands: list[list[str]] = []
    for label in labels:
        commands.append(
            [
                "gh",
                "label",
                "create",
                label["name"],
                "--repo",
                repo,
                "--color",
                label["color"],
                "--description",
                label["description"],
                "--force",
            ]
        )
    return commands


def build_milestone_create_command(repo: str, milestone: dict[str, Any]) -> list[str]:
    return [
        "gh",
        "api",
        "--method",
        "POST",
        f"repos/{repo}/milestones",
        "-f",
        f"title={milestone['title']}",
        "-f",
        f"description={milestone['description']}",
    ]


def build_milestone_update_command(repo: str, milestone_number: int, milestone: dict[str, Any]) -> list[str]:
    return [
        "gh",
        "api",
        "--method",
        "PATCH",
        f"repos/{repo}/milestones/{milestone_number}",
        "-f",
        f"title={milestone['title']}",
        "-f",
        f"description={milestone['description']}",
    ]


def build_initial_issue_create_command(repo: str, issue: dict[str, Any]) -> list[str]:
    command = [
        "gh",
        "issue",
        "create",
        "--repo",
        repo,
        "--title",
        issue["title"],
        "--body",
        issue["bodySummary"],
        "--milestone",
        issue["milestone"],
    ]
    for label in issue["labels"]:
        command.extend(["--label", label])
    return command


def build_initial_issue_edit_command(
    repo: str,
    issue_number: int,
    *,
    body: str | None = None,
    milestone: str | None = None,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
) -> list[str]:
    command = [
        "gh",
        "issue",
        "edit",
        str(issue_number),
        "--repo",
        repo,
    ]
    if body is not None:
        command.extend(["--body", body])
    if milestone:
        command.extend(["--milestone", milestone])
    for label in add_labels or []:
        command.extend(["--add-label", label])
    for label in remove_labels or []:
        command.extend(["--remove-label", label])
    return command


def build_initial_issue_state_command(repo: str, issue_number: int, state: str) -> list[str]:
    if state == "OPEN":
        return [
            "gh",
            "issue",
            "reopen",
            str(issue_number),
            "--repo",
            repo,
        ]
    if state == "CLOSED":
        return [
            "gh",
            "issue",
            "close",
            str(issue_number),
            "--repo",
            repo,
        ]
    raise ValueError(f"unsupported issue state command target: {state}")


def parse_issue_number_from_url(repo: str, issue_url: str | None) -> int | None:
    if not isinstance(issue_url, str) or not issue_url:
        return None
    prefix = f"https://github.com/{repo}/issues/"
    if not issue_url.startswith(prefix):
        return None
    suffix = issue_url[len(prefix) :].split("/", 1)[0]
    if not suffix.isdigit():
        return None
    return int(suffix)


def build_branch_protection_payload(repo_settings: dict[str, Any], status_check_contexts: list[str]) -> dict[str, Any]:
    branch_protection = repo_settings["branchProtection"]
    required_status_checks = None
    if branch_protection.get("requireStatusChecks") and status_check_contexts:
        required_status_checks = {
            "strict": True,
            "contexts": status_check_contexts,
        }

    return {
        "required_status_checks": required_status_checks,
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": branch_protection["dismissStaleApprovals"],
            "require_code_owner_reviews": branch_protection["requireCodeOwnerReview"],
            "required_approving_review_count": branch_protection["requiredApprovals"],
            "require_last_push_approval": False,
        }
        if branch_protection["requirePullRequest"]
        else None,
        "restrictions": None,
        "required_conversation_resolution": branch_protection["requireConversationResolution"],
        "allow_force_pushes": branch_protection["allowForcePushes"],
        "allow_deletions": branch_protection["allowDeletion"],
        "block_creations": False,
        "required_linear_history": False,
        "lock_branch": False,
        "allow_fork_syncing": False,
    }


def build_branch_protection_command(repo: str, repo_settings: dict[str, Any]) -> list[str]:
    return [
        "gh",
        "api",
        "--method",
        "PUT",
        "-H",
        "Accept: application/vnd.github+json",
        f"repos/{repo}/branches/{repo_settings['defaultBranch']}/protection",
        "--input",
        "-",
    ]


def format_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def run_command(command: list[str], *, dry_run: bool, input_text: str | None = None) -> None:
    if dry_run:
        return
    subprocess.run(command, cwd=REPO_ROOT, check=True, text=True, input=input_text)


def run_json_command(command: list[str], *, allow_not_found: bool = False) -> Any | None:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        combined = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        if allow_not_found and any(marker in combined for marker in ["404", "Not Found", "Branch not protected"]):
            return None
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
    return json.loads(result.stdout)


def _format_called_process_error(exc: subprocess.CalledProcessError) -> str:
    output = exc.output.strip() if isinstance(exc.output, str) else ""
    stderr = exc.stderr.strip() if isinstance(exc.stderr, str) else ""
    return "\n".join(part for part in [output, stderr] if part)


def _is_branch_protection_probe_auth_error(exc: subprocess.CalledProcessError) -> bool:
    combined = _format_called_process_error(exc)
    return any(
        marker in combined
        for marker in [
            "403",
            "Forbidden",
            "Resource not accessible by integration",
            "Requires admin access",
            "Must have admin rights to Repository",
        ]
    )


def fetch_active_github_auth_context(
    *,
    hostname: str = "github.com",
    required_scopes: list[str] | None = None,
) -> dict[str, Any] | None:
    try:
        payload = run_json_command(
            [
                "gh",
                "auth",
                "status",
                "--active",
                "--hostname",
                hostname,
                "--json",
                "hosts",
                "--jq",
                "{hosts: (.hosts | with_entries(.value |= map({active, login, scopes, tokenSource})))}",
            ]
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    hosts_payload = payload.get("hosts")
    host_entries = hosts_payload.get(hostname) if isinstance(hosts_payload, dict) else None
    if not isinstance(host_entries, list) or not host_entries:
        return None

    active_entry = next(
        (item for item in host_entries if isinstance(item, dict) and item.get("active") is True),
        None,
    )
    if active_entry is None:
        active_entry = next((item for item in host_entries if isinstance(item, dict)), None)
    if not isinstance(active_entry, dict):
        return None

    raw_scopes = active_entry.get("scopes")
    if isinstance(raw_scopes, str):
        scopes = [scope.strip() for scope in raw_scopes.split(",") if scope.strip()]
    elif isinstance(raw_scopes, list):
        scopes = [scope.strip() for scope in raw_scopes if isinstance(scope, str) and scope.strip()]
    else:
        scopes = []

    missing_scopes = [scope for scope in (required_scopes or []) if scope not in scopes]
    return {
        "host": hostname,
        "login": active_entry.get("login") if isinstance(active_entry.get("login"), str) else None,
        "tokenSource": active_entry.get("tokenSource") if isinstance(active_entry.get("tokenSource"), str) else None,
        "scopes": scopes,
        "missingScopes": missing_scopes,
    }


def fetch_existing_milestones(repo: str) -> dict[str, int]:
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    milestones: dict[str, int] = {}
    for item in payload:
        title = item.get("title")
        number = item.get("number")
        if isinstance(title, str) and isinstance(number, int):
            milestones[title] = number
    return milestones


def ensure_milestones(repo: str, milestones: list[dict[str, Any]], *, dry_run: bool) -> list[str]:
    if dry_run:
        return [format_command(build_milestone_create_command(repo, milestone)) for milestone in milestones]

    existing = fetch_existing_milestones(repo)
    applied_commands: list[str] = []
    for milestone in milestones:
        title = milestone["title"]
        if title in existing:
            command = build_milestone_update_command(repo, existing[title], milestone)
        else:
            command = build_milestone_create_command(repo, milestone)
        run_command(command, dry_run=False)
        applied_commands.append(format_command(command))
    return applied_commands


def _dedupe_status_check_contexts(status_check_contexts: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for context in status_check_contexts:
        if context in seen:
            continue
        seen.add(context)
        ordered.append(context)
    return ordered


def default_status_check_contexts(plan: dict[str, Any]) -> list[str]:
    repo_defaults = plan["repo_settings"]["branchProtection"].get("defaultStatusCheckContexts", [])
    if repo_defaults:
        return _dedupe_status_check_contexts(repo_defaults)
    return _dedupe_status_check_contexts(
        [job["expectedStatusCheckContext"] for job in plan["ci"]["jobs"] if job.get("expectedStatusCheckContext")]
    )


def _extract_repo_visibility(repo_state: dict[str, Any]) -> str | None:
    visibility = repo_state.get("visibility")
    if isinstance(visibility, str) and visibility:
        return visibility
    private = repo_state.get("private")
    if private is True:
        return "private"
    if private is False:
        return "public"
    return None


def _extract_security_status(repo_state: dict[str, Any], key: str) -> bool | None:
    security = repo_state.get("security_and_analysis")
    if not isinstance(security, dict):
        return None
    value = security.get(key)
    if not isinstance(value, dict):
        return None
    status = value.get("status")
    if status == "enabled":
        return True
    if status == "disabled":
        return False
    return None


def _unwrap_enabled(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        enabled = value.get("enabled")
        if isinstance(enabled, bool):
            return enabled
    return None


def _matches_expected_subset(expected: Any, actual: Any) -> bool:
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return actual == expected
    return all(actual.get(key) == value for key, value in expected.items())


def _normalize_multiline_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value.replace("\r\n", "\n")


def _make_live_check(
    scope: str,
    field: str,
    expected: Any,
    actual: Any,
    *,
    none_status: str = "unknown",
    subset_match: bool = False,
) -> dict[str, Any]:
    if actual is None:
        status = none_status
    elif subset_match and _matches_expected_subset(expected, actual):
        status = "match"
    elif actual == expected:
        status = "match"
    else:
        status = "drift"
    return {
        "scope": scope,
        "field": field,
        "expected": expected,
        "actual": actual,
        "status": status,
    }


def fetch_live_repo_state(repo: str) -> dict[str, Any]:
    payload = run_json_command(
        ["gh", "api", "-H", "Accept: application/vnd.github+json", f"repos/{repo}"]
    )
    assert isinstance(payload, dict)
    return payload


def fetch_live_branch_protection_state(repo: str, default_branch: str) -> dict[str, Any] | None:
    try:
        payload = run_json_command(
            [
                "gh",
                "api",
                "-H",
                "Accept: application/vnd.github+json",
                f"repos/{repo}/branches/{default_branch}/protection",
            ],
            allow_not_found=True,
        )
    except subprocess.CalledProcessError as exc:
        if _is_branch_protection_probe_auth_error(exc):
            return {"_probeAuthError": _format_called_process_error(exc) or "branch protection probe requires elevated GitHub repo admin access"}
        raise
    if payload is None:
        return None
    assert isinstance(payload, dict)
    return payload


def fetch_live_labels_state(repo: str) -> dict[str, dict[str, Any]]:
    payload = run_json_command(["gh", "api", f"repos/{repo}/labels?per_page=100"])
    assert isinstance(payload, list)
    labels: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue
        color = item.get("color")
        labels[name] = {
            "color": color.lower() if isinstance(color, str) else color,
            "description": item.get("description") if isinstance(item.get("description"), str) else None,
        }
    return labels


def fetch_live_milestones_state(repo: str) -> dict[str, dict[str, Any]]:
    payload = run_json_command(["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"])
    assert isinstance(payload, list)
    milestones: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        if not isinstance(title, str) or not title:
            continue
        milestones[title] = {
            "description": item.get("description") if isinstance(item.get("description"), str) else None,
        }
    return milestones


def fetch_live_initial_issues_state(repo: str) -> dict[str, dict[str, Any]]:
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "100",
            "--json",
            "title,url,labels,milestone,state,body",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    issues: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        if not isinstance(title, str) or not title:
            continue
        labels_payload = item.get("labels") if isinstance(item.get("labels"), list) else []
        labels = sorted(
            label.get("name")
            for label in labels_payload
            if isinstance(label, dict) and isinstance(label.get("name"), str) and label.get("name")
        )
        milestone = item.get("milestone") if isinstance(item.get("milestone"), dict) else None
        milestone_title = milestone.get("title") if isinstance(milestone, dict) and isinstance(milestone.get("title"), str) else None
        issues[title] = {
            "url": item.get("url") if isinstance(item.get("url"), str) else None,
            "state": item.get("state") if isinstance(item.get("state"), str) else None,
            "labels": labels,
            "milestone": milestone_title,
            "body": _normalize_multiline_text(item.get("body")),
        }
    return issues


def fetch_live_discussion_categories_state(repo: str) -> dict[str, Any]:
    owner, name = repo.split("/", 1)
    query = (
        "query=query($owner:String!,$repo:String!){repository(owner:$owner,name:$repo){"
        "id hasDiscussionsEnabled discussionCategories(first:20){nodes{id name description emojiHTML isAnswerable slug}} "
        "pinnedDiscussions(first:20){nodes{discussion{id title url body category{id name description slug}}}} "
        "discussions(first:50){nodes{id title url body category{id name description slug}}}}}"
    )
    payload = run_json_command(
        [
            "gh",
            "api",
            "graphql",
            "--raw-field",
            query,
            "-F",
            f"owner={owner}",
            "-F",
            f"repo={name}",
        ]
    )
    assert isinstance(payload, dict)
    data = payload.get("data")
    repository = data.get("repository") if isinstance(data, dict) else None
    assert isinstance(repository, dict)
    categories_payload = repository.get("discussionCategories")
    nodes = categories_payload.get("nodes") if isinstance(categories_payload, dict) else []
    categories: dict[str, dict[str, Any]] = {}
    if isinstance(nodes, list):
        for item in nodes:
            if not isinstance(item, dict):
                continue
            category_name = item.get("name")
            if not isinstance(category_name, str) or not category_name:
                continue
            categories[category_name] = {
                "id": item.get("id") if isinstance(item.get("id"), str) else None,
                "description": item.get("description") if isinstance(item.get("description"), str) else None,
                "slug": item.get("slug") if isinstance(item.get("slug"), str) else None,
                "emojiHtml": item.get("emojiHTML") if isinstance(item.get("emojiHTML"), str) else None,
                "isAnswerable": item.get("isAnswerable") if isinstance(item.get("isAnswerable"), bool) else None,
            }

    def _extract_discussion_topics(payload: Any, *, pinned: bool) -> list[dict[str, Any]]:
        nodes = payload.get("nodes") if isinstance(payload, dict) else []
        topics: list[dict[str, Any]] = []
        if not isinstance(nodes, list):
            return topics
        for item in nodes:
            if not isinstance(item, dict):
                continue
            discussion = item.get("discussion") if isinstance(item.get("discussion"), dict) else item
            if not isinstance(discussion, dict):
                continue
            title = discussion.get("title")
            if not isinstance(title, str) or not title:
                continue
            category = discussion.get("category") if isinstance(discussion.get("category"), dict) else None
            category_name = category.get("name") if isinstance(category, dict) and isinstance(category.get("name"), str) else None
            category_description = (
                category.get("description")
                if isinstance(category, dict) and isinstance(category.get("description"), str)
                else None
            )
            url = discussion.get("url") if isinstance(discussion.get("url"), str) else None
            body = discussion.get("body") if isinstance(discussion.get("body"), str) else None
            discussion_id = discussion.get("id") if isinstance(discussion.get("id"), str) else None
            category_id = category.get("id") if isinstance(category, dict) and isinstance(category.get("id"), str) else None
            category_slug = category.get("slug") if isinstance(category, dict) and isinstance(category.get("slug"), str) else None
            topics.append(
                {
                    "id": discussion_id,
                    "title": title,
                    "url": url,
                    "body": body,
                    "categoryId": category_id,
                    "categorySlug": category_slug,
                    "categoryName": category_name,
                    "categoryDescription": category_description,
                    "pinned": pinned,
                }
            )
        return topics

    discussion_topics = _extract_discussion_topics(repository.get("discussions"), pinned=False)
    pinned_discussion_topics = _extract_discussion_topics(repository.get("pinnedDiscussions"), pinned=True)
    topics_by_title: dict[str, dict[str, Any]] = {topic["title"]: topic for topic in discussion_topics}
    for topic in pinned_discussion_topics:
        existing = topics_by_title.get(topic["title"])
        if existing is None:
            topics_by_title[topic["title"]] = topic
            continue
        existing["pinned"] = True
        if existing.get("url") is None:
            existing["url"] = topic.get("url")
        if existing.get("categoryId") is None:
            existing["categoryId"] = topic.get("categoryId")
        if existing.get("categorySlug") is None:
            existing["categorySlug"] = topic.get("categorySlug")
        if existing.get("categoryName") is None:
            existing["categoryName"] = topic.get("categoryName")
        if existing.get("categoryDescription") is None:
            existing["categoryDescription"] = topic.get("categoryDescription")
        if existing.get("id") is None:
            existing["id"] = topic.get("id")

    enabled = repository.get("hasDiscussionsEnabled")
    repository_id = repository.get("id") if isinstance(repository.get("id"), str) else None
    discussion_topics_sorted = sorted(topics_by_title.values(), key=lambda topic: str(topic.get("title", "")).lower())
    pinned_titles = sorted(topic["title"] for topic in discussion_topics_sorted if topic.get("pinned") is True)
    return {
        "repositoryId": repository_id,
        "enabled": enabled if isinstance(enabled, bool) else None,
        "categories": categories,
        "discussionTitles": sorted(topic["title"] for topic in discussion_topics_sorted),
        "pinnedDiscussionTitles": pinned_titles,
        "discussionTopics": discussion_topics_sorted,
    }


def fetch_live_project_board_scope_state(repo: str) -> dict[str, Any]:
    owner, _ = repo.split("/", 1)
    missing_scope_message = "Current token lacks read:project scope, so live GitHub Projects board verification is blocked."
    current_auth = fetch_active_github_auth_context(required_scopes=["read:project"])
    try:
        payload = run_json_command(
            [
                "gh",
                "api",
                "graphql",
                "--raw-field",
                (
                    "query=query($owner:String!){repositoryOwner(login:$owner){"
                    "__typename login ... on User { projectsV2(first:1){nodes{id}} } "
                    "... on Organization { projectsV2(first:1){nodes{id}} }}}"
                ),
                "-F",
                f"owner={owner}",
            ]
        )
    except subprocess.CalledProcessError as exc:
        output = exc.output.strip() if isinstance(exc.output, str) else ""
        stderr = exc.stderr.strip() if isinstance(exc.stderr, str) else ""
        combined = "\n".join(part for part in [output, stderr] if part)
        missing_read_project_scope = "read:project" in combined
        return {
            "ownerLogin": owner,
            "ownerType": None,
            "projectsQueryable": False,
            "missingReadProjectScope": missing_read_project_scope,
            "error": missing_scope_message if missing_read_project_scope else (combined or str(exc)),
            "currentAuth": current_auth,
        }

    assert isinstance(payload, dict)
    data = payload.get("data")
    owner_payload = data.get("repositoryOwner") if isinstance(data, dict) else None
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
    error_messages: list[str] = []
    missing_read_project_scope = False
    for item in errors:
        if not isinstance(item, dict):
            continue
        message = item.get("message")
        if not isinstance(message, str):
            continue
        error_messages.append(message)
        if "read:project" in message:
            missing_read_project_scope = True

    owner_type = owner_payload.get("__typename") if isinstance(owner_payload, dict) else None
    return {
        "ownerLogin": owner,
        "ownerType": owner_type if isinstance(owner_type, str) else None,
        "projectsQueryable": False if error_messages else True,
        "missingReadProjectScope": missing_read_project_scope,
        "error": missing_scope_message if missing_read_project_scope else ("\n".join(error_messages) if error_messages else None),
        "currentAuth": current_auth,
    }


def _build_seeded_object_checks(
    scope: str,
    expected_items: dict[str, dict[str, Any]],
    actual_items: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for name, expected in expected_items.items():
        if actual_items is None:
            checks.append(_make_live_check(scope, name, expected, None))
        elif name not in actual_items:
            checks.append({"scope": scope, "field": name, "expected": expected, "actual": None, "status": "drift"})
        else:
            checks.append(_make_live_check(scope, name, expected, actual_items[name]))
    return checks


def build_live_verification_snapshot(
    repo: str,
    plan: dict[str, Any],
    *,
    repo_state: dict[str, Any],
    branch_protection_state: dict[str, Any] | None,
    status_check_contexts: list[str],
    live_labels_state: dict[str, dict[str, Any]] | None = None,
    live_milestones_state: dict[str, dict[str, Any]] | None = None,
    live_initial_issues_state: dict[str, dict[str, Any]] | None = None,
    live_discussions_state: dict[str, Any] | None = None,
    project_board_scope_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_settings = plan["repo_settings"]
    features = repo_settings["features"]
    merge_policy = repo_settings["mergePolicy"]
    security = repo_settings["security"]
    branch_protection = repo_settings["branchProtection"]

    checks = [
        _make_live_check("repo", "visibility", repo_settings["visibility"], _extract_repo_visibility(repo_state)),
        _make_live_check("repo", "description", repo_settings["description"], repo_state.get("description")),
        _make_live_check("repo", "homepage", repo_settings["homepage"], repo_state.get("homepage")),
        _make_live_check("repo", "defaultBranch", repo_settings["defaultBranch"], repo_state.get("default_branch")),
        _make_live_check("repo", "issues", features["issues"], repo_state.get("has_issues")),
        _make_live_check("repo", "discussions", features["discussions"], repo_state.get("has_discussions")),
        _make_live_check("repo", "projects", features["projects"], repo_state.get("has_projects")),
        _make_live_check("repo", "wiki", features["wiki"], repo_state.get("has_wiki")),
        _make_live_check("repo", "mergeCommits", merge_policy["mergeCommits"], repo_state.get("allow_merge_commit")),
        _make_live_check("repo", "squashMerge", merge_policy["squashMerge"], repo_state.get("allow_squash_merge")),
        _make_live_check("repo", "rebaseMerge", merge_policy["rebaseMerge"], repo_state.get("allow_rebase_merge")),
        _make_live_check(
            "repo",
            "autoDeleteHeadBranches",
            merge_policy["autoDeleteHeadBranches"],
            repo_state.get("delete_branch_on_merge"),
        ),
        _make_live_check("security", "secretScanning", security["secretScanning"], _extract_security_status(repo_state, "secret_scanning")),
        _make_live_check(
            "security",
            "pushProtection",
            security["pushProtection"],
            _extract_security_status(repo_state, "secret_scanning_push_protection"),
        ),
    ]
    notes = [
        "unknown means the live GitHub API response did not expose that field in the current auth context.",
        "drift means the live repo no longer matches the checked-in ancap-docs bootstrap seeds.",
    ]

    if branch_protection_state is None:
        checks.extend(
            [
                _make_live_check("branchProtection", "configured", True, False),
                _make_live_check("branchProtection", "requiredStatusChecks", status_check_contexts, None),
            ]
        )
    elif branch_protection_state.get("_probeAuthError"):
        auth_error = branch_protection_state.get("_probeAuthError")
        notes.append(
            "branch protection details were not exposed in the current GitHub auth context; verify the default-branch protection with admin-capable auth if this check matters."
        )
        if isinstance(auth_error, str) and auth_error:
            notes.append(f"branch protection probe error: {auth_error}")
        checks.extend(
            [
                _make_live_check("branchProtection", "configured", True, None),
                _make_live_check("branchProtection", "requiredStatusChecks", _dedupe_status_check_contexts(status_check_contexts), None),
                _make_live_check("branchProtection", "probeAuth", "admin-capable branch protection visibility", None),
            ]
        )
    else:
        required_reviews = branch_protection_state.get("required_pull_request_reviews") or {}
        required_status_checks = branch_protection_state.get("required_status_checks") or {}
        actual_status_check_contexts = _dedupe_status_check_contexts(required_status_checks.get("contexts") or [])
        checks.extend(
            [
                _make_live_check("branchProtection", "configured", True, True),
                _make_live_check("branchProtection", "requirePullRequest", branch_protection["requirePullRequest"], required_reviews is not None),
                _make_live_check(
                    "branchProtection",
                    "requiredApprovals",
                    branch_protection["requiredApprovals"],
                    required_reviews.get("required_approving_review_count"),
                ),
                _make_live_check(
                    "branchProtection",
                    "dismissStaleApprovals",
                    branch_protection["dismissStaleApprovals"],
                    required_reviews.get("dismiss_stale_reviews"),
                ),
                _make_live_check(
                    "branchProtection",
                    "requireCodeOwnerReview",
                    branch_protection["requireCodeOwnerReview"],
                    required_reviews.get("require_code_owner_reviews"),
                ),
                _make_live_check(
                    "branchProtection",
                    "requireConversationResolution",
                    branch_protection["requireConversationResolution"],
                    _unwrap_enabled(branch_protection_state.get("required_conversation_resolution")),
                ),
                _make_live_check(
                    "branchProtection",
                    "allowForcePushes",
                    branch_protection["allowForcePushes"],
                    _unwrap_enabled(branch_protection_state.get("allow_force_pushes")),
                ),
                _make_live_check(
                    "branchProtection",
                    "allowDeletion",
                    branch_protection["allowDeletion"],
                    _unwrap_enabled(branch_protection_state.get("allow_deletions")),
                ),
                _make_live_check(
                    "branchProtection",
                    "requiredStatusChecks",
                    _dedupe_status_check_contexts(status_check_contexts),
                    actual_status_check_contexts,
                ),
                _make_live_check(
                    "branchProtection",
                    "strictStatusChecks",
                    branch_protection.get("requireStatusChecks", False),
                    required_status_checks.get("strict"),
                ),
            ]
        )

    community_verification_enabled = any(
        state is not None
        for state in (live_labels_state, live_milestones_state, live_initial_issues_state, live_discussions_state)
    )
    if live_labels_state is not None:
        expected_labels = {
            label["name"]: {
                "color": label["color"].lower(),
                "description": label["description"],
            }
            for label in plan["labels"]
        }
        checks.extend(_build_seeded_object_checks("label", expected_labels, live_labels_state))

    if live_milestones_state is not None:
        expected_milestones = {
            milestone["title"]: {
                "description": milestone["description"],
            }
            for milestone in plan["milestones"]
        }
        checks.extend(_build_seeded_object_checks("milestone", expected_milestones, live_milestones_state))

    manual_follow_ups: dict[str, Any] = {}
    if live_initial_issues_state is not None:
        initial_issue_follow_ups: list[dict[str, Any]] = []
        initial_issue_actions: list[dict[str, Any]] = []
        for issue in plan["initial_issues"]:
            expected_body = _normalize_multiline_text(issue["bodySummary"])
            expected_state = issue.get("expectedState")
            status_note = issue.get("statusNote")
            expected = {
                "milestone": issue["milestone"],
                "labels": sorted(issue["labels"]),
                "body": expected_body,
            }
            if isinstance(expected_state, str) and expected_state:
                expected["state"] = expected_state
            actual_issue = live_initial_issues_state.get(issue["title"])
            actual = None
            actual_body = None
            actual_state = None
            if isinstance(actual_issue, dict):
                actual_body = _normalize_multiline_text(actual_issue.get("body"))
                actual_state = actual_issue.get("state") if isinstance(actual_issue.get("state"), str) else None
                actual = {
                    "milestone": actual_issue.get("milestone"),
                    "labels": actual_issue.get("labels"),
                    "body": actual_body,
                    "url": actual_issue.get("url"),
                    "state": actual_state,
                }
            checks.append(
                _make_live_check(
                    "initialIssue",
                    issue["title"],
                    expected,
                    actual,
                    none_status="drift",
                    subset_match=True,
                )
            )

            initial_issue_follow_up = {
                "title": issue["title"],
                "milestone": issue["milestone"],
                "labels": issue["labels"],
                "bodySummary": issue["bodySummary"],
                "boardFields": issue["boardFields"],
                "command": format_command(build_initial_issue_create_command(repo, issue)),
                "exists": actual_issue is not None,
                "url": actual_issue.get("url") if isinstance(actual_issue, dict) else None,
                "actualMilestone": actual_issue.get("milestone") if isinstance(actual_issue, dict) else None,
                "actualLabels": actual_issue.get("labels") if isinstance(actual_issue, dict) else None,
                "actualBodySummary": actual_body,
                "bodyMatchesSeed": actual_body == expected_body if isinstance(actual_issue, dict) else None,
                "state": actual_state,
                "expectedState": expected_state,
                "stateMatchesSeed": actual_state == expected_state if isinstance(actual_issue, dict) and isinstance(expected_state, str) else None,
                "statusNote": status_note,
            }
            initial_issue_follow_ups.append(initial_issue_follow_up)

            if not isinstance(actual_issue, dict):
                initial_issue_actions.append(
                    {
                        "kind": "createInitialIssue",
                        "title": issue["title"],
                        "milestone": issue["milestone"],
                        "labels": issue["labels"],
                        "boardFields": issue["boardFields"],
                        "command": initial_issue_follow_up["command"],
                        "instruction": "Create this seeded starter issue in the public docs repo so the initial contributor queue matches the checked-in backlog seed.",
                    }
                )
                continue

            actual_labels = actual_issue.get("labels") if isinstance(actual_issue.get("labels"), list) else []
            actual_milestone = actual_issue.get("milestone") if isinstance(actual_issue.get("milestone"), str) else None
            expected_labels = sorted(issue["labels"])
            actual_labels_sorted = sorted(actual_labels)
            labels_to_add = [label for label in expected_labels if label not in actual_labels_sorted]
            labels_to_remove = [label for label in actual_labels_sorted if label not in expected_labels]
            needs_body_update = actual_body != expected_body
            needs_metadata_update = actual_milestone != issue["milestone"] or actual_labels_sorted != expected_labels or needs_body_update
            issue_number = parse_issue_number_from_url(repo, actual_issue.get("url"))
            reroute_command = None
            if needs_metadata_update and issue_number is not None:
                reroute_command = format_command(
                    build_initial_issue_edit_command(
                        repo,
                        issue_number,
                        body=issue["bodySummary"] if needs_body_update else None,
                        milestone=issue["milestone"],
                        add_labels=labels_to_add,
                        remove_labels=labels_to_remove,
                    )
                )
            if needs_metadata_update:
                initial_issue_actions.append(
                    {
                        "kind": "rerouteInitialIssue",
                        "title": issue["title"],
                        "url": actual_issue.get("url"),
                        "expectedMilestone": issue["milestone"],
                        "actualMilestone": actual_milestone,
                        "expectedLabels": expected_labels,
                        "actualLabels": actual_labels_sorted,
                        "expectedBodySummary": issue["bodySummary"],
                        "actualBodySummary": actual_body,
                        "bodyMatchesSeed": not needs_body_update,
                        "boardFields": issue["boardFields"],
                        "command": reroute_command,
                        "instruction": "Align this seeded starter issue with the checked-in milestone, label routing, and body summary so the first public queue matches the repo seed.",
                    }
                )

            if isinstance(expected_state, str) and actual_state != expected_state:
                state_command = None
                if issue_number is not None:
                    state_command = format_command(build_initial_issue_state_command(repo, issue_number, expected_state))
                initial_issue_actions.append(
                    {
                        "kind": "setInitialIssueState",
                        "title": issue["title"],
                        "url": actual_issue.get("url"),
                        "expectedState": expected_state,
                        "actualState": actual_state,
                        "statusNote": status_note,
                        "boardFields": issue["boardFields"],
                        "command": state_command,
                        "instruction": "Set this seeded starter issue to the checked-in open/closed state so the public backlog reflects current repo truth.",
                    }
                )

        manual_follow_ups["initialIssuesNote"] = (
            "Keep the seeded starter backlog explicit via the checked-in gh issue create commands; use them to open the first public queue on a fresh repo, or to recreate/reconcile issues later if live state drifts."
        )
        manual_follow_ups["initialIssues"] = initial_issue_follow_ups
        manual_follow_ups["initialIssueActions"] = initial_issue_actions

    issue_urls_by_title = {
        issue.get("title"): issue.get("url")
        for issue in initial_issue_follow_ups
        if isinstance(issue, dict) and isinstance(issue.get("title"), str) and isinstance(issue.get("url"), str)
    } if live_initial_issues_state is not None else {}
    discussion_cleanup_issue = None
    if live_initial_issues_state is not None:
        for issue in initial_issue_follow_ups:
            if not isinstance(issue, dict):
                continue
            if issue.get("title") != "Align Discussions categories and pin seeded bootstrap topics":
                continue
            discussion_cleanup_issue = {
                "title": issue.get("title"),
                "url": issue.get("url"),
                "exists": issue.get("exists"),
                "state": issue.get("state"),
                "milestone": issue.get("milestone"),
                "labels": issue.get("labels"),
            }
            break

    if live_discussions_state is not None:
        checks.append(_make_live_check("discussions", "enabled", True, live_discussions_state.get("enabled")))
        actual_categories = live_discussions_state.get("categories")
        expected_categories = {
            category["name"]: {
                "description": category["description"],
            }
            for category in plan["discussions"]["categories"]
        }
        if isinstance(actual_categories, dict):
            checks.extend(_build_seeded_object_checks("discussionCategory", expected_categories, actual_categories))
            checks.append(
                _make_live_check(
                    "discussionCategory",
                    "categoryNames",
                    sorted(expected_categories),
                    sorted(actual_categories),
                )
            )
        else:
            checks.extend(_build_seeded_object_checks("discussionCategory", expected_categories, None))
            checks.append(_make_live_check("discussionCategory", "categoryNames", sorted(expected_categories), None))

        actual_discussion_titles = live_discussions_state.get("discussionTitles")
        actual_discussion_title_set = set(actual_discussion_titles) if isinstance(actual_discussion_titles, list) else None
        actual_pinned_titles = live_discussions_state.get("pinnedDiscussionTitles")
        actual_pinned_title_set = set(actual_pinned_titles) if isinstance(actual_pinned_titles, list) else None
        discussion_topics_payload = live_discussions_state.get("discussionTopics")
        discussion_topics = discussion_topics_payload if isinstance(discussion_topics_payload, list) else []
        discussion_topics_by_title = {
            item["title"]: item
            for item in discussion_topics
            if isinstance(item, dict) and isinstance(item.get("title"), str) and item.get("title")
        }
        expected_discussion_topic_bodies = {
            topic["title"]: _normalize_multiline_text(topic.get("starterBody"))
            for topic in plan["discussions"]["pinnedTopics"]
        }
        for topic in plan["discussions"]["pinnedTopics"]:
            title = topic["title"]
            actual_topic = discussion_topics_by_title.get(title)
            actual_topic_body = _normalize_multiline_text(actual_topic.get("body")) if isinstance(actual_topic, dict) else None
            expected_topic_body = expected_discussion_topic_bodies.get(title)
            actual_body_matches_seed = None
            if actual_topic is not None and actual_topic_body is not None and expected_topic_body is not None:
                actual_body_matches_seed = actual_topic_body == expected_topic_body
            checks.append(
                _make_live_check(
                    "discussionTopic",
                    title,
                    True,
                    title in actual_discussion_title_set if actual_discussion_title_set is not None else None,
                )
            )
            checks.append(
                _make_live_check(
                    "pinnedDiscussionTopic",
                    title,
                    True,
                    title in actual_pinned_title_set if actual_pinned_title_set is not None else None,
                )
            )
            if isinstance(actual_topic, dict):
                checks.append(
                    _make_live_check(
                        "discussionTopicBody",
                        title,
                        True,
                        actual_body_matches_seed,
                    )
                )

        category_description_drift: list[dict[str, Any]] = []
        unexpected_categories: list[str] = []
        missing_categories: list[str] = []
        if isinstance(actual_categories, dict):
            unexpected_categories = sorted(name for name in actual_categories if name not in expected_categories)
            missing_categories = sorted(name for name in expected_categories if name not in actual_categories)
            for name, expected in expected_categories.items():
                actual = actual_categories.get(name)
                if not isinstance(actual, dict):
                    continue
                actual_description = actual.get("description")
                if actual_description != expected["description"]:
                    category_description_drift.append(
                        {
                            "name": name,
                            "expectedDescription": expected["description"],
                            "actualDescription": actual_description,
                        }
                    )
        category_description_drift.sort(key=lambda item: str(item.get("name", "")).lower())
        manual_follow_ups["discussionCategories"] = {
            "expected": sorted(expected_categories),
            "actual": sorted(actual_categories) if isinstance(actual_categories, dict) else None,
            "missing": missing_categories,
            "unexpected": unexpected_categories,
            "descriptionDrift": category_description_drift,
        }
        manual_follow_ups["discussionUi"] = {
            "landingUrl": f"https://github.com/{repo}/discussions",
            "expectedCategoryNames": sorted(expected_categories),
            "expectedCategoryDescriptions": [
                {
                    "name": name,
                    "description": expected_categories[name]["description"],
                }
                for name in sorted(expected_categories)
            ],
        }
        if isinstance(discussion_cleanup_issue, dict):
            manual_follow_ups["discussionCleanupIssue"] = discussion_cleanup_issue
        expected_discussion_topic_categories = {
            topic["title"]: topic.get("categoryName")
            for topic in plan["discussions"]["pinnedTopics"]
            if isinstance(topic.get("categoryName"), str)
        }
        expected_discussion_topics_by_title = {
            topic["title"]: topic
            for topic in plan["discussions"]["pinnedTopics"]
            if isinstance(topic, dict) and isinstance(topic.get("title"), str) and topic.get("title")
        }
        manual_follow_ups["discussionTopics"] = [
            {
                "title": title,
                "url": actual_topic.get("url") if isinstance(actual_topic, dict) else None,
                "discussionId": actual_topic.get("id") if isinstance(actual_topic, dict) else None,
                "expectedBody": expected_discussion_topic_bodies.get(title),
                "categoryId": actual_topic.get("categoryId") if isinstance(actual_topic, dict) else None,
                "categorySlug": actual_topic.get("categorySlug") if isinstance(actual_topic, dict) else None,
                "categoryName": actual_topic.get("categoryName") if isinstance(actual_topic, dict) else None,
                "categoryDescription": actual_topic.get("categoryDescription") if isinstance(actual_topic, dict) else None,
                "expectedCategoryName": expected_discussion_topic_categories.get(title),
                "expectedPinned": True,
                "actualPinned": title in actual_pinned_title_set if actual_pinned_title_set is not None else None,
                "bodyMatchesSeed": (
                    _normalize_multiline_text(actual_topic.get("body")) == expected_discussion_topic_bodies.get(title)
                    if isinstance(actual_topic, dict)
                    and _normalize_multiline_text(actual_topic.get("body")) is not None
                    and expected_discussion_topic_bodies.get(title) is not None
                    else None
                ),
            }
            for title in [topic["title"] for topic in plan["discussions"]["pinnedTopics"]]
            for actual_topic in [discussion_topics_by_title.get(title)]
        ]
        discussion_admin_actions: list[dict[str, Any]] = []
        for name in missing_categories:
            expected = expected_categories[name]
            discussion_admin_actions.append(
                {
                    "kind": "createMissingCategory",
                    "categoryName": name,
                    "expectedDescription": expected["description"],
                    "instruction": "Create this missing seeded Discussions category in the GitHub UI using the checked-in seed description.",
                }
            )
        for name in unexpected_categories:
            actual = actual_categories.get(name) if isinstance(actual_categories, dict) else None
            discussion_admin_actions.append(
                {
                    "kind": "removeUnexpectedCategory",
                    "categoryName": name,
                    "actualDescription": actual.get("description") if isinstance(actual, dict) else None,
                    "instruction": "Remove or repurpose this extra live Discussions category in the GitHub UI so the category set matches the checked-in seed.",
                }
            )
        for item in category_description_drift:
            discussion_admin_actions.append(
                {
                    "kind": "updateCategoryDescription",
                    "categoryName": item["name"],
                    "expectedDescription": item["expectedDescription"],
                    "actualDescription": item["actualDescription"],
                    "instruction": "Update the live Discussions category description in the GitHub UI so it matches the checked-in seed.",
                }
            )
        for item in manual_follow_ups["discussionTopics"]:
            title = item["title"]
            if item.get("url") is None:
                expected_topic = expected_discussion_topics_by_title.get(title)
                discussion_admin_actions.append(
                    {
                        "kind": "createAndPinDiscussionTopic",
                        "title": title,
                        "body": expected_topic.get("starterBody") if isinstance(expected_topic, dict) else None,
                        "expectedCategoryName": item.get("expectedCategoryName"),
                        "instruction": "Create this missing seeded bootstrap discussion from docs/ANCAP_DOCS_DISCUSSIONS_SEED.md or .github/bootstrap/ancap-docs-discussions.json, place it in the seeded category, then pin it in the GitHub UI.",
                    }
                )
        for item in manual_follow_ups["discussionTopics"]:
            title = item["title"]
            if item.get("url") is None:
                continue
            expected_category_name = item.get("expectedCategoryName")
            actual_category_name = item.get("categoryName")
            if expected_category_name and actual_category_name and actual_category_name != expected_category_name:
                discussion_admin_actions.append(
                    {
                        "kind": "moveDiscussionTopicCategory",
                        "title": title,
                        "url": item.get("url"),
                        "expectedCategoryName": expected_category_name,
                        "actualCategoryName": actual_category_name,
                        "instruction": "Move this seeded bootstrap discussion into the expected seeded category so the live Discussions lane matches the checked-in seed.",
                    }
                )
            if item.get("bodyMatchesSeed") is False:
                discussion_admin_actions.append(
                    {
                        "kind": "updateDiscussionTopicBody",
                        "title": title,
                        "url": item.get("url"),
                        "body": item.get("expectedBody"),
                        "instruction": "Re-edit this seeded bootstrap discussion body in the GitHub UI so it matches the checked-in Discussions seed copy.",
                    }
                )
        for item in manual_follow_ups["discussionTopics"]:
            title = item["title"]
            if item.get("url") is None:
                continue
            if item.get("actualPinned") is not True:
                discussion_admin_actions.append(
                    {
                        "kind": "pinDiscussionTopic",
                        "title": title,
                        "url": item.get("url"),
                        "instruction": "Pin this already-seeded bootstrap discussion in the GitHub UI so the live Discussions landing surface matches the checked-in seed.",
                    }
                )
        manual_follow_ups["discussionAdminActions"] = discussion_admin_actions
        manual_follow_ups["discussionAdminActionAutomation"] = build_discussion_admin_action_automation_summary(
            discussion_admin_actions,
            categories=actual_categories if isinstance(actual_categories, dict) else None,
            discussion_topics_by_title=discussion_topics_by_title,
            repository_id=live_discussions_state.get("repositoryId") if isinstance(live_discussions_state, dict) else None,
        )

    if community_verification_enabled:
        notes.extend(
            [
                "community verification mode also checks seeded labels, milestones, initial issue backlog presence/routing, Discussions category state, seeded discussion-topic presence, seeded discussion-topic body alignment, and pinned-discussion presence.",
                "GitHub Projects boards still require owner-capability follow-up beyond this helper's live checks.",
            ]
        )

    if live_discussions_state is not None:
        notes.append(
            "This helper currently verifies Discussions category drift, seeded discussion-topic category/body drift, and pinned-topic presence. GitHub's public GraphQL surface does expose createDiscussion/updateDiscussion for future missing-topic, topic-body, or category-reassignment follow-up, but this helper does not apply those mutations today. The remaining live seeded-surface gaps still need GitHub UI or a future owner-capable automation path because the public gh/API path does not expose a complete category lifecycle/description or discussion-pinning admin flow; use docs/ANCAP_DOCS_DISCUSSIONS_SEED.md and .github/bootstrap/ancap-docs-discussions.json as the source of truth."
        )

    if project_board_scope_state is not None:
        owner_login = project_board_scope_state.get("ownerLogin")
        owner_label = owner_login if isinstance(owner_login, str) and owner_login else "the target owner"
        if project_board_scope_state.get("missingReadProjectScope"):
            notes.append(
                f"live GitHub Projects board verification for {owner_label} is currently blocked because the active token lacks read:project scope; keep the project-board seed documented and defer live seeding/verification until project-capable auth is available."
            )
        elif project_board_scope_state.get("error"):
            notes.append(
                f"live GitHub Projects board verification probe for {owner_label} could not complete in the current auth context; keep the project-board seed documented and verify manually once owner/project-capable auth is available."
            )

    if project_board_scope_state is not None:
        project_board_setup = build_project_board_setup(
            repo,
            plan["project_board"],
            plan["initial_issues"],
            issue_urls_by_title=issue_urls_by_title,
        )
        auth_refresh_command = None
        if project_board_scope_state.get("missingReadProjectScope"):
            auth_refresh_command = "gh auth refresh -h github.com -s read:project"
        manual_follow_ups["projectBoard"] = {
            "ownerLogin": project_board_scope_state.get("ownerLogin"),
            "projectsQueryable": project_board_scope_state.get("projectsQueryable"),
            "missingReadProjectScope": project_board_scope_state.get("missingReadProjectScope"),
            "error": project_board_scope_state.get("error"),
            "authRefreshCommand": auth_refresh_command,
            "currentAuth": project_board_scope_state.get("currentAuth"),
            "name": plan["project_board"]["name"],
            "scope": plan["project_board"]["scope"],
            "fields": [
                {
                    "name": field.get("name"),
                    "kind": field.get("kind"),
                    "options": field.get("options"),
                    "source": field.get("source"),
                }
                for field in plan["project_board"]["fields"]
            ],
            "views": [
                {
                    "name": view.get("name"),
                    "layout": view.get("layout"),
                    "groupBy": view.get("groupBy"),
                    "filters": view.get("filters"),
                }
                for view in plan["project_board"]["views"]
            ],
            "notes": plan["project_board"]["notes"],
            "projectNumberPlaceholder": project_board_setup["projectNumberPlaceholder"],
            "commands": project_board_setup["commands"],
            "fieldCommands": project_board_setup["fieldCommands"],
            "manualSteps": project_board_setup["manualSteps"],
            "starterIssueBoarding": project_board_setup["starterIssueBoarding"],
        }
        project_board_actions: list[dict[str, Any]] = []
        if project_board_scope_state.get("missingReadProjectScope"):
            project_board_actions.append(
                {
                    "kind": "requestProjectScope",
                    "instruction": "Refresh GitHub auth with read:project scope (or switch to owner-capable project auth) before trying live project-board seeding or verification again.",
                    "command": auth_refresh_command,
                }
            )
        elif project_board_scope_state.get("error"):
            project_board_actions.append(
                {
                    "kind": "inspectProjectBoardProbeError",
                    "error": project_board_scope_state.get("error"),
                    "instruction": "Inspect the current GitHub Projects probe error, then retry live project-board verification once the auth/runtime blocker is removed.",
                }
            )
        project_board_actions.append(
            {
                "kind": "seedProjectBoard",
                "boardName": plan["project_board"]["name"],
                "instruction": "Seed or verify the public docs project board from docs/ANCAP_DOCS_PROJECT_BOARD_SEED.md and .github/bootstrap/ancap-docs-project-board.json once project-capable auth exists.",
            }
        )
        manual_follow_ups["projectBoardActions"] = project_board_actions

    drift_count = sum(1 for check in checks if check["status"] == "drift")
    unknown_count = sum(1 for check in checks if check["status"] == "unknown")
    snapshot = {
        "repo": repo,
        "ok": drift_count == 0 and unknown_count == 0,
        "driftCount": drift_count,
        "unknownCount": unknown_count,
        "checks": checks,
        "driftSummary": build_live_verification_drift_summary(checks),
        "notes": notes,
    }
    if manual_follow_ups:
        snapshot["manualFollowUps"] = manual_follow_ups
        snapshot["manualFollowUpSummary"] = build_live_verification_manual_follow_up_summary(manual_follow_ups)
    return snapshot


def build_live_verification_drift_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    drift_checks: list[dict[str, str]] = []
    unknown_checks: list[dict[str, str]] = []
    drift_count_by_scope: dict[str, int] = {}
    unknown_count_by_scope: dict[str, int] = {}

    for check in checks:
        if not isinstance(check, dict):
            continue
        scope = check.get("scope")
        field = check.get("field")
        status = check.get("status")
        if not isinstance(scope, str) or not scope or not isinstance(field, str) or not field:
            continue

        identifier = {"scope": scope, "field": field}
        if status == "drift":
            drift_checks.append(identifier)
            drift_count_by_scope[scope] = drift_count_by_scope.get(scope, 0) + 1
        elif status == "unknown":
            unknown_checks.append(identifier)
            unknown_count_by_scope[scope] = unknown_count_by_scope.get(scope, 0) + 1

    return {
        "driftChecks": drift_checks,
        "unknownChecks": unknown_checks,
        "driftCountByScope": drift_count_by_scope,
        "unknownCountByScope": unknown_count_by_scope,
    }


def build_live_verification_manual_follow_up_summary(manual_follow_ups: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in ("initialIssueActions", "discussionAdminActions", "projectBoardActions"):
        actions = manual_follow_ups.get(key)
        if not isinstance(actions, list):
            continue

        by_kind: dict[str, int] = {}
        for item in actions:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if isinstance(kind, str) and kind:
                by_kind[kind] = by_kind.get(kind, 0) + 1

        summary[key] = {
            "count": len(actions),
            "byKind": by_kind,
        }

    return summary


def render_live_verification(snapshot: dict[str, Any]) -> str:
    lines = [
        f"Live repo verification for {snapshot['repo']}",
        "",
        f"Overall OK: {snapshot['ok']}",
        f"Drift count: {snapshot['driftCount']}",
        f"Unknown count: {snapshot['unknownCount']}",
        "",
        "Checks:",
    ]
    for check in snapshot["checks"]:
        lines.append(
            f"- [{check['status'].upper()}] {check['scope']}.{check['field']}: expected {json.dumps(check['expected'])}; actual {json.dumps(check['actual'])}"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in snapshot["notes"])

    manual_follow_ups = snapshot.get("manualFollowUps")
    if isinstance(manual_follow_ups, dict) and manual_follow_ups:
        lines.extend(["", "Manual follow-ups:"])
        discussion_categories = manual_follow_ups.get("discussionCategories")
        if isinstance(discussion_categories, dict):
            missing = discussion_categories.get("missing") or []
            unexpected = discussion_categories.get("unexpected") or []
            if missing:
                lines.append(f"- missing seeded Discussion categories: {', '.join(missing)}")
            if unexpected:
                lines.append(f"- unexpected live Discussion categories: {', '.join(unexpected)}")
            description_drift = discussion_categories.get("descriptionDrift") or []
            if isinstance(description_drift, list):
                for item in description_drift:
                    if not isinstance(item, dict):
                        continue
                    lines.append(
                        "- Discussion category description drift "
                        f"for {item.get('name')}: expected {json.dumps(item.get('expectedDescription'))}; "
                        f"actual {json.dumps(item.get('actualDescription'))}"
                    )

        discussion_ui = manual_follow_ups.get("discussionUi")
        if isinstance(discussion_ui, dict):
            landing_url = discussion_ui.get("landingUrl")
            if landing_url:
                lines.append(f"- Discussions landing URL: {landing_url}")
            expected_category_descriptions = discussion_ui.get("expectedCategoryDescriptions") or []
            if isinstance(expected_category_descriptions, list) and expected_category_descriptions:
                lines.append("- seeded Discussion category descriptions:")
                for item in expected_category_descriptions:
                    if not isinstance(item, dict):
                        continue
                    lines.append(
                        "  - "
                        f"{item.get('name')} -> {json.dumps(item.get('description'))}"
                    )

        initial_issues = manual_follow_ups.get("initialIssues")
        if isinstance(initial_issues, list) and initial_issues:
            lines.append("- seeded initial issues:")
            for item in initial_issues:
                if not isinstance(item, dict):
                    continue
                state = item.get("state") if item.get("exists") else "MISSING"
                lines.append(
                    "  - "
                    f"{item.get('title')} | exists={item.get('exists')} | state={state} | expectedState={item.get('expectedState')} | "
                    f"stateMatchesSeed={item.get('stateMatchesSeed')} | milestone={item.get('actualMilestone') or item.get('milestone')} | "
                    f"labels={json.dumps(item.get('actualLabels') or item.get('labels'))} | url={item.get('url')}"
                )
                status_note = item.get("statusNote")
                if isinstance(status_note, str) and status_note:
                    lines.append(f"    statusNote={json.dumps(status_note)}")

        initial_issue_actions = manual_follow_ups.get("initialIssueActions")
        if isinstance(initial_issue_actions, list) and initial_issue_actions:
            lines.append("- initial issue actions:")
            for item in initial_issue_actions:
                if not isinstance(item, dict):
                    continue
                target = item.get("url") or item.get("title") or item.get("kind")
                lines.append(
                    "  - "
                    f"{item.get('kind')} | target={target} | instruction={item.get('instruction')}"
                )

        discussion_topics = manual_follow_ups.get("discussionTopics")
        if isinstance(discussion_topics, list) and discussion_topics:
            lines.append("- seeded discussion topics:")
            for item in discussion_topics:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    "  - "
                    f"{item.get('title')} | category={item.get('categoryName')} | "
                    f"bodyMatchesSeed={item.get('bodyMatchesSeed')} | pinned={item.get('actualPinned')} | url={item.get('url')}"
                )

        discussion_admin_actions = manual_follow_ups.get("discussionAdminActions")
        if isinstance(discussion_admin_actions, list) and discussion_admin_actions:
            lines.append("- discussion admin actions:")
            for item in discussion_admin_actions:
                if not isinstance(item, dict):
                    continue
                target = item.get("categoryName") or item.get("title") or item.get("kind")
                lines.append(
                    "  - "
                    f"{item.get('kind')} | target={target} | instruction={item.get('instruction')}"
                )

        discussion_action_automation = manual_follow_ups.get("discussionAdminActionAutomation")
        if isinstance(discussion_action_automation, list) and discussion_action_automation:
            lines.append("- discussion action automation:")
            for item in discussion_action_automation:
                if not isinstance(item, dict):
                    continue
                detail = (
                    f"{item.get('kind')} | target={item.get('target')} | status={item.get('status')} | "
                    f"mutation={item.get('mutation')} | reason={item.get('reason')}"
                )
                blockers = item.get("blockers")
                if isinstance(blockers, list) and blockers:
                    detail += f" | blockers={json.dumps(blockers)}"
                manual_remainder = item.get("manualRemainder")
                if isinstance(manual_remainder, list) and manual_remainder:
                    detail += f" | manualRemainder={json.dumps(manual_remainder)}"
                lines.append("  - " + detail)

        project_board = manual_follow_ups.get("projectBoard")
        if isinstance(project_board, dict):
            lines.append(
                "- project-board verification context: "
                f"owner={project_board.get('ownerLogin')} | "
                f"projectsQueryable={project_board.get('projectsQueryable')} | "
                f"missingReadProjectScope={project_board.get('missingReadProjectScope')}"
            )
            if project_board.get("error"):
                lines.append(f"  - project-board probe error: {project_board.get('error')}")
            if project_board.get("name"):
                lines.append(
                    "- project-board seed target: "
                    f"name={project_board.get('name')} | scope={project_board.get('scope')}"
                )
            fields = project_board.get("fields")
            if isinstance(fields, list) and fields:
                lines.append("- project-board seeded fields:")
                for item in fields:
                    if not isinstance(item, dict):
                        continue
                    detail = f"{item.get('name')} ({item.get('kind')})"
                    options = item.get("options")
                    source = item.get("source")
                    if isinstance(options, list) and options:
                        detail += f" | options={json.dumps(options)}"
                    elif source:
                        detail += f" | source={source}"
                    lines.append(f"  - {detail}")
            views = project_board.get("views")
            if isinstance(views, list) and views:
                lines.append("- project-board seeded views:")
                for item in views:
                    if not isinstance(item, dict):
                        continue
                    detail = f"{item.get('name')} ({item.get('layout')})"
                    group_by = item.get("groupBy")
                    filters = item.get("filters")
                    if group_by:
                        detail += f" | groupBy={group_by}"
                    if isinstance(filters, list) and filters:
                        detail += f" | filters={json.dumps(filters)}"
                    lines.append(f"  - {detail}")
            starter_issue_boarding = project_board.get("starterIssueBoarding")
            if isinstance(starter_issue_boarding, dict):
                lookup_commands = starter_issue_boarding.get("lookupCommands")
                if isinstance(lookup_commands, dict) and lookup_commands:
                    lines.append("- project-board starter issue lookup commands:")
                    for key, label in [("view", "project view"), ("fieldList", "field list")]:
                        command = lookup_commands.get(key)
                        if isinstance(command, str) and command:
                            lines.append(f"  - {label}: {command}")
                starter_items = starter_issue_boarding.get("items")
                if isinstance(starter_items, list) and starter_items:
                    lines.append("- project-board starter issue commands:")
                    for item in starter_items:
                        if not isinstance(item, dict):
                            continue
                        title = item.get("title") or "issue"
                        issue_url = item.get("issueUrl") or "<issue-url>"
                        lines.append(
                            f"  - {title} | issueUrl={issue_url} | addCommand={item.get('addCommand')}"
                        )
                        field_assignments = item.get("fieldAssignments")
                        if isinstance(field_assignments, list):
                            for assignment in field_assignments:
                                if not isinstance(assignment, dict):
                                    continue
                                if assignment.get("command"):
                                    lines.append(
                                        "    - "
                                        f"{assignment.get('field')}={assignment.get('value')} | command={assignment.get('command')}"
                                    )
                                elif assignment.get("note"):
                                    lines.append(
                                        "    - "
                                        f"{assignment.get('field')} note={assignment.get('note')}"
                                    )

        project_board_actions = manual_follow_ups.get("projectBoardActions")
        if isinstance(project_board_actions, list) and project_board_actions:
            lines.append("- project-board actions:")
            for item in project_board_actions:
                if not isinstance(item, dict):
                    continue
                target = item.get("boardName") or item.get("kind")
                detail = (
                    "  - "
                    f"{item.get('kind')} | target={target} | instruction={item.get('instruction')}"
                )
                command = item.get("command")
                if isinstance(command, str) and command:
                    detail += f" | command={command}"
                lines.append(detail)
    return "\n".join(lines) + "\n"


def render_live_verification_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        f"# ANCAP docs live follow-up checklist for {snapshot['repo']}",
        "",
        f"- Overall OK: `{snapshot['ok']}`",
        f"- Drift count: `{snapshot['driftCount']}`",
        f"- Unknown count: `{snapshot['unknownCount']}`",
    ]

    drift_checks = [check for check in snapshot["checks"] if check["status"] in {"drift", "unknown"}]
    if drift_checks:
        lines.extend(["", "## Drift summary"])
        for check in drift_checks:
            lines.append(
                "- "
                f"`{check['scope']}.{check['field']}` -> expected `{json.dumps(check['expected'])}`; "
                f"actual `{json.dumps(check['actual'])}` (`{check['status']}`)"
            )

    manual_follow_ups = snapshot.get("manualFollowUps")
    if isinstance(manual_follow_ups, dict) and manual_follow_ups:
        initial_issues = manual_follow_ups.get("initialIssues")
        initial_issue_actions = manual_follow_ups.get("initialIssueActions")
        if isinstance(initial_issues, list) and initial_issues:
            lines.extend(["", "## Initial issue backlog targets"])
            for item in initial_issues:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                url = item.get("url")
                target = f"[`{title}`]({url})" if item.get("exists") and isinstance(url, str) and url else f"`{title}`"
                state = item.get("state") if item.get("exists") else "MISSING"
                lines.append(
                    "- "
                    f"{target} -> exists `{item.get('exists')}`, state `{state}`, milestone `{item.get('milestone')}`, "
                    f"labels `{', '.join(item.get('labels', []))}`, body matches seed `{item.get('bodyMatchesSeed')}`, "
                    f"expected state `{item.get('expectedState')}`, state matches seed `{item.get('stateMatchesSeed')}`, "
                    f"board fields `{json.dumps(item.get('boardFields'))}`"
                )
                status_note = item.get("statusNote")
                if isinstance(status_note, str) and status_note:
                    lines.append(f"  - status note: {status_note}")
                lines.append(f"  - seed command: `{item.get('command')}`")

        if isinstance(initial_issue_actions, list) and initial_issue_actions:
            lines.extend(["", "## Initial issue backlog checklist"])
            for item in initial_issue_actions:
                if not isinstance(item, dict):
                    continue
                kind = item.get("kind")
                if kind == "createInitialIssue":
                    lines.append(
                        "- [ ] "
                        f"Create seeded starter issue `{item.get('title')}` with milestone `{item.get('milestone')}` and labels `{', '.join(item.get('labels', []))}`."
                    )
                    lines.append(f"  - command: `{item.get('command')}`")
                elif kind == "rerouteInitialIssue":
                    url = item.get("url")
                    target = f"[`{item.get('title')}`]({url})" if isinstance(url, str) and url else f"`{item.get('title')}`"
                    alignment_targets: list[str] = []
                    expected_milestone = item.get("expectedMilestone")
                    if isinstance(expected_milestone, str) and expected_milestone:
                        alignment_targets.append(f"milestone `{expected_milestone}`")
                    expected_labels = item.get("expectedLabels")
                    if isinstance(expected_labels, list) and expected_labels:
                        alignment_targets.append(f"labels `{', '.join(expected_labels)}`")
                    if item.get("bodyMatchesSeed") is False:
                        alignment_targets.append("the checked-in body summary")
                    if alignment_targets:
                        if len(alignment_targets) == 1:
                            alignment_detail = alignment_targets[0]
                        elif len(alignment_targets) == 2:
                            alignment_detail = f"{alignment_targets[0]} and {alignment_targets[1]}"
                        else:
                            alignment_detail = f"{', '.join(alignment_targets[:-1])}, and {alignment_targets[-1]}"
                    else:
                        alignment_detail = "the checked-in seed"
                    lines.append(
                        "- [ ] "
                        f"Align seeded starter issue {target} to {alignment_detail}."
                    )
                    command = item.get("command")
                    if isinstance(command, str) and command:
                        lines.append(f"  - command: `{command}`")
                elif kind == "setInitialIssueState":
                    url = item.get("url")
                    target = f"[`{item.get('title')}`]({url})" if isinstance(url, str) and url else f"`{item.get('title')}`"
                    lines.append(
                        "- [ ] "
                        f"Set seeded starter issue {target} to state `{item.get('expectedState')}`."
                    )
                    status_note = item.get("statusNote")
                    if isinstance(status_note, str) and status_note:
                        lines.append(f"  - status note: {status_note}")
                    command = item.get("command")
                    if isinstance(command, str) and command:
                        lines.append(f"  - command: `{command}`")
                else:
                    lines.append(f"- [ ] {item.get('instruction')}")

        discussion_ui = manual_follow_ups.get("discussionUi")
        if isinstance(discussion_ui, dict):
            lines.extend(["", "## Discussion UI targets"])
            landing_url = discussion_ui.get("landingUrl")
            if isinstance(landing_url, str) and landing_url:
                lines.append(f"- Discussions landing page: {landing_url}")
            discussion_cleanup_issue = manual_follow_ups.get("discussionCleanupIssue")
            if isinstance(discussion_cleanup_issue, dict):
                cleanup_url = discussion_cleanup_issue.get("url")
                cleanup_title = discussion_cleanup_issue.get("title") or "Tracked discussion cleanup issue"
                cleanup_target = (
                    f"[`{cleanup_title}`]({cleanup_url})"
                    if isinstance(cleanup_url, str) and cleanup_url
                    else f"`{cleanup_title}`"
                )
                lines.append(
                    "- Tracked cleanup issue: "
                    f"{cleanup_target} -> state `{discussion_cleanup_issue.get('state')}`, milestone `{discussion_cleanup_issue.get('milestone')}`, labels `{', '.join(discussion_cleanup_issue.get('labels', []))}`"
                )
            expected_category_names = discussion_ui.get("expectedCategoryNames") or []
            if isinstance(expected_category_names, list) and expected_category_names:
                lines.append(
                    "- Keep only seeded categories: "
                    + ", ".join(f"`{name}`" for name in expected_category_names)
                )
            expected_category_descriptions = discussion_ui.get("expectedCategoryDescriptions") or []
            if isinstance(expected_category_descriptions, list) and expected_category_descriptions:
                lines.append("- Expected category descriptions:")
                for item in expected_category_descriptions:
                    if not isinstance(item, dict):
                        continue
                    lines.append(
                        "  - "
                        f"`{item.get('name')}` -> `{item.get('description')}`"
                    )

        discussion_admin_actions = manual_follow_ups.get("discussionAdminActions")
        if isinstance(discussion_admin_actions, list) and discussion_admin_actions:
            lines.extend(["", "## Discussions admin checklist"])
            for item in discussion_admin_actions:
                if not isinstance(item, dict):
                    continue
                kind = item.get("kind")
                if kind == "createMissingCategory":
                    lines.append(
                        "- [ ] "
                        f"Create missing Discussion category `{item.get('categoryName')}` with description "
                        f"`{item.get('expectedDescription')}`."
                    )
                elif kind == "removeUnexpectedCategory":
                    lines.append(
                        "- [ ] "
                        f"Remove or repurpose extra Discussion category `{item.get('categoryName')}` "
                        f"(current description: `{item.get('actualDescription')}`)."
                    )
                elif kind == "updateCategoryDescription":
                    lines.append(
                        "- [ ] "
                        f"Update Discussion category `{item.get('categoryName')}` description from "
                        f"`{item.get('actualDescription')}` to `{item.get('expectedDescription')}`."
                    )
                elif kind == "createAndPinDiscussionTopic":
                    lines.append(
                        "- [ ] "
                        f"Create and pin seeded bootstrap discussion `{item.get('title')}` from the checked-in Discussions seed."
                    )
                elif kind == "moveDiscussionTopicCategory":
                    url = item.get("url")
                    target = f"[`{item.get('title')}`]({url})" if isinstance(url, str) and url else f"`{item.get('title')}`"
                    lines.append(
                        "- [ ] "
                        f"Move seeded bootstrap discussion {target} from `{item.get('actualCategoryName')}` to `{item.get('expectedCategoryName')}`."
                    )
                elif kind == "updateDiscussionTopicBody":
                    url = item.get("url")
                    target = f"[`{item.get('title')}`]({url})" if isinstance(url, str) and url else f"`{item.get('title')}`"
                    lines.append(
                        "- [ ] "
                        f"Re-edit seeded bootstrap discussion body for {target} so it matches the checked-in Discussions seed."
                    )
                elif kind == "pinDiscussionTopic":
                    url = item.get("url")
                    target = f"[`{item.get('title')}`]({url})" if isinstance(url, str) and url else f"`{item.get('title')}`"
                    lines.append(f"- [ ] Pin seeded bootstrap discussion {target}.")
                else:
                    lines.append(f"- [ ] {item.get('instruction')}")

        discussion_topics = manual_follow_ups.get("discussionTopics")
        if isinstance(discussion_topics, list) and discussion_topics:
            lines.extend(["", "## Seeded discussion topics"])
            for item in discussion_topics:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                url = item.get("url")
                target = f"[`{title}`]({url})" if isinstance(url, str) and url else f"`{title}`"
                lines.append(
                    "- "
                    f"{target} -> category `{item.get('categoryName')}`, expected category `{item.get('expectedCategoryName')}`, body matches seed `{item.get('bodyMatchesSeed')}`, pinned `{item.get('actualPinned')}`"
                )

        discussion_action_automation = manual_follow_ups.get("discussionAdminActionAutomation")
        if isinstance(discussion_action_automation, list) and discussion_action_automation:
            lines.extend(["", "## Discussions automation map"])
            for item in discussion_action_automation:
                if not isinstance(item, dict):
                    continue
                kind = item.get("kind")
                target = item.get("target")
                status = item.get("status")
                mutation = item.get("mutation")
                detail = f"- `{kind}` / `{target}` -> `{status}`"
                if isinstance(mutation, str) and mutation:
                    detail += f" via `{mutation}`"
                lines.append(detail)
                reason = item.get("reason")
                if isinstance(reason, str) and reason:
                    lines.append(f"  - reason: {reason}")
                command = item.get("command")
                if isinstance(command, str) and command:
                    lines.append(f"  - command: `{command}`")
                blockers = item.get("blockers")
                if isinstance(blockers, list) and blockers:
                    lines.append("  - blockers: " + ", ".join(f"`{value}`" for value in blockers))
                manual_remainder = item.get("manualRemainder")
                if isinstance(manual_remainder, list) and manual_remainder:
                    lines.append(
                        "  - manual remainder: " + ", ".join(f"`{value}`" for value in manual_remainder)
                    )

        project_board = manual_follow_ups.get("projectBoard")
        if isinstance(project_board, dict):
            lines.extend(["", "## Project board seed targets"])
            if project_board.get("name"):
                lines.append(f"- Board name: `{project_board.get('name')}`")
            if project_board.get("scope"):
                lines.append(f"- Scope: `{project_board.get('scope')}`")
            project_board_error = project_board.get("error")
            if isinstance(project_board_error, str) and project_board_error:
                lines.append(f"- Live verification status: `{project_board_error}`")
            current_auth = project_board.get("currentAuth")
            if isinstance(current_auth, dict):
                auth_login = current_auth.get("login")
                auth_token_source = current_auth.get("tokenSource")
                auth_scopes = current_auth.get("scopes")
                missing_scopes = current_auth.get("missingScopes")
                if isinstance(auth_login, str) and auth_login:
                    if isinstance(auth_token_source, str) and auth_token_source:
                        lines.append(f"- Current GitHub auth account: `{auth_login}` via `{auth_token_source}`")
                    else:
                        lines.append(f"- Current GitHub auth account: `{auth_login}`")
                if isinstance(auth_scopes, list) and auth_scopes:
                    lines.append("- Current GitHub auth scopes: " + ", ".join(f"`{scope}`" for scope in auth_scopes))
                if isinstance(missing_scopes, list) and missing_scopes:
                    lines.append("- Missing project auth scopes: " + ", ".join(f"`{scope}`" for scope in missing_scopes))
            auth_refresh_command = project_board.get("authRefreshCommand")
            if isinstance(auth_refresh_command, str) and auth_refresh_command:
                lines.append(f"- Auth refresh command: `{auth_refresh_command}`")
            commands = project_board.get("commands")
            if isinstance(commands, dict) and commands:
                command_specs = [
                    ("create", "Create command"),
                    ("editDescription", "Description command"),
                    ("linkRepo", "Repo link command"),
                ]
                lines.append("- Seeded commands:")
                for key, label in command_specs:
                    command = commands.get(key)
                    if isinstance(command, str) and command:
                        lines.append(f"  - {label}: `{command}`")
            fields = project_board.get("fields")
            if isinstance(fields, list) and fields:
                lines.append("- Seeded fields:")
                for item in fields:
                    if not isinstance(item, dict):
                        continue
                    detail = f"`{item.get('name')}` ({item.get('kind')})"
                    options = item.get("options")
                    source = item.get("source")
                    if isinstance(options, list) and options:
                        detail += f" -> options `{', '.join(str(option) for option in options)}`"
                    elif source:
                        detail += f" -> source `{source}`"
                    lines.append(f"  - {detail}")
            field_commands = project_board.get("fieldCommands")
            if isinstance(field_commands, list) and field_commands:
                lines.append("- Seeded field commands:")
                for item in field_commands:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name") or item.get("kind") or "field"
                    command = item.get("command")
                    source = item.get("source")
                    if isinstance(command, str) and command:
                        lines.append(f"  - `{name}` -> `{command}`")
                    elif source:
                        lines.append(f"  - `{name}` -> manual source `{source}`")
            views = project_board.get("views")
            if isinstance(views, list) and views:
                lines.append("- Seeded views:")
                for item in views:
                    if not isinstance(item, dict):
                        continue
                    detail = f"`{item.get('name')}` ({item.get('layout')})"
                    group_by = item.get("groupBy")
                    filters = item.get("filters")
                    if group_by:
                        detail += f" -> groupBy `{group_by}`"
                    if isinstance(filters, list) and filters:
                        detail += f" -> filters `{'; '.join(str(value) for value in filters)}`"
                    lines.append(f"  - {detail}")
            notes = project_board.get("notes")
            if isinstance(notes, list) and notes:
                lines.append("- Seed notes:")
                for note in notes:
                    lines.append(f"  - {note}")
            manual_steps = project_board.get("manualSteps")
            if isinstance(manual_steps, list) and manual_steps:
                lines.append("- Manual steps:")
                for step in manual_steps:
                    lines.append(f"  - {step}")
            starter_issue_boarding = project_board.get("starterIssueBoarding")
            if isinstance(starter_issue_boarding, dict):
                lookup_commands = starter_issue_boarding.get("lookupCommands")
                if isinstance(lookup_commands, dict) and lookup_commands:
                    lines.append("- Starter issue project-item lookup commands:")
                    for key, label in [("view", "Project view"), ("fieldList", "Field list")]:
                        command = lookup_commands.get(key)
                        if isinstance(command, str) and command:
                            lines.append(f"  - {label}: `{command}`")
                starter_items = starter_issue_boarding.get("items")
                if isinstance(starter_items, list) and starter_items:
                    lines.append("- Starter issue project-item commands:")
                    for item in starter_items:
                        if not isinstance(item, dict):
                            continue
                        title = item.get("title") or "issue"
                        issue_url = item.get("issueUrl")
                        issue_url_note = issue_url if isinstance(issue_url, str) and issue_url else "<issue-url>"
                        add_command = item.get("addCommand")
                        lines.append(f"  - `{title}` -> add issue `{issue_url_note}` via `{add_command}`")
                        field_assignments = item.get("fieldAssignments")
                        if isinstance(field_assignments, list):
                            for assignment in field_assignments:
                                if not isinstance(assignment, dict):
                                    continue
                                field_name = assignment.get("field") or "field"
                                if assignment.get("command"):
                                    lines.append(
                                        f"    - set `{field_name}` to `{assignment.get('value')}` via `{assignment.get('command')}`"
                                    )
                                elif assignment.get("note"):
                                    lines.append(f"    - `{field_name}`: {assignment.get('note')}")
                starter_notes = starter_issue_boarding.get("notes")
                if isinstance(starter_notes, list) and starter_notes:
                    lines.append("- Starter issue project-item notes:")
                    for note in starter_notes:
                        lines.append(f"  - {note}")

        project_board_actions = manual_follow_ups.get("projectBoardActions")
        if isinstance(project_board_actions, list) and project_board_actions:
            lines.extend(["", "## Project board checklist"])
            for item in project_board_actions:
                if not isinstance(item, dict):
                    continue
                kind = item.get("kind")
                if kind == "requestProjectScope":
                    lines.append("- [ ] Refresh GitHub auth with `read:project` scope (or switch to owner-capable project auth).")
                    command = item.get("command")
                    if isinstance(command, str) and command:
                        lines.append(f"  - command: `{command}`")
                elif kind == "seedProjectBoard":
                    lines.append(
                        "- [ ] "
                        f"Seed or verify public docs project board `{item.get('boardName')}` from "
                        "`docs/ANCAP_DOCS_PROJECT_BOARD_SEED.md` and `.github/bootstrap/ancap-docs-project-board.json`."
                    )
                else:
                    lines.append(f"- [ ] {item.get('instruction')}")

    if snapshot.get("notes"):
        lines.extend(["", "## Notes"])
        lines.extend(f"- {note}" for note in snapshot["notes"])

    return "\n".join(lines) + "\n"


def validate_repo_creation_request(*, apply_changes: bool, create_repo: bool, apply_branch_protection: bool) -> None:
    if create_repo and not apply_changes:
        raise ValueError("--create-repo requires --apply")
    if create_repo and apply_branch_protection:
        raise ValueError(
            "--create-repo cannot be combined with --apply-branch-protection; create/push the initial bundle first, then rerun branch protection"
        )


def validate_live_verification_request(
    *,
    apply_changes: bool,
    verify_live: bool,
    create_repo: bool,
    verify_live_community: bool,
    output_format: str,
) -> None:
    if verify_live_community and not verify_live:
        raise ValueError("--verify-live-community requires --verify-live")
    if output_format == "markdown" and not verify_live:
        raise ValueError("--format markdown currently requires --verify-live")
    if not verify_live:
        return
    if apply_changes:
        raise ValueError("--verify-live cannot be combined with --apply")
    if create_repo:
        raise ValueError("--verify-live cannot be combined with --create-repo")


def validate_branch_protection_request(
    repo_settings: dict[str, Any],
    *,
    apply_changes: bool,
    apply_branch_protection: bool,
    status_check_contexts: list[str],
) -> None:
    if not apply_changes or not apply_branch_protection:
        return

    branch_protection = repo_settings["branchProtection"]
    if branch_protection.get("requireStatusChecks") and not status_check_contexts:
        raise ValueError(
            "branch protection apply requires at least one --status-check-context when the seed requires status checks"
        )


def build_plan_snapshot(
    repo: str,
    plan: dict[str, Any],
    *,
    label_commands: list[list[str]],
    milestone_commands: list[str],
    apply_branch_protection: bool,
    status_check_contexts: list[str],
) -> dict[str, Any]:
    repo_settings = plan["repo_settings"]
    branch_protection = repo_settings["branchProtection"]
    discussions = plan["discussions"]
    project_board = plan["project_board"]
    initial_issues = plan["initial_issues"]
    update_cadence = plan["update_cadence"]
    ci_seed = plan["ci"]
    project_board_setup = build_project_board_setup(repo, plan["project_board"], plan["initial_issues"])

    branch_protection_command: str | None = None
    branch_protection_payload: dict[str, Any] | None = None
    if apply_branch_protection and status_check_contexts:
        status_checks_note = (
            "status checks can be applied after the first public CI workflow exists with these contexts: "
            + ", ".join(status_check_contexts)
        )
        branch_protection_command = format_command(build_branch_protection_command(repo, repo_settings))
        branch_protection_payload = build_branch_protection_payload(repo_settings, status_check_contexts)
    elif apply_branch_protection:
        status_checks_note = (
            "branch protection apply was requested, but status checks are still deferred; pass one or more "
            "--status-check-context values when the public docs repo has stable CI context names."
        )
    else:
        status_checks_note = (
            "status checks are intentionally deferred until the public docs repo has stable CI context names; pass "
            "--apply-branch-protection plus one or more --status-check-context values when those contexts exist."
        )

    return {
        "repo": repo,
        "commands": {
            "repoCreate": format_command(build_repo_create_command(repo, repo_settings)),
            "repoSettings": format_command(build_repo_edit_command(repo, repo_settings)),
            "dependabotAlerts": format_command(build_dependabot_alerts_command(repo)),
            "labels": [format_command(command) for command in label_commands],
            "milestones": milestone_commands,
            "branchProtection": branch_protection_command,
        },
        "repoCreateNotes": build_repo_create_notes(repo_settings),
        "repoSettingsNotes": build_repo_edit_notes(repo_settings),
        "branchProtection": {
            "defaultBranch": repo_settings["defaultBranch"],
            "requirePullRequest": branch_protection["requirePullRequest"],
            "requiredApprovals": branch_protection["requiredApprovals"],
            "dismissStaleApprovals": branch_protection["dismissStaleApprovals"],
            "requireConversationResolution": branch_protection["requireConversationResolution"],
            "requireCodeOwnerReview": branch_protection["requireCodeOwnerReview"],
            "allowForcePushes": branch_protection["allowForcePushes"],
            "allowDeletion": branch_protection["allowDeletion"],
            "statusCheckContexts": status_check_contexts,
            "statusChecksNote": status_checks_note,
            "payload": branch_protection_payload,
        },
        "manualFollowUps": {
            "discussionsCategories": [category["name"] for category in discussions["categories"]],
            "pinnedDiscussionTopics": [topic["title"] for topic in discussions["pinnedTopics"]],
            "discussionsAdminNotes": [
                "The gh/API helper currently verifies Discussions drift and could later automate missing-topic/body/category-reassignment follow-up via createDiscussion/updateDiscussion, but it does not apply those mutations today.",
                "The remaining live gaps still need GitHub UI or a future owner-capable path because the public gh/API surface does not expose full category-description/category-set/pinned-topic admin controls; use docs/ANCAP_DOCS_DISCUSSIONS_SEED.md and .github/bootstrap/ancap-docs-discussions.json as the copy-ready source of truth.",
            ],
            "discussionAutomation": build_discussion_automation_boundary(),
            "projectBoard": {
                "name": project_board["name"],
                "views": [view["name"] for view in project_board["views"]],
                "ownerLogin": project_board_setup["ownerLogin"],
                "projectNumberPlaceholder": project_board_setup["projectNumberPlaceholder"],
                "commands": project_board_setup["commands"],
                "fieldCommands": project_board_setup["fieldCommands"],
                "notes": project_board_setup["notes"],
                "manualSteps": project_board_setup["manualSteps"],
                "starterIssueBoarding": project_board_setup["starterIssueBoarding"],
            },
            "docsCI": {
                "workflowName": ci_seed["workflowName"],
                "targetWorkflowPath": ci_seed["targetWorkflowPath"],
                "jobs": [job["name"] for job in ci_seed["jobs"]],
                "statusCheckContexts": [job["expectedStatusCheckContext"] for job in ci_seed["jobs"]],
            },
            "updateCadence": [item["name"] for item in update_cadence["cadences"]],
            "initialIssuesNote": (
                "Keep the seeded starter backlog explicit via the checked-in gh issue create commands; use them to open the first public queue on a fresh repo, or to recreate/reconcile issues later if live state drifts."
            ),
            "initialIssues": [
                {
                    "title": issue["title"],
                    "milestone": issue["milestone"],
                    "labels": issue["labels"],
                    "boardFields": issue["boardFields"],
                    "command": format_command(build_initial_issue_create_command(repo, issue)),
                    "expectedState": issue.get("expectedState"),
                    "statusNote": issue.get("statusNote"),
                }
                for issue in initial_issues
            ],
            "alignmentNote": (
                "Keep repo settings / labels / milestones / CI seed data aligned with the matching Markdown docs in docs/ "
                "and .github/bootstrap/README.md."
            ),
        },
    }


def render_plan(snapshot: dict[str, Any]) -> str:
    commands = snapshot["commands"]
    branch_protection = snapshot["branchProtection"]
    manual_follow_ups = snapshot["manualFollowUps"]

    lines = [
        f"ANCAP docs bootstrap plan for {snapshot['repo']}",
        "",
        "Repo creation command:",
        f"- {commands['repoCreate']}",
    ]

    repo_create_notes = snapshot["repoCreateNotes"]
    if repo_create_notes:
        lines.extend(["", "Repo creation notes:"])
        lines.extend(f"- {note}" for note in repo_create_notes)

    lines.extend(
        [
            "",
            "Repo settings command:",
            f"- {commands['repoSettings']}",
            f"- {commands['dependabotAlerts']}",
        ]
    )

    repo_settings_notes = snapshot["repoSettingsNotes"]
    if repo_settings_notes:
        lines.extend(["", "Repo settings notes:"])
        lines.extend(f"- {note}" for note in repo_settings_notes)

    lines.extend(["", "Labels:"])
    lines.extend(f"- {command}" for command in commands["labels"])
    lines.extend(["", "Milestones:"])
    lines.extend(f"- {command}" for command in commands["milestones"])

    lines.extend(
        [
            "",
            "Branch protection follow-up:",
            f"- default branch: {branch_protection['defaultBranch']}",
            f"- require pull request before merge: {branch_protection['requirePullRequest']}",
            f"- required approvals: {branch_protection['requiredApprovals']}",
            f"- dismiss stale approvals: {branch_protection['dismissStaleApprovals']}",
            f"- require conversation resolution: {branch_protection['requireConversationResolution']}",
            f"- require CODEOWNERS review: {branch_protection['requireCodeOwnerReview']}",
            f"- allow force pushes: {branch_protection['allowForcePushes']}",
            f"- allow deletion: {branch_protection['allowDeletion']}",
            f"- {branch_protection['statusChecksNote']}",
        ]
    )

    if commands["branchProtection"] and branch_protection["payload"] is not None:
        lines.append(f"- {commands['branchProtection']}")
        lines.append("- branch protection payload:")
        lines.append("```json")
        lines.append(json.dumps(branch_protection["payload"], indent=2))
        lines.append("```")

    lines.extend(
        [
            "",
            "Manual / owner-capability follow-ups still driven by the seeds:",
            f"- Discussions categories: {', '.join(manual_follow_ups['discussionsCategories'])}",
            f"- Pinned discussion topics: {', '.join(manual_follow_ups['pinnedDiscussionTopics'])}",
            f"- Discussions admin note: {manual_follow_ups['discussionsAdminNotes'][0]}",
            f"- Discussions admin note: {manual_follow_ups['discussionsAdminNotes'][1]}",
            f"- Discussion automation confirmed via: {manual_follow_ups['discussionAutomation']['confirmedBy']}",
            f"- Project board: {manual_follow_ups['projectBoard']['name']}",
            f"- Project board views: {', '.join(manual_follow_ups['projectBoard']['views'])}",
            f"- Project board owner: {manual_follow_ups['projectBoard']['ownerLogin']}",
            f"- Project board create command: {manual_follow_ups['projectBoard']['commands']['create']}",
            f"- Project board description command (replace {manual_follow_ups['projectBoard']['projectNumberPlaceholder']}): {manual_follow_ups['projectBoard']['commands']['editDescription']}",
            f"- Project board repo-link command (replace {manual_follow_ups['projectBoard']['projectNumberPlaceholder']}): {manual_follow_ups['projectBoard']['commands']['linkRepo']}",
            f"- Docs CI workflow: {manual_follow_ups['docsCI']['workflowName']} -> {manual_follow_ups['docsCI']['targetWorkflowPath']}",
            f"- Docs CI jobs: {', '.join(manual_follow_ups['docsCI']['jobs'])}",
            f"- Docs CI status-check contexts: {', '.join(manual_follow_ups['docsCI']['statusCheckContexts'])}",
            f"- Update cadence: {', '.join(manual_follow_ups['updateCadence'])}",
            f"- Initial issue backlog note: {manual_follow_ups['initialIssuesNote']}",
        ]
    )

    discussion_automation = manual_follow_ups.get('discussionAutomation')
    if isinstance(discussion_automation, dict):
        supported_mutations = discussion_automation.get('supportedMutations')
        if isinstance(supported_mutations, list) and supported_mutations:
            lines.append("- Discussion GraphQL mutations:")
            for item in supported_mutations:
                if not isinstance(item, dict):
                    continue
                required_fields = ", ".join(item.get('requiredFields', []))
                optional_fields = ", ".join(item.get('optionalFields', []))
                supports = ", ".join(item.get('supports', []))
                lines.append(
                    "  - "
                    f"{item.get('name')} ({item.get('inputType')}) | required={required_fields} | optional={optional_fields} | supports={supports}"
                )
        manual_only_flows = discussion_automation.get('manualOnlyFlows')
        if isinstance(manual_only_flows, list) and manual_only_flows:
            lines.append("- Discussion manual-only flows: " + ", ".join(manual_only_flows))
        split_actions = discussion_automation.get('splitActions')
        if isinstance(split_actions, list) and split_actions:
            lines.append("- Discussion split actions:")
            for item in split_actions:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    "  - "
                    f"{item.get('kind')}: automatable={item.get('automatablePortion')} | manual={item.get('manualPortion')}"
                )

    project_board_field_commands = manual_follow_ups['projectBoard'].get('fieldCommands')
    if isinstance(project_board_field_commands, list) and project_board_field_commands:
        lines.append("- Project board field commands:")
        for field in project_board_field_commands:
            if not isinstance(field, dict):
                continue
            if field.get('command'):
                lines.append(f"  - {field.get('name')} ({field.get('kind')}): {field.get('command')}")
            else:
                detail = field.get('source') or 'manual follow-up required'
                lines.append(f"  - {field.get('name')} ({field.get('kind')}): {detail}")

    project_board_notes = manual_follow_ups['projectBoard'].get('notes')
    if isinstance(project_board_notes, list) and project_board_notes:
        lines.append("- Project board setup notes:")
        lines.extend(f"  - {note}" for note in project_board_notes)

    project_board_manual_steps = manual_follow_ups['projectBoard'].get('manualSteps')
    if isinstance(project_board_manual_steps, list) and project_board_manual_steps:
        lines.append("- Project board manual steps:")
        lines.extend(f"  - {step}" for step in project_board_manual_steps)

    initial_issues = manual_follow_ups.get("initialIssues")
    if isinstance(initial_issues, list) and initial_issues:
        lines.append("- Initial issue backlog commands:")
        for issue in initial_issues:
            if not isinstance(issue, dict):
                continue
            board_fields = issue.get("boardFields")
            board_fields_text = ""
            if isinstance(board_fields, dict) and board_fields:
                board_fields_text = " | board fields=" + ", ".join(
                    f"{key}={value}" for key, value in board_fields.items()
                )
            lines.append(
                "  - "
                f"{issue.get('title')} | milestone={issue.get('milestone')} | "
                f"labels={', '.join(issue.get('labels', []))} | expectedState={issue.get('expectedState')}{board_fields_text}"
            )
            status_note = issue.get("statusNote")
            if isinstance(status_note, str) and status_note:
                lines.append(f"    status note: {status_note}")
            lines.append(f"    command: {issue.get('command')}")

    lines.append(f"- {manual_follow_ups['alignmentNote']}")
    return "\n".join(lines) + "\n"


def emit_output(text: str, *, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply the ANCAP docs repo bootstrap settings/labels/milestones from .github/bootstrap seeds."
    )
    parser.add_argument("--repo", required=True, help="GitHub repository in OWNER/REPO format")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply repo settings, vulnerability alerts, labels, and milestones instead of only printing the plan.",
    )
    parser.add_argument(
        "--apply-branch-protection",
        action="store_true",
        help="Document that branch-protection status checks are ready to be applied once public CI contexts are known.",
    )
    parser.add_argument(
        "--create-repo",
        action="store_true",
        help="When used with --apply, create the public repo before applying repo settings/labels/milestones for the first launch.",
    )
    parser.add_argument(
        "--status-check-context",
        action="append",
        default=[],
        help="Named GitHub status-check context to require later on the default branch.",
    )
    parser.add_argument(
        "--verify-live",
        action="store_true",
        help="Compare the live GitHub repo metadata and default-branch protection against the checked-in seeds.",
    )
    parser.add_argument(
        "--verify-live-community",
        action="store_true",
        help="When used with --verify-live, also compare live labels, milestones, Discussions categories, seeded discussion-topic presence, and pinned-discussion presence against the checked-in seeds.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="Render the bootstrap plan/live verification as plain text, structured JSON, or a markdown checklist (markdown currently requires --verify-live).",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to also write the rendered output as UTF-8. Prefer this over shell redirection on Windows when you need a copy-ready checklist artifact.",
    )
    args = parser.parse_args(argv)

    try:
        args.repo = validate_repo_argument(args.repo)
    except ValueError as exc:
        parser.error(str(exc))

    plan = load_bootstrap_plan()
    repo_edit_command = build_repo_edit_command(args.repo, plan["repo_settings"])
    dependabot_command = build_dependabot_alerts_command(args.repo)
    label_commands = build_label_commands(args.repo, plan["labels"])
    status_check_contexts = _dedupe_status_check_contexts(args.status_check_context) or default_status_check_contexts(plan)

    validate_live_verification_request(
        apply_changes=args.apply,
        verify_live=args.verify_live,
        create_repo=args.create_repo,
        verify_live_community=args.verify_live_community,
        output_format=args.format,
    )
    validate_repo_creation_request(
        apply_changes=args.apply,
        create_repo=args.create_repo,
        apply_branch_protection=args.apply_branch_protection,
    )
    validate_branch_protection_request(
        plan["repo_settings"],
        apply_changes=args.apply,
        apply_branch_protection=args.apply_branch_protection,
        status_check_contexts=status_check_contexts,
    )

    if args.verify_live:
        snapshot = build_live_verification_snapshot(
            args.repo,
            plan,
            repo_state=fetch_live_repo_state(args.repo),
            branch_protection_state=fetch_live_branch_protection_state(
                args.repo,
                plan["repo_settings"]["defaultBranch"],
            ),
            status_check_contexts=status_check_contexts,
            live_labels_state=fetch_live_labels_state(args.repo) if args.verify_live_community else None,
            live_milestones_state=fetch_live_milestones_state(args.repo) if args.verify_live_community else None,
            live_initial_issues_state=fetch_live_initial_issues_state(args.repo) if args.verify_live_community else None,
            live_discussions_state=fetch_live_discussion_categories_state(args.repo) if args.verify_live_community else None,
            project_board_scope_state=fetch_live_project_board_scope_state(args.repo) if args.verify_live_community else None,
        )
        if args.format == "json":
            output = json.dumps(snapshot, indent=2) + "\n"
        elif args.format == "markdown":
            output = render_live_verification_markdown(snapshot)
        else:
            output = render_live_verification(snapshot)
        emit_output(output, output_path=args.output)
        return 0

    if args.apply:
        if args.create_repo:
            run_command(build_repo_create_command(args.repo, plan["repo_settings"]), dry_run=False)
            milestone_commands = ensure_milestones(args.repo, plan["milestones"], dry_run=True)
        else:
            run_command(repo_edit_command, dry_run=False)
            run_command(dependabot_command, dry_run=False)
            for command in label_commands:
                run_command(command, dry_run=False)
            milestone_commands = ensure_milestones(args.repo, plan["milestones"], dry_run=False)
            if args.apply_branch_protection:
                run_command(
                    build_branch_protection_command(args.repo, plan["repo_settings"]),
                    dry_run=False,
                    input_text=json.dumps(
                        build_branch_protection_payload(plan["repo_settings"], status_check_contexts),
                        indent=2,
                    ),
                )
    else:
        milestone_commands = ensure_milestones(args.repo, plan["milestones"], dry_run=True)

    snapshot = build_plan_snapshot(
        args.repo,
        plan,
        label_commands=label_commands,
        milestone_commands=milestone_commands,
        apply_branch_protection=args.apply_branch_protection,
        status_check_contexts=status_check_contexts,
    )
    if args.format == "json":
        output = json.dumps(snapshot, indent=2) + "\n"
    else:
        output = render_plan(snapshot)
    emit_output(output, output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
