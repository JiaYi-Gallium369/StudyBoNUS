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
 

import os
from datetime import datetime
from SoC.onek.onek import COURSE_INFO_1K
from SoC.twok.twok import COURSE_INFO_2K
from SoC.threek.threek import COURSE_INFO_3K
from SoC.fourK.fourK import COURSE_INFO_4K
from SoC.fiveK.fiveK import COURSE_INFO_5K
from SoC.sixK.sixK import COURSE_INFO_6K


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# States
FACULTY, LEVEL, COURSE, MATERIAL_TYPE, EXAM_TYPE, YEAR = range(6)

# Categories
EXAM_TYPE_DATA = ['Midterm', 'Final']
YEAR_DATA = ['EARLIER', '18/19', '19/20', '20/21', '21/22', '22/23', '23/24', 'LATEST']

# Sample course data structure with Google Drive links
COURSES_DATA = {
    'School of Computing': {
        '1000 Level': ['CS1101S', 'CS1231S'],
        '2000 Level': ['CS2030S', 'CS2040S', 'CS2100', 'CS2109S'],
        '3000 Level': ['CS3230', 'CS3243', 'CS3213', 'CS3210'],
        '4000 Level': ['CS4211', 'CS4212', 'CS4215', 'CS4220'],
        '5000 Level': ['CS5231', 'CS5242', 'CS5322', 'CS5339'],
        '6000 Level': ['CS6217', 'CS6222'],
        'Others': ['CFG1002', 'CS2101']
    }
}

COMMANDS = {
    '/start': 'Starts the bot and lets you choose courses',
    '/help': 'Shows this help message',
    '/study': 'Begins the study session',
    '/stop': 'Terminates the study session',
    '/lockin' : 'Try it then u know',
    '/cancel': 'Cancels the current operation'
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
    context.user_data.clear()
    context.user_data['history'] = []  # Initialize the history stack

    """Start the conversation and ask user to select faculty."""
    keyboard = [['School of Computing'], ['Upcoming']]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        """
        ✨Hey there, welcome to StudyBoNUS!✨\n\nYour go-to study sidekick for owning that NUS bell curve like a pro 💅.\n\n Grab all the good stuff—faculty notes, past year papers, and the ultimate cheatsheets—right here in one spot! 📚🔥\n\nKeep your study grind strong with our built-in Pomodoro clock ⏳. It’s fun, it’s efficient, and it’s your new productivity BFF. Let’s goooo! 💪\n\nType /help to explore all the commands—uwu slayyyy~ 🫶 \n\nDon’t gatekeep! Share this with your friends and send us your notes if you wanna contribute to the fam. \n📧 Email us: studybonus@gmail.com\n\nAlright, pick your faculty and let’s dive in! 😎
        """,
        reply_markup=reply_markup
    )
    return FACULTY

async def faculty_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle faculty selection and show course levels."""
    faculty = update.message.text
    
    
    if faculty == "Main Menu":
        return await start(update, context)
        
    if faculty == "Back":
        return await start(update, context)
    
    if faculty == "Upcoming":
        await update.message.reply_text(
            "More faculties coming soon! Stay tuned! 👀✨"
        )
        return await start(update, context)
    faculties = COURSES_DATA.keys()
    if faculty not in faculties:
        await update.message.reply_text(
            "Bruh, that ain't it. Try again and pick your actual faculty 🤨✋",
            reply_markup=ReplyKeyboardRemove()
        )
        keyboard = [['School of Computing'], ['Upcoming']]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Alright bestie, tap your faculty and let’s vibe 🎓✨👇",
            reply_markup=reply_markup
        )
        return FACULTY
    context.user_data['faculty'] = faculty
    
    keyboard = [
        ['1000 Level'],
        ['2000 Level'],
        ['3000 Level'],
        ['4000 Level'],
        ['5000 Level'],
        ['6000 Level'],
        ['Others'],
        ['Back', 'Main Menu']
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Choose your course level fam! From 1000 to 6000, pick your vibe! 👨‍💻🔥",
        reply_markup=reply_markup
    )
    return LEVEL

async def level_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle level selection and show available courses."""
    level = update.message.text

    if level == "Main Menu":
        return await start(update, context)

    if level == "Back":
        keyboard = [['School of Computing', 'Upcoming']]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Alright bestie, tap your faculty and let’s vibe 🎓✨👇",
            reply_markup=reply_markup
        )
        return FACULTY

    context.user_data['level'] = level
    
    try:
        courses = COURSES_DATA[context.user_data['faculty']][level]
        keyboard = [[course] for course in courses]
        keyboard.append(['Back', 'Main Menu'])
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        await update.message.reply_text(
            "Which course are you conquering today?💥📚",
            reply_markup=reply_markup
        )
        return COURSE
    except KeyError:
        await update.message.reply_text(
            "Yikes! No courses for this level. Guess you're too advanced for us 😂 Try another level!",
            reply_markup=ReplyKeyboardRemove()
        )
        keyboard = [
            ['1000 Level'],
            ['2000 Level'],
            ['3000 Level'],
            ['4000 Level'],
            ['5000 Level'],
            ['6000 Level'],
            ['Others'],
            ['Back', 'Main Menu']
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Choose your course level fam! From 1000 to 6000, pick your vibe! 👨‍💻🔥",
            reply_markup=reply_markup
        )
        return LEVEL
    
def get_first_digit(s: str) -> int:
    for char in s:
        if char.isdigit():
            return int(char)
    return None

async def course_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle course selection and show course information and material options."""
    course_code = update.message.text

    if course_code == "Main Menu":
        return await start(update, context)

    if course_code == "Back":
        keyboard = [
            ['1000 Level'],
            ['2000 Level'],
            ['3000 Level'],
            ['4000 Level'],
            ['5000 Level'],
            ['6000 Level'],
            ['Others'],
            ['Back', 'Main Menu']
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Choose your course level fam! From 1000 to 6000, pick your vibe! 👨‍💻🔥",
            reply_markup=reply_markup
        )
        return LEVEL
    
    try:
        # prefix is first digit of course code
        prefix = get_first_digit(course_code)
        if prefix is None:
            raise KeyError
        if 1 <= prefix <= 6: 
            print(prefix)
            course_dict = globals().get(f"COURSE_INFO_{prefix}K")
            print(course_dict)
            print(course_code)
            if course_code in course_dict:
                course_info = course_dict[course_code]
                print(course_info)
                context.user_data['course'] = course_code
            else:
                raise KeyError  
        else:
            raise KeyError
            
        
        keyboard = [
            ['Notes'],
            ['Slides'],
            ['Cheatsheet'],
            ['Past Papers'],
            ['Back', 'Main Menu']
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        message_text = (
            f"Course: {course_code}\n"
            f"Course Title: {course_info['description']}\n"
            f"Course Link: {NUS_MODS_WEBSITE_PREFIX + course_code}\n\n"
            "Ayo, time to choose your weapon! What’s your material type? 🔥👀"
        )
        
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
        return MATERIAL_TYPE
    except KeyError:
        await update.message.reply_text(
            "Whoops, can’t find that course right now! Hit it up again! 🔄",
            reply_markup=ReplyKeyboardRemove()
        )
        courses = COURSES_DATA[context.user_data['faculty']][context.user_data['level']]
        keyboard = [[course] for course in courses]
        keyboard.append(['Back', 'Main Menu'])
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Which course are you conquering today?💥📚",
            reply_markup=reply_markup
        )
        return COURSE

async def material_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle material type selection and proceed accordingly."""
    material_type = update.message.text

    if material_type == "Main Menu":
        return await start(update, context)
    
    if material_type == "Back":
        try:
            courses = COURSES_DATA[context.user_data['faculty']][context.user_data['level']]
            keyboard = [[course] for course in courses]
            keyboard.append(['Back', 'Main Menu'])
            reply_markup = ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await update.message.reply_text(
                "Which course are you conquering today?💥📚",
                reply_markup=reply_markup
            )
            return COURSE
        except KeyError:
            return await start(update, context)

    context.user_data['material_type'] = material_type
    
    if material_type in ['Cheatsheet', 'Past Papers']:
        keyboard = [[exam] for exam in EXAM_TYPE_DATA]
        keyboard.append(['Back', 'Main Menu'])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Which {material_type} exam are we smashing today? 🧠🔥",
            reply_markup=reply_markup
        )
        return EXAM_TYPE
    else:
        # For Notes and Slides
        await send_material(update, context)
        # Stay in MATERIAL_TYPE state after sending files
        keyboard = [
            ['Notes'],
            ['Slides'],
            ['Cheatsheet'],
            ['Past Papers'],
            ['Back', 'Main Menu']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Feel free to choose another material or go back! 🔁",
            reply_markup=reply_markup
        )
        return MATERIAL_TYPE
    

async def exam_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle exam type selection and proceed accordingly."""
    exam_type = update.message.text

    if exam_type == "Main Menu":
        return await start(update, context)
    
    if exam_type == "Back":
        keyboard = [
            ['Notes'],
            ['Slides'],
            ['Cheatsheet'],
            ['Past Papers'],
            ['Back', 'Main Menu']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Ayo, time to choose your weapon! What’s your material type? 🔥👀",
            reply_markup=reply_markup
        )
        return MATERIAL_TYPE
    
    if exam_type not in EXAM_TYPE_DATA:
        await update.message.reply_text(
            "Oops, that exam doesn’t exist! Try again! 😅",
            reply_markup=ReplyKeyboardRemove()
        )
        keyboard = [[exam] for exam in EXAM_TYPE_DATA]
        keyboard.append(['Back', 'Main Menu'])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Which {context.user_data['material_type']} exam are we smashing today? 🧠🔥",
            reply_markup=reply_markup
        )
        return EXAM_TYPE

    context.user_data['exam_type'] = exam_type
    material_type = context.user_data['material_type']
    
    if material_type == 'Past Papers':
        keyboard = [[year] for year in YEAR_DATA + ['Back', 'Main Menu']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Please select the year for {material_type} {exam_type}:",
            reply_markup=reply_markup
        )
        return YEAR
    else:
        # For Cheatsheet
        await send_material(update, context)
        # Stay in EXAM_TYPE state after sending file
        keyboard = [[exam] for exam in EXAM_TYPE_DATA + ['Back', 'Main Menu']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Want to try a different exam type or go back? Your call! 📚 Or use /study to start grinding! 🧠",
            reply_markup=reply_markup
        )
        return EXAM_TYPE

async def year_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle year selection for past papers."""
    year = update.message.text

    if year == "Main Menu":
        return await start(update, context)
    
    if year == "Back":
        keyboard = [[exam] for exam in EXAM_TYPE_DATA + ['Back', 'Main Menu']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Which exam are we smashing today? 🧠🔥",
            reply_markup=reply_markup
        )
        return EXAM_TYPE

    context.user_data['year'] = year
    await send_material(update, context)
    
    # Stay in YEAR state after sending file
    keyboard = [[y] for y in YEAR_DATA + ['Back', 'Main Menu']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "You can select another year or go back ⏪",
        reply_markup=reply_markup
    )
    return YEAR

async def send_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send requested material and maintain proper state."""
    try:
        course = context.user_data['course']
        print("LOGGGGGG: " + course)
        material_type = context.user_data['material_type']
        prefix = int(course[2])
        course_info = None
        if 1 <= prefix <= 6:
            course_dict = globals().get(f"COURSE_INFO_{prefix}K")
            course_info = course_dict[course]
            context.user_data['course'] = course
        print(course_info)
        materials = course_info['materials']
        # Create downloads directory if it doesn't exist
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
        
        if material_type in ['Notes', 'Slides']:
            # Handle multiple files for Notes and Slides
            drive_links = materials[material_type]
            if not isinstance(drive_links, list):
                drive_links = [drive_links]
            
            if len(drive_links) != 0:
                await update.message.reply_text(
                    f"Sending {len(drive_links)} {material_type.lower()}..."
                )
            else:
                await update.message.reply_photo(
                    photo="./empty.jpg",
                )
            
            for index, drive_link in enumerate(drive_links):
                try:
                    direct_link = get_direct_link(drive_link)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{course}_{material_type}_{index+1}_{timestamp}.pdf"
                    filepath = os.path.join('downloads', filename)
                    
                    response = requests.get(direct_link)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        with open(filepath, 'rb') as f:
                            await context.bot.send_document(
                                chat_id=update.message.chat_id,
                                document=f,
                                filename=filename
                            )
                    else:
                        await update.message.reply_text(
                            f"Failed to download file {index+1}. You can access it directly here:\n{drive_link}"
                        )
                except Exception as e:
                    logger.error(f"Error sending file {index+1}: {str(e)}")
                    await update.message.reply_text(
                        f"Error sending file {index+1}. You can access it directly here:\n{drive_link}"
                    )
            
            # Don't end conversation, let material_choice handle the state
            return None
            
        else:  # Handle Cheatsheet and Past Papers
            try:
                exam_type = context.user_data['exam_type']
                
                if material_type == 'Cheatsheet':
                    drive_links = materials['Cheatsheet'][exam_type]
                    if not isinstance(drive_links, list):
                       drive_links = [drive_links]
                
                    if len(drive_links) != 0:
                        await update.message.reply_text(
                            f"Sending {len(drive_links)} {material_type.lower()}..."
                        )
                    else:
                        await update.message.reply_photo(
                            photo="./empty.jpg",
                        )
                    
                else:  # Past Papers
                    year = update.message.text if 'year' not in context.user_data else context.user_data['year']
                    drive_links = materials['Past Papers'][exam_type][year]
                    if not isinstance(drive_links, list):
                       drive_links = [drive_links]
                
                    if len(drive_links) != 0:
                        await update.message.reply_text(
                            f"Sending {len(drive_links)} {material_type.lower()}..."
                        )
                    else:
                        await update.message.reply_photo(
                            photo="./empty.jpg",
                        )

                print(drive_links) 
                for index, drive_link in enumerate(drive_links):
                    try:
                        direct_link = get_direct_link(drive_link)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{course}_{material_type}_{index+1}_{timestamp}.pdf"
                        filepath = os.path.join('downloads', filename)
                        
                        response = requests.get(direct_link)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            with open(filepath, 'rb') as f:
                                await context.bot.send_document(
                                    chat_id=update.message.chat_id,
                                    document=f,
                                    filename=filename
                                )
                        else:
                            await update.message.reply_text(
                                f"Uh-oh, the file {index+1} didn’t download properly. You can access it directly here:\n{drive_link}"
                            )
                    except Exception as e:
                        logger.error(f"Error sending file {index+1}: {str(e)}")
                        await update.message.reply_text(
                            f"Uh-oh! Something went wrong with sending file {index+1}. You can access it directly here:\n{drive_link}"
                        )

            except Exception as e:
                logger.error(f"Error sending file: {str(e)}")
                await update.message.reply_text(
                    "Aww snap, the file didn’t send."
                    "You can access it directly here:\n" + drive_link
                )
            
            # Don't end conversation, let the calling function handle the state
            return None
    
    except KeyError as e:
        logger.error(f"KeyError in send_material: {str(e)}")
        await update.message.reply_text(
            "Aww, this material’s ghosting us. Wanna pick something else? 👻"
        )
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error in send_material: {str(e)}")
        await update.message.reply_text(
            "Oof, error alert! Let’s give it another go with /start! 🚨"
        )
        return None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        'Mission aborted. Hit /start to try again! 🚀',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the conversation."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update.message:
            # Clean up any existing conversation state
            context.user_data.clear()
            
            await update.message.reply_text(
                "Oof, error alert! Let’s give it another go with /start! 🚨",
                reply_markup=ReplyKeyboardRemove()  # Remove any existing keyboard
            )
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")
    return ConversationHandler.END  # Always end the conversation on error


async def spam_user_until_comeback(update:Update, context: ContextTypes.DEFAULT_TYPE):
    while study_state['break']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"STOP WATCHING BRAINROT AND COME BACK AND STUDY👺! Use /lockin or I will keep REMINDING YOU!"
        )
        await asyncio.sleep(3)

async def user_comes_back_update(update:Update, context: ContextTypes.DEFAULT_TYPE):
    study_state['break'] = False

async def send_study_updates(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await asyncio.sleep(60)
    while study_state['studying']:
        
        video_links = random.sample(BRAIN_ROT_VIDEOS, 3)

        study_state['break'] = True
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"No your crush did not text you. But good job studying! Here's some videos for you to relax to:"
        )
        
        for video_link in video_links:
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{video_link}\n"
            )
        await asyncio.sleep(60)
        asyncio.create_task(spam_user_until_comeback(update, context))

        await asyncio.sleep(60)

async def start_study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    study_state['studying'] = True
    study_state['start_time'] = time.time()
    await update.message.reply_text(
        "Rizzler be locking in! Get mewing sigma!\n" +
        "You can rest for 5 minutes every 25 minutes. Use /stop to stop studying."
    )
    asyncio.create_task(send_study_updates(update, context))
    return

async def stop_study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    study_state['studying'] = False
    await update.message.reply_text(
        "Thats very skibidi of you :((((((( \n" +
        "Use /start to start studying again to save your CGPA!"
    )
    return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = "Here are the commands you can use:\n\n" + "\n".join(
        f"{cmd} - {desc}" for cmd, desc in COMMANDS.items()
    )
    await update.message.reply_text(help_text)
    return 


# Update the conversation handler in main()
def main() -> None:
    application = ApplicationBuilder().token('8122445200:AAF6Kh0kqdQyS-y-Y1wfrQ_6EsxiaiVCNVU').build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, start)
        ],
        states={
            FACULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, faculty_choice)],
            LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, level_choice)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, course_choice)],
            MATERIAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, material_choice)],
            EXAM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, exam_type_choice)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year_choice)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, error_handler)]

    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler('study', start_study_mode))
    application.add_handler(CommandHandler('stop', stop_study_mode))
    application.add_handler(CommandHandler('lockin', user_comes_back_update))
    application.add_handler(CommandHandler('help', help_command))
    
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()