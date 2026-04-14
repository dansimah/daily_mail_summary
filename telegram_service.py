import requests
from datetime import datetime


def send_message(bot_token, chat_id, text):
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")


def build_package_line(subject, tracking_number, courier, summary):
    package_line = f"📦 <b>{subject}</b>\nTracking: <code>{tracking_number}</code>"
    if courier:
        package_line += f"\nCourier: {courier}"
    package_line += f"\n{summary}"
    return package_line


def build_daily_report(processing_count, total_unread, label_counts, daily_summaries, package_summaries):
    report = "📊 <b>Daily Email Stats</b>\n"
    report += f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Total Last 24h Inbox Mails: {processing_count}\n"
    report += f"Initially Unread: {total_unread}\n"

    report += "\n<b>Categories Processed:</b>\n"
    for label, count in label_counts.items():
        report += f"• {label}: {count}\n"

    report += "\n-----------------------\n\n"
    if daily_summaries:
        report += "📬 <b>Important Emails:</b>\n\n" + "\n\n".join(daily_summaries)
    else:
        report += "📭 <b>Important Emails:</b> None today!"

    report += "\n\n-----------------------\n\n"
    if package_summaries:
        report += "📦 <b>Packages Detected:</b>\n\n" + "\n\n".join(package_summaries)
    else:
        report += "📦 <b>Packages Detected:</b> None today."

    return report
