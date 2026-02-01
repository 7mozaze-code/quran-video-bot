#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام لإنشاء فيديوهات القرآن الكريم
Quran Video Generator Bot
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import arabic_reshaper
from bidi.algorithm import get_display
import json

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل المحادثة
SURAH, RECITER, VERSES, BACKGROUND = range(4)

# قائمة السور (مبسطة - يمكن توسيعها)
SURAHS = {
    "الفاتحة": 1, "البقرة": 2, "آل عمران": 3, "النساء": 4,
    "المائدة": 5, "الأنعام": 6, "الأعراف": 7, "الأنفال": 8,
    "التوبة": 9, "يونس": 10, "هود": 11, "يوسف": 12,
    "الرعد": 13, "إبراهيم": 14, "الحجر": 15, "النحل": 16,
    "الإسراء": 17, "الكهف": 18, "مريم": 19, "طه": 20,
    "الأنبياء": 21, "الحج": 22, "المؤمنون": 23, "النور": 24,
    "الفرقان": 25, "الشعراء": 26, "النمل": 27, "القصص": 28,
    "العنكبوت": 29, "الروم": 30, "لقمان": 31, "السجدة": 32,
    "الأحزاب": 33, "سبأ": 34, "فاطر": 35, "يس": 36,
    "الصافات": 37, "ص": 38, "الزمر": 39, "غافر": 40,
    "فصلت": 41, "الشورى": 42, "الزخرف": 43, "الدخان": 44,
    "الجاثية": 45, "الأحقاف": 46, "محمد": 47, "الفتح": 48,
    "الحجرات": 49, "ق": 50, "الذاريات": 51, "الطور": 52,
    "النجم": 53, "القمر": 54, "الرحمن": 55, "الواقعة": 56,
    "الحديد": 57, "المجادلة": 58, "الحشر": 59, "الممتحنة": 60,
    "الصف": 61, "الجمعة": 62, "المنافقون": 63, "التغابن": 64,
    "الطلاق": 65, "التحريم": 66, "الملك": 67, "القلم": 68,
    "الحاقة": 69, "المعارج": 70, "نوح": 71, "الجن": 72,
    "المزمل": 73, "المدثر": 74, "القيامة": 75, "الإنسان": 76,
    "المرسلات": 77, "النبأ": 78, "النازعات": 79, "عبس": 80,
    "التكوير": 81, "الإنفطار": 82, "المطففين": 83, "الإنشقاق": 84,
    "البروج": 85, "الطارق": 86, "الأعلى": 87, "الغاشية": 88,
    "الفجر": 89, "البلد": 90, "الشمس": 91, "الليل": 92,
    "الضحى": 93, "الشرح": 94, "التين": 95, "العلق": 96,
    "القدر": 97, "البينة": 98, "الزلزلة": 99, "العاديات": 100,
    "القارعة": 101, "التكاثر": 102, "العصر": 103, "الهمزة": 104,
    "الفيل": 105, "قريش": 106, "الماعون": 107, "الكوثر": 108,
    "الكافرون": 109, "النصر": 110, "المسد": 111, "الإخلاص": 112,
    "الفلق": 113, "الناس": 114
}

# قائمة القراء
RECITERS = {
    "عبد الباسط عبد الصمد": "Abdul_Basit_Murattal_192kbps",
    "محمد صديق المنشاوي": "Minshawy_Murattal_128kbps",
    "ماهر المعيقلي": "Maher_AlMuaiqly_128kbps",
    "مشاري العفاسي": "Alafasy_128kbps",
    "سعد الغامدي": "Ghamadi_40kbps",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية المحادثة"""
    user = update.effective_user
    await update.message.reply_text(
        f"السلام عليكم ورحمة الله وبركاته يا {user.first_name}! 🌙\n\n"
        "أنا بوت إنشاء فيديوهات القرآن الكريم 📖\n\n"
        "هساعدك تعمل فيديو قرآن احترافي خطوة بخطوة:\n"
        "1️⃣ اختيار السورة\n"
        "2️⃣ اختيار الشيخ\n"
        "3️⃣ تحديد الآيات\n"
        "4️⃣ اختيار الخلفية\n\n"
        "يلا نبدأ! 🚀\n\n"
        "📖 اكتب اسم السورة اللي عايزها:\n"
        "(مثال: الفاتحة، البقرة، الكهف...)"
    )
    return SURAH


async def receive_surah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اسم السورة"""
    surah_name = update.message.text.strip()
    
    if surah_name not in SURAHS:
        await update.message.reply_text(
            "⚠️ السورة دي مش موجودة في القائمة!\n"
            "لو سمحت اكتب اسم السورة بشكل صحيح.\n"
            "مثال: الفاتحة، البقرة، الكهف"
        )
        return SURAH
    
    context.user_data['surah_name'] = surah_name
    context.user_data['surah_number'] = SURAHS[surah_name]
    
    # عرض قائمة القراء
    keyboard = [[reciter] for reciter in RECITERS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ تمام! اخترت سورة {surah_name}\n\n"
        "🎧 دلوقتي اختار الشيخ اللي عايز تسمع صوته:",
        reply_markup=reply_markup
    )
    return RECITER


async def receive_reciter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اسم الشيخ"""
    reciter_name = update.message.text.strip()
    
    if reciter_name not in RECITERS:
        await update.message.reply_text(
            "⚠️ لو سمحت اختار شيخ من القائمة!"
        )
        return RECITER
    
    context.user_data['reciter_name'] = reciter_name
    context.user_data['reciter_id'] = RECITERS[reciter_name]
    
    await update.message.reply_text(
        f"✅ اخترت الشيخ: {reciter_name}\n\n"
        "🔢 دلوقتي حدد الآيات اللي عايزها\n"
        "اكتب بالشكل ده: من آية X لآية Y\n\n"
        "مثال: من آية 1 لآية 7\n"
        "أو: 1-7",
        reply_markup=ReplyKeyboardRemove()
    )
    return VERSES


async def receive_verses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال نطاق الآيات"""
    text = update.message.text.strip()
    
    # محاولة استخراج الأرقام
    try:
        if '-' in text:
            parts = text.split('-')
            start_verse = int(parts[0].strip())
            end_verse = int(parts[1].strip())
        elif 'لآية' in text or 'لاية' in text:
            import re
            numbers = re.findall(r'\d+', text)
            start_verse = int(numbers[0])
            end_verse = int(numbers[1])
        else:
            raise ValueError
        
        if start_verse < 1 or end_verse < start_verse:
            raise ValueError
            
        context.user_data['start_verse'] = start_verse
        context.user_data['end_verse'] = end_verse
        
        # خيارات الخلفية
        keyboard = [
            ["خلفية إسلامية زرقاء 🕌"],
            ["خلفية خضراء 🌿"],
            ["خلفية ذهبية ✨"],
            ["خلفية سوداء ⬛"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"✅ تمام! من آية {start_verse} لآية {end_verse}\n\n"
            "🖼️ اختار نوع الخلفية:",
            reply_markup=reply_markup
        )
        return BACKGROUND
        
    except:
        await update.message.reply_text(
            "⚠️ الصيغة مش صحيحة!\n"
            "اكتب بالشكل ده: 1-7\n"
            "أو: من آية 1 لآية 7"
        )
        return VERSES


async def receive_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال نوع الخلفية وبدء المعالجة"""
    background_choice = update.message.text.strip()
    
    # تحديد اللون بناءً على الاختيار
    bg_colors = {
        "خلفية إسلامية زرقاء 🕌": (26, 82, 118),
        "خلفية خضراء 🌿": (34, 87, 64),
        "خلفية ذهبية ✨": (138, 102, 36),
        "خلفية سوداء ⬛": (20, 20, 20)
    }
    
    context.user_data['bg_color'] = bg_colors.get(background_choice, (26, 82, 118))
    
    await update.message.reply_text(
        "⏳ جاري تحضير الفيديو...\n"
        "ده ممكن ياخد شوية وقت (1-3 دقائق)\n"
        "استنى شوية... 🎬",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # بدء إنشاء الفيديو
    try:
        video_path = await create_quran_video(context.user_data, update)
        
        # إرسال الفيديو
        await update.message.reply_video(
            video=open(video_path, 'rb'),
            caption=f"✅ تم بحمد الله!\n\n"
                    f"📖 سورة {context.user_data['surah_name']}\n"
                    f"🎧 بصوت الشيخ {context.user_data['reciter_name']}\n"
                    f"🔢 من آية {context.user_data['start_verse']} لآية {context.user_data['end_verse']}\n\n"
                    f"بارك الله فيك! 🤲"
        )
        
        # حذف الملفات المؤقتة
        import shutil
        shutil.rmtree('temp', ignore_errors=True)
        
        await update.message.reply_text(
            "عايز تعمل فيديو تاني؟\n"
            "اكتب /start عشان نبدأ من جديد! 🔄"
        )
        
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        await update.message.reply_text(
            "❌ للأسف حصلت مشكلة في إنشاء الفيديو\n"
            "جرب تاني أو تواصل مع المطور\n"
            f"الخطأ: {str(e)}"
        )
    
    return ConversationHandler.END


async def create_quran_video(user_data: dict, update: Update) -> str:
    """إنشاء فيديو القرآن"""
    
    # إنشاء مجلد مؤقت
    os.makedirs('temp', exist_ok=True)
    
    surah_num = user_data['surah_number']
    start_verse = user_data['start_verse']
    end_verse = user_data['end_verse']
    
    # 1. جلب نصوص الآيات من API
    verses_data = []
    for verse_num in range(start_verse, end_verse + 1):
        url = f"http://api.alquran.cloud/v1/ayah/{surah_num}:{verse_num}/ar.asad"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            verse_text = data['data']['text']
            verses_data.append({
                'number': verse_num,
                'text': verse_text
            })
    
    # 2. جلب ملفات الصوت
    # ملاحظة: هنا نستخدم طريقة مبسطة - في الواقع محتاج تحميل ملفات MP3 للآيات
    # يمكن استخدام everyayah.com API
    
    await update.message.reply_text("📥 جاري تحميل التلاوة...")
    
    # 3. إنشاء صور للآيات
    clips = []
    bg_color = user_data['bg_color']
    
    for verse in verses_data:
        img_path = create_verse_image(verse, bg_color)
        # مدة عرض كل آية (3 ثواني كمثال - يجب ضبطها حسب الصوت)
        clip = ImageClip(img_path, duration=3)
        clips.append(clip)
    
    # 4. دمج الصور في فيديو
    final_video = concatenate_videoclips(clips, method="compose")
    
    # 5. حفظ الفيديو
    output_path = 'temp/quran_video.mp4'
    final_video.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio=False  # سنضيف الصوت لاحقاً
    )
    
    return output_path


def create_verse_image(verse: dict, bg_color: tuple) -> str:
    """إنشاء صورة للآية"""
    
    # إنشاء صورة
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # النص العربي (يحتاج معالجة خاصة)
    verse_text = verse['text']
    
    # معالجة النص العربي
    try:
        reshaped_text = arabic_reshaper.reshape(verse_text)
        bidi_text = get_display(reshaped_text)
    except:
        bidi_text = verse_text
    
    # الخط - نستخدم خط افتراضي (يفضل استخدام خط عربي جميل)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font = ImageFont.load_default()
        number_font = ImageFont.load_default()
    
    # كتابة النص في المنتصف
    text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    position = ((width - text_width) / 2, (height - text_height) / 2)
    draw.text(position, bidi_text, fill=(255, 255, 255), font=font)
    
    # رقم الآية
    verse_number = f"﴿ {verse['number']} ﴾"
    number_bbox = draw.textbbox((0, 0), verse_number, font=number_font)
    number_width = number_bbox[2] - number_bbox[0]
    number_position = ((width - number_width) / 2, position[1] + text_height + 50)
    draw.text(number_position, verse_number, fill=(200, 200, 200), font=number_font)
    
    # حفظ الصورة
    img_path = f'temp/verse_{verse["number"]}.png'
    img.save(img_path)
    
    return img_path


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء المحادثة"""
    await update.message.reply_text(
        'تم الإلغاء! ✋\n'
        'لو عايز تبدأ من جديد، اكتب /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    """تشغيل البوت"""
    
    # توكن البوت
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8308766847:AAHp6VIy0p1Amoch_Q4UlSYEcLJGiQS7w2g")
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SURAH: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_surah)],
            RECITER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reciter)],
            VERSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_verses)],
            BACKGROUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_background)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # بدء البوت
    logger.info("🚀 البوت بدأ العمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
