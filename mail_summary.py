import json
from config import (
    CATEGORY_LABELS,
    INBOX_QUERY,
    OLLAMA_MODEL,
    OLLAMA_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    ensure_required_settings,
)
from gmail_service import (
    apply_label_if_available,
    authenticate,
    ensure_category_labels_exist,
    fetch_messages,
    fetch_unread_ids,
    restore_unread_if_needed,
)
from llm_service import analyze_email
from logging_utils import log
from models import EmailProcessingResult
from telegram_service import build_daily_report, build_package_line, send_message


def main():
    log("=== STARTING DAILY EMAIL AGENT ===")
    try:
        ensure_required_settings()
    except RuntimeError as error:
        log(f"CRITICAL ERROR: {error}")
        return

    try:
        log("Authenticating with Gmail API...")
        gmail = authenticate()
        log("Authentication successful.")
    except Exception as e:
        log(f"CRITICAL ERROR: Could not connect to Gmail. {e}")
        return

    log("Fetching Gmail label IDs...")
    try:
        label_map = ensure_category_labels_exist(gmail, CATEGORY_LABELS, log)
    except Exception as e:
        log(f"Warning: Could not fetch labels. {e}")
        label_map = {}

    date_query = INBOX_QUERY

    log("Fetching last 24h unread messages (for state restoration)...")
    unread_ids = fetch_unread_ids(gmail, date_query)
    total_unread = len(unread_ids)
    
    log("Fetching all last 24h inbox messages (read + unread)...")
    messages_to_process = fetch_messages(gmail, date_query)
    processing_count = len(messages_to_process)
    daily_summaries = []
    package_summaries = []
    label_counts = {}

    if processing_count == 0:
        log("No emails found in last 24h. Sending empty digest.")
        report = build_daily_report(
            processing_count,
            total_unread,
            label_counts,
            daily_summaries,
            package_summaries,
        )
        try:
            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, report)
            log("Empty digest sent successfully.")
        except Exception as e:
            log(f"CRITICAL ERROR: Failed to send empty digest. {e}")
        return

    log(f"Found {processing_count} inbox emails in last 24h ({total_unread} started unread).")
    
    processed_results = []

    log(f"Beginning processing for {processing_count} emails...")

    for index, msg in enumerate(messages_to_process, start=1):
        was_unread = msg.id in unread_ids
        subject = msg.subject or "(No Subject)"
        body = msg.plain[:3000] if msg.plain else ""
        
        log(f"--- [Email {index}/{processing_count}] ---")
        log(f"Subject: {subject}")
        
        try:
            log("Sending to Ollama for analysis...")
            run_result = analyze_email(
                OLLAMA_URL,
                OLLAMA_MODEL,
                subject,
                body,
                CATEGORY_LABELS,
            )
            log(f"Ollama responded in {run_result.elapsed_seconds:.1f} seconds.")
            analysis = run_result.analysis
            log(f"Parsed JSON successfully. Label: {analysis.label}, Important: {analysis.important}")
            result = EmailProcessingResult(label=analysis.label)

            label_counts[analysis.label] = label_counts.get(analysis.label, 0) + 1

            apply_label_if_available(msg, analysis.label, label_map, log)

            if analysis.important:
                result.important_summary = f"📌 <b>{subject}</b>\n{analysis.summary}"
                daily_summaries.append(result.important_summary)
                msg.star()
                log("Marked email as Important (Starred).") 

            if analysis.tracking_number:
                package_line = build_package_line(
                    subject,
                    analysis.tracking_number,
                    analysis.courier,
                    analysis.summary,
                )
                result.package_summary = package_line
                package_summaries.append(package_line)

                try:
                    send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, "🚚 <b>Package Alert</b>\n\n" + package_line)
                    log("Sent package-specific Telegram alert.")
                except Exception as e:
                    log(f"ERROR: Failed to send package alert. {e}")

            processed_results.append(result)
        except json.JSONDecodeError:
            log("ERROR: Ollama did not return valid JSON. Skipping categorization.")
        except Exception as e:
            log(f"ERROR processing email: {e}")

        restore_unread_if_needed(msg, was_unread, log)

    log("=== PROCESSING COMPLETE ===")
    log("Constructing Telegram Digest...")
    
    report = build_daily_report(
        processing_count,
        total_unread,
        label_counts,
        daily_summaries,
        package_summaries,
    )

    try:
        log("Sending daily digest to Telegram API...")
        send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, report)
        log("Telegram digest sent successfully!")
    except Exception as e:
        log(f"CRITICAL ERROR: Failed to send Telegram message. {e}")
        
    log("=== AGENT SHUTTING DOWN CLEANLY ===")


if __name__ == "__main__":
    main()