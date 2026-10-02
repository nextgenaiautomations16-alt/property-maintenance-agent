"""
Posts to Slack only when the orchestrator has decided a human genuinely
needs to be involved -- critical safety cases, or a dispatch that didn't
get confirmed. Routine and high-urgency-but-handled cases never page
anyone; the whole point of the agent is that most cases resolve without
a human touching them at all.
"""
import os
import requests

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def send_escalation_alert(case, reason: str) -> bool:
    property_info_line = f"{case.property_id} / Unit {case.unit_id}"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🚨 Maintenance case escalated — {case.tenant_name} ({case.case_id})"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Property:*\n{property_info_line}"},
                {"type": "mrkdwn", "text": f"*Urgency:*\n{case.urgency} ({case.triage_source})"},
            ]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Tenant message:*\n\"{case.raw_message}\""}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Why this needs a human:*\n{reason}"}
        },
    ]

    payload = {"text": f"Maintenance case escalated: {case.case_id}", "blocks": blocks}

    if not SLACK_WEBHOOK_URL:
        print("[notifications] SLACK_WEBHOOK_URL not set — logging alert instead of sending:")
        print(reason)
        return True

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[notifications] Failed to send Slack alert: {e}")
        return False
