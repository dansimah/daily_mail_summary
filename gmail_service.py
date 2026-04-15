from simplegmail import Gmail


def authenticate(client_secret_file, token_file):
    return Gmail(client_secret_file=client_secret_file, creds_file=token_file)


def fetch_label_map(gmail):
    existing_labels = gmail.list_labels()
    return {label.name.lower(): label for label in existing_labels}


def ensure_category_labels_exist(gmail, category_labels, logger):
    label_map = fetch_label_map(gmail)
    created_count = 0

    for desired_label in category_labels:
        if desired_label.lower() in label_map:
            continue
        try:
            gmail.create_label(desired_label)
            created_count += 1
            logger(f"Created missing Gmail label: '{desired_label}'")
        except Exception as error:
            logger(f"Warning: Could not create label '{desired_label}'. {error}")

    if created_count > 0:
        return fetch_label_map(gmail)

    return label_map


def fetch_unread_ids(gmail, query):
    unread_messages = gmail.get_messages(query=f"is:unread {query}")
    return {message.id for message in unread_messages}


def fetch_messages(gmail, query):
    return gmail.get_messages(query=query)


def apply_label_if_available(message, label_name, label_map, logger):
    if label_name == "Uncategorized":
        return

    target_label = label_map.get(label_name.lower())
    if not target_label:
        logger(f"Notice: Label '{label_name}' not found in Gmail. Skipping.")
        return

    try:
        message.add_label(target_label)
        logger(f"Successfully applied Gmail label: '{target_label.name}'")
    except Exception as error:
        logger(f"Error applying label '{label_name}': {error}")


def restore_unread_if_needed(message, was_unread, logger):
    if not was_unread:
        return

    try:
        message.mark_as_unread()
        logger("Restored originally unread email back to Unread.")
    except Exception as error:
        logger(f"Warning: Failed to restore unread state. {error}")
