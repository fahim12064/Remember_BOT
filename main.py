import os
import json
import requests
import time

# --- Configuration ---
USER_IDS_FILE = "user_ids.json"
# আপনার টেলিগ্রাম বটের টোকেন এখানে দিন অথবা এনভায়রনমেন্ট ভ্যারিয়েবল হিসেবে সেট করুন
TELEGRAM_BOT_TOKEN = os.getenv("YOUR_TELEGRAM_BOT_TOKEN", "এখানে_আপনার_টোকেন_দিন")


# --- Utility Functions ---

def load_user_ids():
    """user_ids.json ফাইল থেকে ব্যবহারকারীদের Chat ID লোড করে।"""
    if not os.path.exists(USER_IDS_FILE):
        return set()
    try:
        with open(USER_IDS_FILE, "r") as f:
            content = f.read()
            if not content:
                return set()
            return set(json.loads(content))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_user_ids(user_ids):
    """ব্যবহারকারীদের Chat ID সেভ করে user_ids.json ফাইলে।"""
    with open(USER_IDS_FILE, "w") as f:
        json.dump(list(user_ids), f, indent=2)


def handle_new_users():
    """নতুন ব্যবহারকারীদের /start কমান্ড হ্যান্ডেল করে এবং তাদের রেজিস্টার করে।"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Telegram Bot Token is not set.")
        return

    # শেষ update_id ট্র্যাক করার জন্য একটি ফাইল
    last_update_file = "last_update_id.txt"
    last_update_id = 0
    if os.path.exists(last_update_file):
        with open(last_update_file, "r") as f:
            try:
                last_update_id = int(f.read().strip())
            except ValueError:
                last_update_id = 0

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=5"

    try:
        response = requests.get(url, timeout=10)
        updates = response.json().get("result", [])

        if not updates:
            return  # কোনো নতুন মেসেজ নেই

        user_ids = load_user_ids()
        new_users_found = False

        for update in updates:
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]
                first_name = update["message"]["from"].get("first_name", "User")

                if text == "/start":
                    if chat_id not in user_ids:
                        user_ids.add(chat_id)
                        new_users_found = True
                        print(f"✅ New user registered: {chat_id} ({first_name})")

                        # নতুন ব্যবহারকারীকে স্বাগত বার্তা
                        welcome_message = f"Welcome, {first_name}! I will now remind you to study every 2 minutes."
                        send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                        payload = {"chat_id": chat_id, "text": welcome_message}
                        requests.post(send_url, json=payload, timeout=10)

            last_update_id = update["update_id"]

        if new_users_found:
            save_user_ids(user_ids)

        with open(last_update_file, "w") as f:
            f.write(str(last_update_id))

    except Exception as e:
        print(f"❌ Error checking Telegram updates: {e}")


def send_reminders():
    """সকল রেজিস্টার্ড ব্যবহারকারীকে রিমাইন্ডার পাঠায়।"""
    user_ids = load_user_ids()
    if not user_ids:
        print("🤷 No users to remind.")
        return

    print(f"✉️ Sending reminders to {len(user_ids)} user(s)...")
    message = "GO and STUDY"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for chat_id in user_ids:
        try:
            payload = {"chat_id": chat_id, "text": message}
            requests.post(url, json=payload, timeout=10)
            print(f"    ✅ Reminder sent to {chat_id}")
        except Exception as e:
            print(f"    ❌ Failed to send reminder to {chat_id}: {e}")
        time.sleep(1)  # রেট লিমিটিং এড়ানোর জন্য ১ সেকেন্ড বিরতি


# --- Main Loop ---
if __name__ == "__main__":
    print("--- Study Buddy Bot Started ---")
    while True:
        print("\n--- Running Cycle ---")
        # ধাপ ১: নতুন ব্যবহারকারী চেক ও রেজিস্টার করা
        print("STEP 1: Checking for new users...")
        handle_new_users()

        # ধাপ ২: সকল ব্যবহারকারীকে রিমাইন্ডার পাঠানো
        print("\nSTEP 2: Sending reminders...")
        send_reminders()

        # ধাপ ৩: ২ মিনিট অপেক্ষা করা
        print("\n--- Cycle complete. Waiting for 2 minutes... ---")
        time.sleep(120)

