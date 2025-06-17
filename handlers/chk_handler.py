import html
import requests
import telebot

def check_card(card):
    """Check a single card using xchecker.cc API"""
    try:
        parts = card.strip().split('|')
        if len(parts) != 4:
            return "❌ Invalid card format. Use cc|mm|yy|cvv"

        cc, mm, yy, cvv = parts
        if len(yy) == 4:
            yy = yy[-2:]

        url = f"https://xchecker.cc/api.php?cc={cc}|{mm}|{yy}|{cvv}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "error" in data:
            return f"❌ {data['error']}"
        else:
            status = data.get("status", "Unknown")
            details = data.get("details", "")

            # Filter out donation lines
            filtered_lines = []
            for line in details.strip().splitlines():
                if "donation" not in line.lower() and "bc1q" not in line.lower():
                    filtered_lines.append(line)
            cleaned_details = "\n".join(filtered_lines)

            # Beautified emojis
            if "live" in status.lower():
                status_emoji = "🟢✅"
            elif "dead" in status.lower() or "declined" in cleaned_details.lower():
                status_emoji = "🔴❌"
            else:
                status_emoji = "⚠️❓"

            return (
                f"{status_emoji} <b>Status:</b> <code>{html.escape(status)}</code>\n"
                f"ℹ️ {html.escape(cleaned_details)}"
            )
    except Exception as e:
        return f"⚠️ Error checking card: {str(e)}"

def register(bot):
    @bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(('/chk', '.chk')))
    def handle_chk(message):
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Provide a card to check. Format: `cc|mm|yy|cvv`", parse_mode="Markdown")
            return

        card = parts[1].strip()
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        sent_msg = bot.reply_to(message, f"🔄 Checking <code>{card}</code>...", parse_mode="HTML")

        status = check_card(card)

        try:
            bot.edit_message_text(
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                text=f"<code>{card}</code>\n{status}\n\n👤 Checked by: {username}",
                parse_mode="HTML"
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Failed to edit message: {str(e)}")


    @bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(('/mas', '.mas')))
    def handle_mass_chk(message):
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Please reply to a message containing cards.")
            return

        lines = message.reply_to_message.text.strip().split('\n')
        cards = [line.strip() for line in lines if '|' in line and line.count('|') == 3]

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the replied message.")
            return

        if len(cards) > 10:
            bot.reply_to(message, f"⚠️ Limit exceeded: You can check a maximum of 10 cards at once. You provided {len(cards)}.")
            return

        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        sent_msg = bot.reply_to(message, f"🔄 Checking {len(cards)} cards...", parse_mode="HTML")

        results = []
        for card in cards:
            status = check_card(card)
            results.append(f"<code>{card}</code>\n{status}")

        reply_text = "\n\n".join(results) + f"\n\n👤 Checked by: {username}"

        if len(reply_text) > 4000:
            reply_text = reply_text[:3900] + "\n\n⚠️ Output trimmed..."

        try:
            bot.edit_message_text(
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                text=reply_text.strip(),
                parse_mode="HTML"
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Failed to edit message: {str(e)}")
