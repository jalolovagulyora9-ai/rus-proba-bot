# RUSSIAN PROBA BOT — Ishga Tushirish va Boshqaruv Qo'llanmasi

Ushbu loyiha Rus tili va adabiyoti Milliy sertifikat bepul offline mock imtihoniga Telegram orqali nomzodlarni ro'yxatga olish, ularga unikal raqam berish va ma'lumotlarni Django Admin orqali boshqarish tizimidir.

---

## 1. Dasturlash Muhiti (Windows 11)

Loyiha dasturchining Windows 11 noutbukida ishlab chiqiladi va test qilinadi. Production muhiti esa bulutda (Render + Neon) mustaqil ishlaydi.

### Tizim Talablari:
* **OS:** Windows 11 / 10
* **Python:** 3.11.x (Lokalda o'rnatilgan: Python 3.11.9)
* **Shell:** Windows PowerShell yoki Terminal

---

## 2. Mahalliy Muhitni Sozlash (Yo'riqnoma)

Loyihani o'z kompyuteringizda faollashtirish uchun quyidagi ketma-ketlikni bajaring:

### 1-qadam: PowerShell-da skriptlarni ishga tushirishga ruxsat berish
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2-qadam: Virtual muhitni faollashtirish
```powershell
.\.venv\Scripts\Activate.ps1
```
*(Faollashgach, terminal qatorining boshida `(.venv)` yozuvi paydo bo'ladi).*

### 3-qadam: Kutubxonalarni o'rnatish
```powershell
pip install -r requirements.txt
```

### 4-qadam: Migratsiyalarni qo'llash va Admin yaratish
```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_dev_admin
.\.venv\Scripts\python.exe manage.py setup_roles
.\.venv\Scripts\python.exe manage.py seed_dummy_participants
```

### 5-qadam: Serverni ishga tushirish
```powershell
.\.venv\Scripts\python.exe manage.py runserver
```
Brauzerda quyidagi manzilni oching:  
👉 **http://127.0.0.1:8000/portal-exam-ctrl-2026/**  
* **Login:** `admin`  
* **Parol:** `admin123`  

### 6-qadam: Telegram Botni sinovdan o'tkazish (Polling rejimida)
1. `.env` faylingizdagi `BOT_TOKEN` parametriga @BotFather orqali olingan Telegram bot tokeningizni kiriting:
```ini
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ_sample_token
```
2. Botni mahalliy noutbukingizda polling rejimida ishga tushiring:
```powershell
.\.venv\Scripts\python.exe manage.py run_bot
```
3. Telegram-da botingizga kiring va `/start` buyrug'ini yuboring.

---

## 3. Telegram Bot Arxitekturasi va FSM Ro'yxatdan O'tish

Bot **aiogram 3.x** asinxron freymvorkida qurilgan va quyidagi ketma-ketlikda ishlaydi:
1. **/start:** Ishtirokchining Telegram ID-si bo'yicha bazadan tekshiradi:
   * Agar avval ro'yxatdan o'tgan bo'lsa: uning rasmiy chiptasini (`RU-XXXX`), kiritilgan ma'lumotlarini va doimiy bosh menyuni ko'rsatadi.
   * Agar ro'yxatdan o'tmagan bo'lsa: imtihon ochiqligi va sig'imini tekshiradi hamda "Ro'yxatdan o'tish" taklifini beradi.
2. **FSM Bosqichlari (Yangilangan qulay ketma-ketlik):**
   * **1-bosqich (Ism va Familiya birgalikda):** Bitta xabarda to'liq kiritiladi (masalan: `Jasur Rustamov` yoki `Rustamov Jasur`).
   * **2-bosqich (Telefon):** «📱 Kontaktni ulashish» tugmasi yoki qo'lda `+998XXXXXXXXX` shaklida kiritish imkoniyati.
   * **3-bosqich (Viloyat):** O'zbekistonning 14 ta hududi 2 qatorli inline tugmalarda taqdim etiladi.
   * **4-bosqich (Tuman):** Tanlangan viloyatga mos tumanlar ro'yxati inline tugmalarda ko'rsatiladi ("⬅️ Viloyatni qayta tanlash" tugmasi bilan).
   * **5-bosqich (Ta'lim muassasasi / Maktab):** O'qiyotgan maktab, litsey yoki o'quv markazi nomeri/nomi (masalan: `14-maktab`, `2-son IDUM`).
   * **Tasdiqlash:** Barcha ma'lumotlar kartochka shaklida chiqarilib, «✅ Ma'lumotlarni tasdiqlash», «✏️ Qayta kiritish» va «❌ Bekor qilish» imkoniyati beriladi.
   * **Muvaffaqiyat:** Tranzaksiya orqali unikal `RU-XXXX` raqam generatsiya qilinadi va chipta foydalanuvchiga taqdim etiladi.

---

## 4. Avtotestlarni Ishga Tushirish

Barcha biznes-mantiq, tranzaksiyalar, ma'lumotlar eksporti va Telegram bot FSM testlari avtomatlashtirilgan:
```powershell
.\.venv\Scripts\python.exe manage.py test
```
*(Barcha 48 ta avtotest to'liq muvaffaqiyatli o'tadi).*

---

## 5. Zaxiralash (Backup & Restore) va Xabarnoma (Broadcast)

Loyiha xavfsizlik va favqulodda holatlarda ma'lumotlarni yo'qotmaslik uchun maxsus buyruqlarga ega:

### 1. Zaxira nusxa yaratish:
```powershell
.\.venv\Scripts\python.exe manage.py backup_data
```
* Barcha ishtirokchilar ma'lumotlarini JSON va formatlangan Excel (`.xlsx`) ko'rinishida `backups/backup_participants_YYYYMMDD_HHMMSS.zip` arxiviga joylaydi.

### 2. Zaxiradan qayta tiklash:
```powershell
# Sinov rejimida tekshirish (bazaga tegilmaydi):
.\.venv\Scripts\python.exe manage.py restore_data --file backups/backup_participants_YYYYMMDD_HHMMSS.zip --dry-run

# Haqiqiy tiklash:
.\.venv\Scripts\python.exe manage.py restore_data --file backups/backup_participants_YYYYMMDD_HHMMSS.zip --overwrite
```

### 3. Ishtirokchilarga ommaviy xabarnoma yuborish:
```powershell
# Faqat sinov rejimida (kimlarga borishini ko'rish):
.\.venv\Scripts\python.exe manage.py broadcast_message --text "Imtihon 15-noyabr kuni bo'lib o'tadi!" --dry-run

# Muayyan viloyat ishtirokchilariga yuborish:
.\.venv\Scripts\python.exe manage.py broadcast_message --text "Toshkent shahri uchun manzil: ..." --region "Toshkent shahri"
```

---

## 6. Django Admin va Excel Eksport Imkoniyatlari

Admin panel orqali quyidagi amallarni bajarish mumkin:
1. **Excel formatida eksport:**
   * Ishtirokchilar ro'yxatidan keraklilarni tanlab (yoki barchasini) "Action" bo'limidan **"Tanlangan ishtirokchilarni Excel formatida yuklab olish"** buyrug'ini tanlang.
   * Faylda quyidagi ustunlar to'liq va formatlangan holda shakllanadi:
     * `№` (T/r)
     * `ID Raqami` (`reg_number`, masalan: `RU-0001`)
     * `Ism` (`first_name`)
     * `Familiya` (`last_name`)
     * `Telefon Raqami` (`phone_number`)
     * `Maktab Nomeri` (`school_number`)
     * `Viloyat` (`region`)
     * `Tuman / Shahar` (`district`)
     * `Imtihonga Keldi` (`Ha` / `Yo'q`)
     * `Ro'yxatdan O'tgan Vaqt`
2. **Bir tugma bilan davomatni belgilash:**
   * Ro'yxat ko'rinishining o'zida "Imtihonga keldi" katakchalarini belgilab, pastdagi "Saqlash" tugmasini bosish orqali tezkor davomat olish mumkin.
3. **Qidiruv va Filtrlash:**
   * Qidiruv: F.I.Sh., telefon raqami, unikal ID (`RU-0001`), maktab raqami va Telegram username bo'yicha.
   * Filtrlar: Viloyat, kelganlik holati va sana bo'yicha.

---

## 7. Muhim Me'moriy Ogohlantirishlar (Production haqida)

> [!WARNING]
> **Render Free cheklovlari:**
> * Render Free xizmati **muhim (mission-critical) production tizimlari uchun kafolatlangan yechim emas**.
> * 15 daqiqa harakatsizlikdan so'ng server uxlab qoladi (spin down). Uyg'onish vaqti (Cold Start) 30–50 soniya kechikish keltirib chiqarishi mumkin.
> * UptimeRobot monitoring vositasi sifatida qo'llaniladi, ammo u platforma texnik to'xtashlarida 24/7 ishlashga mutlaq yuridik kafolat (SLA) bera olmaydi.

> [!NOTE]
> **Neon Free PostgreSQL limitlari (2026-yil):**
> * **Xotira:** Har bir loyihaga 1 GB doimiy NVMe xotira beriladi (1 000 ishtirokchi ma'lumotlari ~5–10 MB bo'lib, limitdan atigi 1% foydalaniladi).
> * **Compute:** Oyiga 100 CU-hours (Compute Unit hours). Baza 5 daqiqa harakatsizlikdan so'ng avto-uyquga ketadi va resurs sarflamaydi.
> * **Connection Pooler:** Django ulanishlari toshib ketmasligi uchun Neon ulanish manzilida doimo `-pooler` (PgBouncer) prefiksidan foydalanish shart.

---

## 8. Loyiha Holati va Bosqichlar

* [x] **1-BOSQICH (Bajarildi):** Virtual muhit `.venv`, `requirements.txt`, `.env.example`, `.gitignore`, `PROJECT_PLAN.md` va `README.md`.
* [x] **2-BOSQICH (Bajarildi):** Django loyihasi, PostgreSQL/Neon sozlamalari, `ExamConfig`, `Participant` modellari, xavfsiz tranzaksiyali ro'yxatga olish xizmati (`core/services/registration.py`) va telefon/ism validatorlari.
* [x] **3-BOSQICH (Bajarildi):** Django Admin paneli, filtrlash, ro'yxatga olish sig'imini boshqarish, tezkor davomat, rollar (RBAC) va `openpyxl` Excel eksporti.
* [x] **4-BOSQICH (Bajarildi):** aiogram 3 Telegram boti va FSM ro'yxatga olish jarayoni (Ism va Familiya birgalikda, Telefon, Viloyat, Tuman, Maktab, unikal chipta, `run_bot.py`, `set_webhook.py` va avtotestlar).
* [x] **5-BOSQICH (Bajarildi):** Webhook (`/webhook/telegram/`), monitoring (`/health/`), xavfsiz zaxira nusxa buyruqlari (`backup_data.py`, `restore_data.py`, `broadcast_message.py`), `Procfile`, `runtime.txt` va 48 ta to'liq avtotestlar.
* [x] **6-BOSQICH (Bajarildi):** Render Free + Neon Free bulutiga muvaffaqiyatli joylandi, Telegram Webhook ulandi, Neon PostgreSQL sinovdan o'tkazildi va jonli efirga (Live) chiqdi!

---

## 9. Jonli Havolalar (Production Links)

* 🌐 **Server (Render):** https://rus-proba-bot.onrender.com
* 🩺 **Monitoring (Health Check):** https://rus-proba-bot.onrender.com/health/
* 🔐 **Admin Panel:** https://rus-proba-bot.onrender.com/portal-exam-ctrl-2026/
  * **Login:** `admin`
  * **Boshlang'ich parol:** `admin123`
* 🤖 **Telegram Bot:** @BotFather'dan olingan botingiz (Webhook ulangan, 24/7 ishlaydi)
