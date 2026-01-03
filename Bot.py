import telebot
from telebot import types
import sqlite3

# --- CONFIGURATION ---
API_TOKEN = '8387557873:AAGmiQkmKwxdaz7WGbFAzG4vsH7CqT6OVJk'
ADMIN_ID = 6267675097 
BKASH_NUMBER = "01815243007" 
bot = telebot.TeleBot(API_TOKEN)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('proxy_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS proxies (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def get_balance(user_id):
    conn = sqlite3.connect('proxy_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect('proxy_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# --- MAIN KEYBOARD ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🚀 Buy Proxy (1 TK)")
    btn2 = types.KeyboardButton("💰 My Balance")
    btn3 = types.KeyboardButton("➕ Deposit")
    btn4 = types.KeyboardButton("📞 Support")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# --- BOT COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        f"👋 আসসালামু আলাইকুম {message.from_user.first_name}!\n\n"
        "আমাদের অটোমেটেড প্রক্সি শপে আপনাকে স্বাগতম।\n"
        "এখানে আপনি সাশ্রয়ী মূল্যে হাই-কোয়ালিটি প্রক্সি পাবেন।\n\n"
        "🔹 **রেট:** ১ টাকা / প্রক্সি"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    uid = message.from_user.id
    
    if message.text == "🚀 Buy Proxy (1 TK)":
        balance = get_balance(uid)
        if balance < 1:
            bot.send_message(message.chat.id, "❌ আপনার ব্যালেন্স অপর্যাপ্ত! প্রক্সি কিনতে আগে টাকা ডিপোজিট করুন।")
            return
        
        conn = sqlite3.connect('proxy_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, data FROM proxies LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            proxy_id, proxy_data = row
            cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
            conn.commit()
            update_balance(uid, -1)
            bot.send_message(message.chat.id, f"✅ **ক্রয় সফল হয়েছে!**\n\n🔗 আপনার প্রক্সি:\n`{proxy_data}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "⚠️ দুঃখিত! এই মুহূর্তে প্রক্সি স্টকে নেই। অ্যাডমিনকে জানান।")
        conn.close()

    elif message.text == "💰 My Balance":
        balance = get_balance(uid)
        bot.send_message(message.chat.id, f"👤 ইউজার আইডি: `{uid}`\n💵 আপনার বর্তমান ব্যালেন্স: **{balance} টাকা**", parse_mode="Markdown")

    elif message.text == "➕ Deposit":
        deposit_msg = (
            "🏦 **বিকাশ পেমেন্ট মেথড**\n\n"
            f"বিকাশ (Personal): `{BKASH_NUMBER}`\n"
            "টাকা সেন্ড মানি করার পর নিচের ধাপগুলো অনুসরণ করুন।\n\n"
            "📸 এখন আপনার পেমেন্টের **স্ক্রিনশট** পাঠান।"
        )
        msg = bot.send_message(message.chat.id, deposit_msg, parse_mode="Markdown")
        bot.register_next_step_handler(msg, get_screenshot)

    elif message.text == "📞 Support":
        bot.send_message(message.chat.id, "যেকোনো সমস্যায় যোগাযোগ করুন: @Mrchowdhury100")

# --- DEPOSIT FLOW ---

def get_screenshot(message):
    if message.content_type != 'photo':
        bot.reply_to(message, "❌ ভুল হয়েছে! দয়া করে পেমেন্টের স্ক্রিনশট (ছবি) পাঠান।")
        return
    
    photo_id = message.photo[-1].file_id
    msg = bot.reply_to(message, "✅ স্ক্রিনশট পেয়েছি। এখন পেমেন্টের **TrxID (ট্রানজেকশন আইডি)** টি লিখুন।")
    bot.register_next_step_handler(msg, get_trxid, photo_id)

def get_trxid(message, photo_id):
    trxid = message.text
    uid = message.from_user.id
    user_name = message.from_user.first_name

    # ইউজারকে জানানো
    bot.send_message(uid, "⏳ আপনার পেমেন্ট রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে। অ্যাপ্রুভ হওয়া পর্যন্ত অপেক্ষা করুন।")

    # অ্যাডমিনকে জানানো
    admin_markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("Approve ✅", callback_data=f"approve_{uid}_{trxid}")
    btn_reject = types.InlineKeyboardButton("Reject ❌", callback_data=f"reject_{uid}")
    admin_markup.add(btn_approve, btn_reject)

    admin_info = (
        "🔔 **নতুন ডিপোজিট রিকোয়েস্ট**\n\n"
        f"👤 ইউজার: {user_name}\n"
        f"🆔 আইডি: `{uid}`\n"
        f"📝 TrxID: `{trxid}`"
    )
    bot.send_photo(ADMIN_ID, photo_id, caption=admin_info, reply_markup=admin_markup, parse_mode="Markdown")

# --- CALLBACK HANDLER (ADMIN APPROVAL) ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def admin_action(call):
    data = call.data.split('_')
    action = data[0]
    target_uid = int(data[1])

    if action == 'approve':
        # এখানে কত টাকা অ্যাড করবেন তা ইনপুট নেয়ার সিস্টেম করা যায়, 
        # তবে আপাতত সিম্পল রাখতে /addtk কমান্ড ব্যবহার করতে পারেন।
        bot.send_message(ADMIN_ID, f"ইউজার {target_uid} এর পেমেন্ট অ্যাপ্রুভ করতে নিচের কমান্ডটি কপি করে টাকার পরিমাণ লিখে সেন্ড করুন:\n\n`/addtk {target_uid} 50`", parse_mode="Markdown")
        bot.send_message(target_uid, "✅ আপনার পেমেন্ট রিকোয়েস্ট অ্যাডমিন গ্রহণ করেছেন। কিছুক্ষণের মধ্যেই ব্যালেন্স যোগ হবে।")
    
    elif action == 'reject':
        bot.send_message(target_uid, "❌ দুঃখিত! আপনার পেমেন্ট রিকোয়েস্টটি অ্যাডমিন রিজেক্ট করেছেন। সঠিক তথ্য দিয়ে আবার চেষ্টা করুন।")
        bot.send_message(ADMIN_ID, f"ইউজার {target_uid} এর রিকোয়েস্ট রিজেক্ট করা হয়েছে।")

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['addtk'])
def admin_add_tk(message):
    if message.from_user.id == ADMIN_ID:
        try:
            args = message.text.split()
            target_id = int(args[1])
            amount = float(args[2])
            update_balance(target_id, amount)
            bot.send_message(message.chat.id, f"✅ ইউজার {target_id}-এ {amount} টাকা অ্যাড করা হয়েছে।")
            bot.send_message(target_id, f"🎉 অভিনন্দন! আপনার অ্যাকাউন্টে {amount} টাকা জমা হয়েছে।")
        except:
            bot.send_message(message.chat.id, "সঠিকভাবে লিখুন। উদাহরণ: `/addtk 12345678 50`", parse_mode="Markdown")

@bot.message_handler(commands=['addstock'])
def admin_add_stock(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "প্রক্সি লিস্ট পাঠান (এক লাইনে একটি):")
        bot.register_next_step_handler(msg, save_stock)

def save_stock(message):
    proxies = message.text.split('\n')
    conn = sqlite3.connect('proxy_bot.db')
    cursor = conn.cursor()
    count = 0
    for p in proxies:
        if p.strip():
            cursor.execute("INSERT INTO proxies (data) VALUES (?)", (p.strip(),))
            count += 1
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ সফলভাবে {count}টি প্রক্সি স্টকে যোগ করা হয়েছে।")

bot.polling()
