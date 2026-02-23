import os
import time
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright, TimeoutError

# Environment variables (set these in Railway → Variables)
USERNAME = os.getenv("SMARTFIND_USERNAME")
PASSWORD = os.getenv("SMARTFIND_PASSWORD")
EMAILNAME = os.getenv("EMAILNAME")
EMAILPASS = os.getenv("EMAILPASS")

LOGIN_URL = "https://hrsubsfresnounified.eschoolsolutions.com/logOnInitAction.do"


def send_email():
    try:
        msg = EmailMessage()
        msg["Subject"] = "🚨 Jobs Available on SmartFind"
        msg["From"] = EMAILNAME
        msg["To"] = EMAILNAME  # send to yourself

        msg.set_content("Jobs are available on SmartFind. Log in immediately.")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAILNAME, EMAILPASS)
            smtp.send_message(msg)

        print("📧 Email sent successfully.")

    except Exception as e:
        print(f"Email error: {e}")


def check_for_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🔐 Logging in...")

        page.goto(LOGIN_URL)

        page.fill("#userId", USERNAME)
        page.fill("#userPin", PASSWORD)
        page.click("#submitBtn")

        # Wait for dashboard
        page.wait_for_selector("#available-tab", timeout=60000)

        page.click("#available-tab")
        page.wait_for_selector("#available-panel.pds-is-active", timeout=60000)

        print("📋 Waiting for jobs state...")

        try:
            page.wait_for_function(
                """
                () => {
                    const panel = document.querySelector('#available-panel');
                    if (!panel) return false;

                    const noJobs = panel
                        .querySelector('.pds-message-info')
                        ?.innerText
                        .toLowerCase()
                        .includes('no jobs');

                    const hasRows = panel
                        .querySelector('#parent-table-desktop-available tbody')
                        ?.querySelectorAll('tr').length > 0;

                    return noJobs || hasRows;
                }
                """,
                timeout=60000
            )
        except TimeoutError:
            print("⏱ Timed out waiting for jobs state.")
            browser.close()
            return

        no_jobs_locator = page.locator("#available-panel .pds-message-info")

        if no_jobs_locator.count() > 0 and \
           "no jobs" in no_jobs_locator.first.inner_text().lower():
            print("❌ No jobs available.")
        else:
            print("✅ Jobs available!")
            send_email()

        browser.close()


# Continuous loop for Railway
print("🚀 SmartFind Railway Bot Started")

while True:
    try:
        check_for_jobs()
    except Exception as e:
        print(f"Unexpected error: {e}")

    print("⏳ Sleeping 120 seconds...\n")
    time.sleep(120)