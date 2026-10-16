import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests

# ====== CONFIGURATION ======
TOKEN = '8893946869:AAFkq4ZzNygJ14HFUTVkOkMuUlBz0oaEMto'
ADMIN_CHAT_ID = 8858060392
DB_URL = 'https://itz-my-site-default-rtdb.asia-southeast1.firebasedatabase.app'

bot = telebot.TeleBot(TOKEN)

# Main Menu Keyboard
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton('📊 Site Stats'), KeyboardButton('⚙️ Settings'))
    markup.row(KeyboardButton('👥 Latest Users'), KeyboardButton('💬 Recent Comments'))
    markup.row(KeyboardButton('⚠️ Reset Tools'))
    return markup

def is_admin(message):
    return message.chat.id == ADMIN_CHAT_ID

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔ Unauthorized access.")
        return
    bot.send_message(message.chat.id, "🚀 *System Online!*\nWelcome to the RK-SYSTEM Python Admin Control Panel.", parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_admin(message):
        return

    text = message.text

    try:
        if text == '📊 Site Stats':
            res = requests.get(f"{DB_URL}/stats.json").json() or {}
            
            stat_msg = (
                "📊 *LIVE SITE STATISTICS*\n━━━━━━━━━━━━━━━━━━\n"
                f"👥 *Today Joined:* {res.get('todayJoined', 0)}\n"
                f"📈 *Total Joined:* {res.get('totalJoined', 0)}\n"
                f"🌐 *Total Site Visits:* {res.get('totalVisitor', 0)}\n"
                f"🖱️ *Total Ad Clicks:* {res.get('todayAdsClick', 0)}\n━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(ADMIN_CHAT_ID, stat_msg, parse_mode='Markdown')

        elif text == '⚙️ Settings':
            send_settings_menu()

        elif text == '👥 Latest Users':
            res = requests.get(f"{DB_URL}/users.json").json()
            if not res:
                bot.send_message(ADMIN_CHAT_ID, "No users found in database.")
                return
            
            users = list(res.values())
            latest = users[-5:]
            latest.reverse()
            
            u_msg = "👥 *LAST 5 USERS*\n━━━━━━━━━━━━━━━━━━\n"
            for i, u in enumerate(latest):
                u_msg += (
                    f"{i+1}. *ID:* {u.get('id', 'N/A')}\n"
                    f"   ▪️ *Status:* {u.get('status', 'Unknown')}\n"
                    f"   ▪️ *IP:* {u.get('ip', 'Hidden')}\n"
                    f"   ▪️ *Loc:* {u.get('city', '')}, {u.get('country', '')}\n"
                    f"   ▪️ *Visits:* {u.get('visits', 1)}\n"
                    f"   ▪️ *Active:* {u.get('lastActive', '')}\n━━━━━━━━━━━━━━━━━━\n"
                )
            bot.send_message(ADMIN_CHAT_ID, u_msg, parse_mode='Markdown')

        elif text == '💬 Recent Comments':
            res = requests.get(f"{DB_URL}/comments.json").json()
            if not res:
                bot.send_message(ADMIN_CHAT_ID, "No comments found.")
                return
            
            comments = list(res.values())
            latest = comments[-5:]
            latest.reverse()
            
            c_msg = "💬 *LATEST COMMENTS*\n━━━━━━━━━━━━━━━━━━\n"
            for c in latest:
                c_msg += (
                    f"👤 *User:* {c.get('userKey', 'Unknown')[:8]}\n"
                    f"🕒 *Time:* {c.get('time', '')}\n"
                    f"💬 *Text:* \"{c.get('text', '')}\"\n━━━━━━━━━━━━━━━━━━\n"
                )
            bot.send_message(ADMIN_CHAT_ID, c_msg, parse_mode='Markdown')

        elif text == '⚠️ Reset Tools':
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton('🔄 Reset Ad Clicks', callback_data='reset_clicks'))
            markup.row(InlineKeyboardButton('👥 Reset Visitors', callback_data='reset_visitors'))
            markup.row(InlineKeyboardButton('🗑️ Clear All Users', callback_data='clear_users'))
            
            bot.send_message(ADMIN_CHAT_ID, "⚠️ *Database Reset Tools*\n_Select an option to reset data. Actions are irreversible!_", parse_mode='Markdown', reply_markup=markup)

    except Exception as e:
        bot.send_message(ADMIN_CHAT_ID, f"❌ Error: {str(e)}")

def send_settings_menu(message_id=None):
    ad_res = requests.get(f"{DB_URL}/settings/adsEnabled.json").json()
    ads_enabled = True if ad_res is None else ad_res

    prot_res = requests.get(f"{DB_URL}/settings/siteProtect.json").json() or {}
    site_lock = prot_res.get('enabled', False)

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f"Ads: {'🟢 ON' if ads_enabled else '🔴 OFF'}", callback_data='toggle_ads'))
    markup.row(InlineKeyboardButton(f"Site Lock: {'🔒 ON' if site_lock else '🔓 OFF'}", callback_data='toggle_lock'))

    if message_id:
        bot.edit_message_reply_markup(chat_id=ADMIN_CHAT_ID, message_id=message_id, reply_markup=markup)
    else:
        bot.send_message(ADMIN_CHAT_ID, "⚙️ *Control Panel Settings*", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    try:
        if call.data == 'toggle_ads':
            current = requests.get(f"{DB_URL}/settings/adsEnabled.json").json()
            new_state = False if current else True
            requests.put(f"{DB_URL}/settings/adsEnabled.json", json=new_state)
            bot.answer_callback_query(call.id, f"Ads turned {'ON' if new_state else 'OFF'}")
            send_settings_menu(call.message.message_id)

        elif call.data == 'toggle_lock':
            prot_data = requests.get(f"{DB_URL}/settings/siteProtect.json").json() or {"enabled": False, "password": "1234"}
            prot_data['enabled'] = not prot_data.get('enabled', False)
            requests.put(f"{DB_URL}/settings/siteProtect.json", json=prot_data)
            bot.answer_callback_query(call.id, f"Site Lock turned {'ON' if prot_data['enabled'] else 'OFF'}")
            send_settings_menu(call.message.message_id)

        elif call.data == 'reset_clicks':
            requests.put(f"{DB_URL}/stats/todayAdsClick.json", json=0)
            bot.answer_callback_query(call.id, "Ad Clicks Reset to 0!", show_alert=True)

        elif call.data == 'reset_visitors':
            requests.put(f"{DB_URL}/stats/totalVisitor.json", json=0)
            bot.answer_callback_query(call.id, "Total Visitors Reset to 0!", show_alert=True)

        elif call.data == 'clear_users':
            requests.delete(f"{DB_URL}/users.json")
            bot.answer_callback_query(call.id, "All Tracked Users Deleted!", show_alert=True)

    except Exception as e:
        bot.answer_callback_query(call.id, "Error executing command.")

# Notify admin that bot has started
try:
    bot.send_message(ADMIN_CHAT_ID, "🚀 *Python Admin Bot is Online!*\nBackground monitoring active.", parse_mode="Markdown", reply_markup=main_menu())
except:
    pass

# Start polling
print("Bot is running...")
bot.infinity_polling()
