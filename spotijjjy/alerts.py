"""
Best-effort operational alerting for Spotijjjy.

The only thing worth waking you up for is "the refresh token died and the playlists
stopped updating". When that happens we publish a short message to an AWS SNS topic,
which fans out to whatever you subscribed (email is the easy, always-free option).

Design goals:
* Free: SNS email is within the AWS always-free usage for this volume (a handful of
  alerts per year). No extra infrastructure beyond one topic + one subscription.
* Safe: alerting must NEVER mask the original problem. Every failure here is swallowed
  and logged, so a misconfigured/missing topic can't crash the playlist job.
* Opt-in: if ``ALERT_SNS_TOPIC_ARN`` is not set, alerting is silently skipped.
"""
import logging
import os

logger = logging.getLogger("spotijjjy.alerts")

ALERT_TOPIC_ENV = "ALERT_SNS_TOPIC_ARN"


def send_alert(subject, message):
    """
    Publish an alert to the configured SNS topic. Best-effort: returns True on success,
    False otherwise, and never raises.

    The topic ARN is read from the ``ALERT_SNS_TOPIC_ARN`` environment variable. If it is
    not set, the alert is skipped (returns False). No secrets are included in the payload.
    """
    topic_arn = os.environ.get(ALERT_TOPIC_ENV)
    if not topic_arn:
        logger.info("%s not set - skipping alert: %s", ALERT_TOPIC_ENV, subject)
        return False

    try:
        import boto3
        # SNS subject must be <= 100 chars and ASCII.
        safe_subject = (subject or "Spotijjjy alert")[:100]
        boto3.client("sns").publish(
            TopicArn=topic_arn,
            Subject=safe_subject,
            Message=message,
        )
        logger.info("Published alert to SNS topic.")
        return True
    except Exception:
        # Alerting is best-effort; do not let it break the caller.
        logger.exception("Failed to publish SNS alert (continuing).")
        return False
