from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, update

from app.db.models import NotificationEvent, User
from app.config import get_settings
from app.services.mail import can_receive_system_email, send_email
from app.services.pubsub import publish_notification_event


async def notifications_fanout_tick(session: AsyncSession, *, max_events: int = 500) -> dict:
    """Process unprocessed notifications and fan out to email + Redis pub/sub.

    Email is sent for high-priority notifications where the user has opted in.
    Redis pub/sub broadcasts all processed events so any connected client can receive them.
    """
    get_settings()
    processed = 0
    email_sent = 0
    redis_published = 0
    errors = 0

    result = await session.execute(
        select(NotificationEvent)
        .where(NotificationEvent.is_read == False)
        .order_by(desc(NotificationEvent.created_at))
        .limit(max_events)
    )
    notifications: list[NotificationEvent] = list(result.scalars().all())

    for notif in notifications:
        try:
            # Resolve user email for email fanout
            if notif.recipient_user_id:
                user_result = await session.execute(
                    select(User.email).where(User.id == notif.recipient_user_id)
                )
                user_email = user_result.scalar_one_or_none()

                if user_email and can_receive_system_email(user_email):
                    subject, text_body, html_body = _build_notification_email(
                        notif.type, notif.payload_json or {}, notif.priority
                    )
                    if subject and send_email(
                        to_email=user_email,
                        subject=subject,
                        text_body=text_body,
                        html_body=html_body,
                    ):
                        email_sent += 1

            # Publish to Redis pub/sub for real-time in-app delivery
            pub_result = await publish_notification_event(
                notification_id=notif.id,
                notification_type=notif.type,
                recipient_user_id=notif.recipient_user_id,
                recipient_agent_id=notif.recipient_agent_id,
            )
            if pub_result:
                redis_published += 1

            # Mark as read
            await session.execute(
                update(NotificationEvent)
                .where(NotificationEvent.id == notif.id)
                .values(is_read=True, read_at=datetime.now(timezone.utc))
            )
            processed += 1

        except Exception:
            errors += 1

    await session.commit()
    return {
        "processed": processed,
        "email_sent": email_sent,
        "redis_published": redis_published,
        "errors": errors,
        "max_events": max_events,
    }


def _build_notification_email(notif_type: str, payload: dict, priority: str) -> tuple[str | None, str, str]:
    """Build email subject/body from notification type and payload. Returns (subject, text, html)."""
    base_url = get_settings().public_app_url.rstrip("/")
    title = payload.get("title", "ANCAP Notification")
    run_id = payload.get("workflow_run_id", "")

    if notif_type == "workflow.completed":
        subject = f"ANCAP: {title} — completed"
        text = (
            f"Your ANCAP workflow run is complete.\n\n"
            f"Workflow: {title}\n"
            f"Run: {run_id}\n"
            f"Proof: {base_url}/proof-center?run={run_id}\n"
        )
        html = (
            f"<p>Your ANCAP workflow run is complete.</p>"
            f"<p><strong>Workflow:</strong> {title}</p>"
            f"<p><strong>Run:</strong> {run_id}</p>"
            f"<p><a href=\"{base_url}/proof-center?run={run_id}\">Open proof receipt</a></p>"
        )
        return subject, text, html

    if notif_type == "workflow.failed":
        subject = f"ANCAP: {title} — failed"
        text = f"Your ANCAP workflow run failed.\n\nWorkflow: {title}\nRun: {run_id}\n"
        html = f"<p>Your ANCAP workflow run failed.</p><p><strong>Workflow:</strong> {title}</p>"
        return subject, text, html

    if notif_type == "workflow.payment_confirmed":
        subject = f"ANCAP: Payment confirmed for {title}"
        text = f"Payment confirmed. Your workflow run is being prepared.\n\nWorkflow: {title}"
        html = f"<p>Payment confirmed. Your workflow run is being prepared.</p><p><strong>{title}</strong></p>"
        return subject, text, html

    if notif_type == "payment.low_balance":
        subject = "ANCAP: Low ACP balance"
        text = "Your ACP balance is low. Please top up to continue using paid workflows."
        html = "<p>Your ACP balance is low. Please <a href=\"{}/wallet\">top up your wallet</a> to continue.</p>".format(base_url)
        return subject, text, html

    if notif_type == "governance.proposal":
        subject = f"ANCAP: New governance proposal — {title}"
        text = f"A new governance proposal is open for voting.\n\n{title}"
        html = f"<p>A new governance proposal is open for voting.</p><p><strong>{title}</strong></p>"
        return subject, text, html

    if notif_type == "referral.reward":
        amount = payload.get("amount", "N/A")
        subject = f"ANCAP: You earned {amount} ACP from referrals!"
        text = f"Congratulations! You earned {amount} ACP from referral rewards.\n"
        html = f"<p>Congratulations! You earned {amount} ACP from referral rewards.</p>"
        return subject, text, html

    # Generic fallback
    subject = f"ANCAP: {title}"
    text = f"You have a new notification from ANCAP.\n\n{title}"
    html = f"<p>You have a new notification from ANCAP.</p><p>{title}</p>"
    return subject, text, html

