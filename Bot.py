import telebot
import sqlite3

# --- CONFIGURATION ---
API_TOKEN = 'APNAR_BOT_TOKEN_EIKHANE_DIN'
ADMIN_ID = 123456789  # Apnar nijoeder Telegram User ID ekhane din
bot = telebot.TeleBot(API_TOKEN)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS proxies (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNCTIONS ---
def get_balance(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    balance = get_balance(message.from_user.id)
    text = f"Welcome! Proxy Rate: 1 TK\nApnar Balance: {balance} TK\n\nCommands:\n/buy - Proxy kinun\n/deposit - Tk add korar niyom\n/id - Apnar ID dekhun"
    bot.reply_to(message, text)

@bot.message_handler(commands=['id'])
def show_id(message):
    bot.reply_to(message, f"Apnar User ID: {message.from_user.id}")

@bot.message_handler(commands=['deposit'])
def deposit(message):
    text = f"Payment korar por Admin ke apnar ID ({message.from_user.id}) pathan.\nAdmin check kore balance add kore dibe."
    bot.reply_to(message, text)

@bot.message_handler(commands=['buy'])
def buy_proxy(message):
    uid = message.from_user.id
    balance = get_balance(uid)
    
    if balance < 1:
        bot.reply_to(message, "Apnar balance nei! Proti proxy 1 TK.")
        return

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, data FROM proxies LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        proxy_id, proxy_data = row
        cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        conn.commit()
        update_balance(uid, -1) # 1tk kete nilo
        bot.send_message(message.chat.id, f"✅ Purchase Successful!\nProxy: `{proxy_data}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Dukkhiro! Stock e ekhon proxy nei.")
    conn.close()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['addstock'])
def add_stock(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "Proxy gulo ek line e ekta kore ekhane paste korun.")
        bot.register_next_step_handler(msg, process_stock)

def process_stock(message):
    proxies = message.text.split('\n')
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    for p in proxies:
        if p.strip():
            cursor.execute("INSERT INTO proxies (data) VALUES (?)", (p.strip(),))
    conn.commit()
    conn.close()
    bot.reply_to(message, f"{len(proxies)} ti proxy stock e add hoyeche.")

@bot.message_handler(commands=['addtk'])
def add_tk(message):
    if message.from_user.id == ADMIN_ID:
        try:
            # Format: /addtk USER_ID AMOUNT
            args = message.text.split()
            target_id = int(args[1])
            amount = float(args[2])
            update_balance(target_id, amount)
            bot.reply_to(message, f"User {target_id} er account e {amount} TK add kora hoyeche.")
            bot.send_message(target_id, f"Apnar account e {amount} TK add kora hoyeche! Current Balance: {get_balance(target_id)} TK")
        except:
            bot.reply_to(message, "Bhul hoyeche! Use: /addtk [user_id] [amount]")

bot.polling()
