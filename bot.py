import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- TOKEN VA SOZLAMALAR ---
# BotFather'dan olingan eng yangi toza token o'rnatildi:
BOT_TOKEN = "8620955124:AAHnBLXZsrgwpmZy3Yi8Uy_XzjX-AwYVqXU"
# Sizning shaxsiy Telegram ID raqamingiz bosh admin qilib o'rnatildi:
ADMIN_ID = 5039354291 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("rating.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            fullname TEXT,
            score INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- ADMIN UCHUN STATE (HOLATLAR) ---
class AdminStates(StatesGroup):
    waiting_for_ball = State()

# --- ASOSIY MENYU TUGMALARI ---
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📰 Maktab Yangiliklari", callback_data="news"),
            InlineKeyboardButton(text="📅 Dars Jadvali", callback_data="schedule")
        ],
        [
            InlineKeyboardButton(text="📚 O'quv Materiallari", callback_data="materials"),
            InlineKeyboardButton(text="🤖 IT & AI Klubi", callback_data="it_club")
        ],
        [
            InlineKeyboardButton(text="👥 Koordinatorlar", callback_data="coordinators"),
            InlineKeyboardButton(text="📝 Murojaat Qoldirish", callback_data="contact")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Maktab Haqida", callback_data="about")
        ],
        [
            InlineKeyboardButton(text="📊 Koordinatorlar Reytingi 🏆", callback_data="rating")
        ]
    ])
    return keyboard

# /start buyrug'i
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    conn = sqlite3.connect("rating.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, fullname, score) VALUES (?, ?, ?)", 
                   (message.from_user.id, message.from_user.full_name, 0))
    conn.commit()
    conn.close()

    admin_text = ""
    if message.from_user.id == ADMIN_ID:
        admin_text = "\n\n⚙️ Siz adminsiz! Panelni ochish uchun /admin buyrug'ini yozing."

    await message.answer(
        f"Salom, {message.from_user.first_name}! 👋\n\n"
        f"18-Maktabning rasmiy Smart Botiga xush kelibsiz!\n"
        f"Quyidagi menyulardan kerakli bo'limni tanlang:{admin_text}",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# --- ADMIN PANEL FUNKSIYALARI ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="➕ Ball qo'shish", callback_data="admin_add_ball"))
    
    await message.answer("🛠 **Boshqaruv Paneli:**\n\nKoordinatorlarga ball qo'shish uchun quyidagi tugmani bosing:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_add_ball")
async def admin_add_ball_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Sizga ruxsat berilmagan!")
        return
        
    await callback.message.answer(
        "📝 Ball qo'shish uchun foydalanuvchi **ID raqamini** va **ball miqdorini** bo'sh joy tashlab yozing.\n\n"
        "Misol uchun: `12345678 50`\n"
        "(Bu o'sha ID egasiga 50 ball qo'shadi, ayirish uchun `-50` yozish mumkin)",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_ball)
    await callback.answer()

@dp.message(AdminStates.waiting_for_ball)
async def admin_save_ball(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        text_parts = message.text.split()
        target_id = int(text_parts[0])
        points = int(text_parts[1])
        
        conn = sqlite3.connect("rating.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT fullname, score FROM users WHERE telegram_id = ?", (target_id,))
        user = cursor.fetchone()
        
        if user:
            new_score = user[1] + points
            cursor.execute("UPDATE users SET score = ? WHERE telegram_id = ?", (new_score, target_id))
            conn.commit()
            await message.answer(f"✅ **{user[0]}** (ID: {target_id}) hisobiga {points} ball qo'shildi!\nYangilangan umumiy ball: {new_score}")
        else:
            await message.answer("❌ Bu ID raqamli foydalanuvchi hali botga kirmagan (baza topilmadi).")
            
        conn.close()
    except Exception:
        await message.answer("❌ Noto'g'ri format kiritildi. Qaytadan urinib ko'ring.\nFormat: `ID_RAQAM BALL` (Masalan: `12345678 50`)")
        
    await state.clear()

# --- TUGMA BOSILGANDA ISHLAYDIGAN ODDIY FUNKSIYALAR ---
@dp.callback_query(F.data == "news")
async def cb_news(callback: types.CallbackQuery):
    await callback.message.answer("📰 **Maktab yangiliklari:**\n\nTez kunda shu yerda 18-maktabning eng so'nggi yangiliklari va tadbirlari joylab boriladi.", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "schedule")
async def cb_schedule(callback: types.CallbackQuery):
    await callback.message.answer("📅 **Dars jadvali:**\n\n9-11 sinflar dars jadvallari yaqin kunlarda shu bo'limga to'liq joylashtiriladi.", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "materials")
async def cb_materials(callback: types.CallbackQuery):
    await callback.message.answer("📚 **O'quv materiallari:**\n\nO'qituvchilar va o'quvchilar uchun foydali darsliklar hamda qo'llanmalar tez kunda yuklanadi.", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "it_club")
async def cb_it_club(callback: types.CallbackQuery):
    await callback.message.answer("🤖 **IT & AI Klubi:**\n\n18-maktabning IT va sun'iy intellekt to'garaklari, dars kunlari va qilinayotgan loyihalar haqida ma'lumot.", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "contact")
async def cb_contact(callback: types.CallbackQuery):
    await callback.message.answer("📝 **Murojaat qoldirish:**\n\nTaklif, shikoyat yoki savollaringiz bo'lsa yuborishingiz mumkin. Tez orada adminlarga yo'naltiriladi.", parse_mode="Markdown")
    await callback.answer()

# --- 7 TA YO'NALISH KOORDINATORLARI MATNI ---
@dp.callback_query(F.data == "coordinators")
async def cb_coordinators(callback: types.CallbackQuery):
    coordinators_text = (
        "👥 **18-maktab Kengash tuzilmasi va yo'nalish koordinatorlari:**\n\n"
        "🎓 **Maktab maslahatchisi:**\n"
        "👤 [Ism Familiya] — @[username]\n\n"
        "👑 **Kelajak lideri (Kengash rahbari):**\n"
        "👤 [Ism Familiya] — @[username]\n\n"
        "───────────────────\n\n"
        "📘 1. **Ta'lim koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Ta'lim jarayonlari va o'quvchilar takomilini muvofiqlashtiradi.*\n\n"
        "💻 2. **IT va sun'iy intellekt koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Raqamli yechimlar va innovatsiyalarni rivojlantiradi.*\n\n"
        "📷 3. **Media koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Maktab hayotini ommalashtiradi, axborot siyosatini yuritadi.*\n\n"
        "🎭 4. **Madaniyat koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Ijodiy loyihalar va madaniy tadbirlarni tashkil etadi.*\n\n"
        "🏃‍♂️ 5. **Sport koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Sog'lom turmush tarzini targ'ib etadi, sport tadbirlari o'tkazadi.*\n\n"
        "🌱 6. **Ekologiya koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Tabiatni asrash va ekologik loyihalarni muvofiqlashtiradi.*\n\n"
        "🤝 7. **Ijtimoiy tashabbus koordinatorli:**\n"
        "👤 [Ism Familiya] — @[username]\n"
        "*Volontyorlik va ijtimoiy loyihalarni tashkil etadi.*\n\n"
        "───────────────────\n"
        "👥 **Sinf vakillari:** O'quvchilar fikrini yetkazadi va takliflarni ilgari suradi.\n"
        "🏰 **Klublar:** Qiziqishlar asosidagi faoliyatni amalga oshiradi."
    )
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="main_menu"))
    await callback.message.edit_text(text=coordinators_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

# --- DINAMIK REYTING DIAGRAMMASI FUNKSIYASI ---
@dp.callback_query(F.data == "rating")
async def cb_rating(callback: types.CallbackQuery):
    conn = sqlite3.connect("rating.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, score FROM users ORDER BY score DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()
    
    rating_text = "📊 **Koordinatorlar Reyting Diagrammasi 🏆**\n\n"
    
    if not top_users:
        rating_text += "ℹ️ Hozircha hech kimda ball mavjud emas. Admin ball qo'shgandan so'ng diagramma yangilanadi!"
    else:
        scores = [u[1] for u in top_users]
        max_score = max(scores) if scores else 0
        if max_score == 0: max_score = 1
        
        for index, user in enumerate(top_users, start=1):
            name = user[0]
            score = user[1]
            
            bar_length = int((score / max_score) * 8)
            bar = "🟩" * bar_length if bar_length > 0 else "⬜️"
            
