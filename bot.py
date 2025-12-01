import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# 1. Logging සකස් කිරීම (Render එකේ Logs බලන්න උදව් වෙනවා)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. Token එක ලබා ගැනීම (Render Environment Variables හරහා)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot පටන් ගන්නකොට (Start Command)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_name}! 👋\n\n"
        "මම Video Downloader Bot කෙනෙක්.\n"
        "මට YouTube, TikTok, Facebook හෝ Instagram link එකක් එවන්න.\n"
        "මම ඒක download කරලා එවන්නම්. 📥"
    )

# Video එක Download කරන ප්‍රධාන කොටස
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # User ට පණිවිඩයක් යැවීම
    status_msg = await update.message.reply_text("Link එක check කරමින් පවතී... 🔎")

    try:
        # Download Settings
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # MP4 වලට මුල් තැන දෙනවා
            'outtmpl': 'downloads/%(id)s.%(ext)s', # downloads කියන folder එක ඇතුලේ save කරන්න
            'quiet': True,
            'max_filesize': 50 * 1024 * 1024  # 50MB සීමාව (Telegram Bot API limit)
        }

        await status_msg.edit_text("Video එක Download වෙමින් පවතී... ⏳\n(Server එකට Save වේ)")

        # Video එක download කිරීම
        video_path = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        # Telegram එකට Upload කිරීම
        await status_msg.edit_text("ඔබ වෙත එවමින් පවතී... 📤")
        
        with open(video_path, 'rb') as video:
            await update.message.reply_video(
                video=video, 
                caption=f"✅ Downloaded via @{context.bot.username}"
            )

        # වැඩේ ඉවර වුනාම File එක Delete කිරීම (Storage පිරෙන නිසා)
        if os.path.exists(video_path):
            os.remove(video_path)
            
        await status_msg.delete() # Status message එක මකලා දානවා

    except Exception as e:
        # මොනවා හරි දෝෂයක් ආවොත්
        error_text = str(e)
        if "File is larger than" in error_text:
             await status_msg.edit_text("❌ සමාවන්න, මේ Video එක 50MB වලට වඩා වැඩි නිසා Telegram හරහා එවන්න බැහැ.")
        else:
            await status_msg.edit_text(f"❌ Error එකක් ආවා: \n{error_text}")
            logging.error(f"Download Error: {error_text}")

# ප්‍රධාන Main Function එක
if __name__ == '__main__':
    # Token එක නැත්නම් නවතින්න
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN එක හම්බුනේ නෑ. Render Environment Variables check කරන්න.")
        exit()

    # Bot නිර්මාණය කිරීම
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands එකතු කිරීම
    app.add_handler(CommandHandler("start", start))
    
    # Message එකක් ආවම (Link එකක්) ක්‍රියාත්මක වීමට
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot is Polling...")
    app.run_polling()