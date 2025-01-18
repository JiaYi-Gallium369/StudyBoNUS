from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import logging
import requests
from urllib.parse import urlparse
import time
import asyncio
import random

from brainrot import BRAIN_ROT_VIDEOS
 

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# States
FACULTY, LEVEL, COURSE, MATERIAL_TYPE = range(4)

# Sample course data structure with Google Drive links
COURSES_DATA = {
    'School of Computing': {
        '1000 Level': ['CS1101S', 'CS1231S'],
        '2000 Level': ['CS2030S', 'CS2040S'],
        '3000 Level': ['CS3230', 'CS3243'],
        '4000 Level': ['CS4248', 'CS4224'],
        '5000 Level': ['CS5228', 'CS5242'],
        '6000 Level': ['CS6203', 'CS6215'],
        'Others': ['CFG1002', 'CS2101']
    }
}

COURSE_INFO = {
    'CS1101S': {
        'description': 'Programming Methodology',
        'materials': {
            'Notes': ['https://drive.google.com/file/d/1cY6yrE8o6Io-w8ufLQgT2Nt7Um9PWkxp/view?usp=sharing', 'https://drive.google.com/file/d/1QObuhkqEsSjv72KrmoSzI3pKM0SRCR2q/view?usp=sharing'],
            'Slides': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing'],
            'Cheatsheet': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing'],
            'Past Papers': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing']
        }
    },
    'CS1231S': {
        'description': 'Discrete Structures',
        'materials': {
            'Notes': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing'],
            'Slides': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing'],
            'Cheatsheet': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing'],
            'Past Papers': ['https://drive.google.com/file/d/your_file_id_here/view?usp=sharing']
        }
    }
}

NUS_MODS_WEBSITE_PREFIX = "https://nusmods.com/courses/"

study_state = {
    'studying' : False,
    'start_time' : 0,
    'break' : False
}

def get_direct_link(drive_link: str) -> str:
    """Convert Google Drive sharing link to direct download link."""
    file_id = None
    
    # Extract file ID from various Google Drive link formats
    if 'drive.google.com' in drive_link:
        if '/file/d/' in drive_link:
            file_id = drive_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in drive_link:
            file_id = drive_link.split('id=')[1].split('&')[0]
    
    if not file_id:
        raise ValueError("Invalid Google Drive link format")
    
    return f"https://drive.google.com/uc?export=download&id={file_id}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user to select faculty."""
    keyboard = [['School of Computing']]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Welcome to NUS Course Materials Bot!\n"
        "Please select your faculty:",
        reply_markup=reply_markup
    )
    return FACULTY

async def faculty_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle faculty selection and show course levels."""
    faculty = update.message.text
    context.user_data['faculty'] = faculty
    
    keyboard = [
        ['1000 Level'],
        ['2000 Level'],
        ['3000 Level'],
        ['4000 Level'],
        ['5000 Level'],
        ['6000 Level'],
        ['Others']
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Please select the course level:",
        reply_markup=reply_markup
    )
    return LEVEL

async def level_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle level selection and show available courses."""
    level = update.message.text
    faculty = context.user_data['faculty']
    
    try:
        courses = COURSES_DATA[faculty][level]
        keyboard = [[course] for course in courses]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        await update.message.reply_text(
            "Please select the course:",
            reply_markup=reply_markup
        )
        return COURSE
    except KeyError:
        await update.message.reply_text(
            "Sorry, no courses available for this selection. Please /start again.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def course_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle course selection and show course information and material options."""
    course_code = update.message.text
    try:
        course_info = COURSE_INFO[course_code]
        context.user_data['course'] = course_code
        
        keyboard = [
            ['Notes'],
            ['Slides'],
            ['Cheatsheet'],
            ['Past Papers']
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        message_text = (
            f"Course: {course_code}\n"
            f"Description: {course_info['description']}\n"
            f"Course Link: {NUS_MODS_WEBSITE_PREFIX + course_code}\n\n"
            "Please select the material type:"
        )
        
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
        return MATERIAL_TYPE
    except KeyError:
        await update.message.reply_text(
            "Sorry, course information not available. Please /start again.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def send_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the requested material from Google Drive link."""
    try:
        material_type = update.message.text
        course = context.user_data['course']
        drive_links = COURSE_INFO[course]['materials'][material_type]
        
        await update.message.reply_text(
            f"Retrieving {len(drive_links)} {material_type} for {course}...",
            reply_markup=ReplyKeyboardRemove()
        )
        counter = 0
        for drive_link in drive_links:
            counter += 1
            try:
                # Get direct download link
                direct_link = get_direct_link(drive_link)
                
                # Download the file first
                response = requests.get(direct_link)
                if response.status_code == 200:
                    # Send document using the downloaded content
                    await context.bot.send_document(
                        chat_id=update.message.chat_id,
                        document=response.content,  # Send the actual file content
                        filename=f"{course}_{material_type}_{counter}.pdf"
                    )
                    
                    
                else:
                    raise ValueError(f"Failed to download file: Status code {response.status_code}")
                
            except ValueError as e:
                await update.message.reply_text(
                    "Sorry, there seems to be an issue with the file link. "
                    "Here's the direct link instead:\n" + drive_link
                )
                
            except Exception as e:
                logger.error(f"Error sending file: {str(e)}")
                await update.message.reply_text(
                    "Sorry, there was an error sending the file. "
                    "You can access it directly here:\n" + drive_link
                )
        await update.message.reply_text(
                "Here's your document! Use /start to request another material."
            )
            
    except KeyError:
        await update.message.reply_text(
            "Sorry, this material is not available. Please try another option or /start again."
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        'Operation cancelled. Use /start to begin again.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the conversation."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update.message:
            await update.message.reply_text(
                "Sorry, something went wrong. Please try /start again.",
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")

async def spam_user_until_comeback(update:Update, context: ContextTypes.DEFAULT_TYPE):
    while study_state['break']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"COME BACK AND STUDY! Use /lockin to disable this notification!"
        )
        await asyncio.sleep(3)

async def user_comes_back_update(update:Update, context: ContextTypes.DEFAULT_TYPE):
    study_state['break'] = False

async def send_study_updates(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await asyncio.sleep(60)
    while study_state['studying']:
        video_link = random.choice(BRAIN_ROT_VIDEOS)
        study_state['break'] = True
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"No your crush did not text you. But good job studying! Heres a video for you to relax to: {video_link}"
        )
        await asyncio.sleep(300)
        asyncio.create_task(spam_user_until_comeback(update, context))

        await asyncio.sleep(25*60)

async def start_study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    study_state['studying'] = True
    study_state['start_time'] = time.time()
    await update.message.reply_text(
        "Rizzler be locking in! Get mewing sigma!"
    )
    asyncio.create_task(send_study_updates(update, context))
    return

async def stop_study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    study_state['studying'] = False
    await update.message.reply_text(
        "Thats very skibidi of you :((((((("
    )
    return

def main() -> None:
    """Set up and run the bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = ApplicationBuilder().token('8122445200:AAF6Kh0kqdQyS-y-Y1wfrQ_6EsxiaiVCNVU').build()
    
    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FACULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, faculty_choice)],
            LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, level_choice)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, course_choice)],
            MATERIAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_material)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler('study', start_study_mode))
    application.add_handler(CommandHandler('stop', stop_study_mode))
    application.add_handler(CommandHandler('lockin', user_comes_back_update))
    
    # Start the bot
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()