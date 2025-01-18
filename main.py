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
from pathlib import Path

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# States
FACULTY, LEVEL, COURSE, MATERIAL_TYPE = range(4)

# Sample course data structure
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
        'link': 'http://dummy.com/cs1101s',
        'materials': {
            'Notes': 'path/to/cs1101s/notes.pdf',
            'Slides': 'path/to/cs1101s/slides.pdf',
            'Cheatsheet': 'path/to/cs1101s/cheatsheet.pdf',
            'Past Papers': 'path/to/cs1101s/past_papers.pdf'
        }
    },
    'CS1231S': {
        'description': 'Discrete Structures',
        'link': 'http://dummy.com/cs1231s',
        'materials': {
            'Notes': 'path/to/cs1231s/notes.pdf',
            'Slides': 'path/to/cs1231s/slides.pdf',
            'Cheatsheet': 'path/to/cs1231s/cheatsheet.pdf',
            'Past Papers': 'path/to/cs1231s/past_papers.pdf'
        }
    }
}

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
            f"Course Link: {course_info['link']}\n\n"
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
    """Send the requested material and end the conversation."""
    try:
        material_type = update.message.text
        course = context.user_data['course']
        file_path = Path(COURSE_INFO[course]['materials'][material_type])
        
        await update.message.reply_text(
            f"Sending {material_type} for {course}...",
            reply_markup=ReplyKeyboardRemove()
        )
        
        if file_path.exists():
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=file_path.open('rb'),
                filename=f"{course}_{material_type}.pdf"
            )
            await update.message.reply_text(
                "Here's your document! Use /start to request another material."
            )
        else:
            await update.message.reply_text(
                "Sorry, this file is currently unavailable. Please try again later or contact support."
            )
            
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}")
        await update.message.reply_text(
            "Sorry, there was an error sending the file. Please try again later."
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

def main() -> None:
    """Set up and run the bot."""
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
    
    # Start the bot
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()