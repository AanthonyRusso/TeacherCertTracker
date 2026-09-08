import smtplib
import configparser

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

REMINDER_MESSAGES = {
    "3_month": "This is a reminder that your certification is due in approximately 3 months.",
    "1_month": "This is a reminder that your certification is due in approximately 1 month.",
    "1_week": "This is a reminder that your certification is due in approximately 1 week.",
    "2_week_after": "Your certification due date has passed by about 2 weeks. Please renew as soon as possible.",
}


def _load_credentials(config_path="config.ini"):
    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        email = config["smtp"]["email"]
        password = config["smtp"]["password"]
    except KeyError as e:
        raise RuntimeError(f"Missing SMTP config value: {e}. Check {config_path}")

    return email, password


def send_reminder_emails(teacher_email, time_frame, config_path="config.ini"):
    sender_email, sender_password = _load_credentials(config_path)

    print(repr(sender_email), repr(sender_password))

    body = REMINDER_MESSAGES.get(
        time_frame,
        "This is a reminder regarding your certification status."
    )

    subject = "Certification Reminder"
    message = f"Subject: {subject}\n\n{body}"

    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, teacher_email, message)
    server.quit()


if __name__ == "__main__":
    send_reminder_emails("tony_russo@stpiuselementary.org", "1_month")