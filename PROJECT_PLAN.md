# RUSSIAN PROBA BOT — Loyiha Arxitekturasi va Ishlab Chiqish Rejasi (PROJECT PLAN)

**Loyiha:** Rus tili va adabiyoti Milliy sertifikat bepul offline mock imtihoniga Telegram orqali ro'yxatdan o'tish tizimi.  
**Auditoriya va muddat:** 7 kunlik ro'yxatga olish kampaniyasi, boshlang'ich sig'im ~1 000 nafargacha (Django Admin orqali dinamik boshqariladi).  
**Dasturlash va ishlab chiqarish (Production) taqsimoti:**
* **Dasturlash muhiti:** Windows 11 noutbuki (faqat kod yozish, lokal test va tizimni boshqarish uchun).
* **Dastlabki bepul bulutli muhit:**
  * **Veb-ilova va Webhook:** [Render.com Free](https://render.com)
  * **Ma'lumotlar Bazasi:** [Neon.tech Free](https://neon.tech) (Serverless PostgreSQL)

---

## 1. Dastlabki Bulutli Muhit Tahlili va Muhim Ogohlantirishlar

### 1.1 Render Free: Cheklovlar va Kafolat Yo'qligi
> [!WARNING]
> **Muhim:** Render Free xizmati **muhim (mission-critical) production tizimlari uchun kafolatlangan yechim emas**.
> * 15 daqiqalik harakatsizlikdan so'ng server uxlab qoladi (spin down).
> * Qayta ishga tushish (Cold Start) 30–50 soniya kechikish beradi.
> * **UptimeRobot faqat monitoring va vaqti-vaqti bilan ping berish vositasidir.** U serverning 24/7 uzluksiz ishlashiga mutlaq kafolat (SLA) bera olmaydi (Render tarmoq yangilanishlari yoki platforma cheklovlari vaqtida baribir uxlab qolishi mumkin).
> * *Tavsiya:* Agar imtihonga ro'yxatga olish mas'uliyatli va kechikishlarga yo'l qo'yilmaydigan darajada jiddiy bo'lsa, kelajakda arzon VPS ($3–$5/oy) yoki Render-ning pullik tarifiga o'tish tavsiya etiladi.

### 1.2 Neon Free PostgreSQL Amaldagi Limitlari (2026-yil holatiga)
* **Xotira hajmi (Storage):** **1 GB** doimiy xotira (1 000 – 3 000 ishtirokchi ma'lumotlari ~5–10 MB joy egallaydi, 1 GB bemalol yetadi).
* **Hisoblash quvvati (Compute):** Oyiga **100 CU-hours (Compute Unit hours)** har bir loyiha uchun.
* **Autosuspend (Avto-uyqu):** So'rov bo'lmaganda 5 daqiqada uyquga ketadi va CU-hours sarflamaydi. So'rov kelganda ~500ms ichida uyg'onadi.
* **Ulanishlar nazorati (Connection Pooling):** Ulanishlar limitiga tushib qolmaslik uchun Neon taqdim etuvchi PgBouncer (`-pooler`) ulanish manzilidan foydalaniladi.

---

## 2. Platformaga Bog'lanib Qolmaslik (To'liq Portativlik)

* Veb-ilova (Render) va ma'lumotlar bazasi (Neon) mutlaqo alohida saqlanadi.
* Loyiha **12-Factor App** qoidasiga ko'ra faqat standart `DATABASE_URL` orqali ishlaydi.
* Agar ertaga Render Free cheklovlari (uxlab qolish) xalaqit bersa, kodni 5 daqiqa ichida istalgan boshqa serverga (VPS, Railway, Koyeb, Oracle Cloud) ko'chirish mumkin. Baza esa Neon-da o'zgarmasdan saqlanib qolaveradi.

---

## 3. Xavfsiz Zaxira (Backup) va Ma'lumotlarni Himoyalash Strategiyasi

> [!IMPORTANT]
> Ishtirokchilarning F.I.Sh. va telefon raqamlari shaxsiy ma'lumotlar (PII) hisoblanadi. Shaxsiy ma'lumotlarni ochiq holda shaxsiy Telegram chatiga jo'natish xavfsizlik va maxfiylik talablariga to'g'ri kelmaydi.

**Qabul qilingan xavfsiz zaxira arxitekturasi:**
1. **Serverdagi Zaxiralash Buyrug'i (`manage.py backup_participants`):**
   * Ma'lumotlarni formatlangan JSON va Excel ko'rinishida generatsiya qiladi.
   * Fayllar serverning himoyalangan, tashqi veb-foydalanuvchilar kira olmaydigan `backups/` katalogiga yoziladi.
2. **Shifrlangan Zaxira (Encrypted Backup):**
   * Zaxira fayllari xavfsiz kalit (parol) bilan arxivlanadi yoki PostgreSQL `pg_dump` orqali eksport qilinadi.
3. **Faqat Autentifikatsiyadan o'tgan Admin Eksporti:**
   * Ishtirokchilar ro'yxatini faqat Django Admin paneliga xavfsiz kirgan SuperAdmin va Registratorlar yuklab olishi mumkin.
   * Har bir eksport harakati tizim audit loglarida qayd etiladi.
4. **Qayta Tiklash Mexanizmi (`manage.py restore_participants`):**
   * Favqulodda holatda zaxira faylidan yangi bazaga barcha ishtirokchilarni unikal raqamlari bilan qayta tiklash imkoniyati ta'minlanadi.

---

## 4. Concurrency, Tranzaksiya va Sig'im Nazorati

* **Kampaniya davomiyligi:** ~7 kun.
* **Maksimal sig'im:** Boshlang'ich qiymat 1 000 nafar. Django Admin orqali istalgan payt o'zgartirilishi mumkin.
* **Unikallik:** `telegram_id` va `reg_number` bazada qat'iy **UNIQUE**. `phone_number` esa bir oiladan bir nechta nomzod ro'yxatdan o'tishi uchun **UNIQUE EMAS**, faqat indekslangan.
* **Poyga holati (Race Condition) himoyasi:**  
  Ro'yxatga olish jarayonida `ExamConfig` qatori `select_for_update()` orqali bloklanadi. Barcha operatsiyalar `@transaction.atomic` ichida bajarilib, aiogram ichida `sync_to_async(thread_sensitive=True)` bilan chaqiriladi.

---

## 5. Yangilangan Papkalar Strukturasi

```
rus_mock_exam/
├── .venv/                            # Python virtual muhiti (Git-ga kirmaydi)
├── .env                              # Mahalliy maxfiy kalitlar (Git-ga kirmaydi)
├── .env.example                      # Konfiguratsiya namunasi
├── .gitignore                        # Git chetlatish qoidalari
├── README.md                         # Windows va server uchun qo'llanma
├── PROJECT_PLAN.md                   # Ushbu me'moriy hujjat
├── requirements.txt                  # Python paketlari ro'yxati
├── manage.py                         # Django boshqaruv skripti
├── Procfile                          # Render uchun veb-server ishga tushirish qoidasi
├── runtime.txt                       # Python versiyasi (python-3.11.9)
│
├── config/                           # Django sozlamalari
│   ├── __init__.py
│   ├── settings.py                   # DATABASE_URL, WEBHOOK va xavfsizlik sozlamalari
│   ├── urls.py                       # Admin panel, /webhook/ va /health/ marshrutlari
│   ├── wsgi.py                       # WSGI server
│   └── asgi.py                       # Asinxron ASGI server (Webhook uchun)
│
├── core/                             # Asosiy biznes logikasi
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                     # ExamConfig, Participant, BroadcastLog
│   ├── admin.py                      # Django Admin, filtrlash, RBAC, Excel eksport
│   ├── views.py                      # /health/ (monitoring) va /webhook/telegram/ ko'rinishlari
│   ├── migrations/                   # Baza migratsiyalari
│   ├── services/                     # Mustaqil xizmatlar qatlami
│   │   ├── __init__.py
│   │   ├── registration.py           # select_for_update() va sync_to_async ro'yxatga olish
│   │   ├── validator.py              # Telefon raqami tekshiruvi (+998...)
│   │   ├── export.py                 # openpyxl orqali Excel generatsiyasi
│   │   ├── backup.py                 # Shifrlangan zaxira yaratish va tiklash xizmati
│   │   └── broadcast.py              # Ishtirokchilarga xabar yuborish
│   ├── management/
│   │   └── commands/
│   │       ├── run_bot.py            # Mahalliy test uchun botni polling rejimida yoqish
│   │       ├── set_webhook.py        # Renderni Telegram webhookiga ulash
│   │       ├── backup_data.py        # Xavfsiz zaxira nusxa olish
│   │       └── restore_data.py       # Zaxiradan qayta tiklash
│   └── tests/                        # Avtotestlar
│       ├── __init__.py
│       ├── test_registration.py      # Dublikat va ro'yxatga olish testlari
│       ├── test_concurrency.py       # 1000 ta sig'im chegarasining poyga holati testlari
│       └── test_validation.py        # Telefon raqami tekshiruv testlari
│
├── bot/                              # aiogram 3 Telegram bot logikasi
│   ├── __init__.py
│   ├── loader.py                     # Bot, Dispatcher, MemoryStorage
│   ├── states/                       # FSM holatlari (Name, Phone, Region, District)
│   ├── keyboards/                    # Kontakt ulashish va viloyat inline tugmalari
│   └── handlers/                     # /start va ro'yxatga olish handlerlari
│
├── backups/                          # Serverda xavfsiz saqlanadigan zaxiralar (Git-ga kirmaydi)
└── data/                             # Statik ma'lumotlar
    └── uzbekistan_regions.json       # O'zbekiston viloyat va tumanlari
```

---

## 6. Ishlab Chiqish Bosqichlari (Roadmap)

* [x] **1-BOSQICH (Bajarildi):** Windows 11 noutbukda virtual muhit (`.venv`), `requirements.txt`, `.env.example`, `.gitignore` va `README.md` tayyorlash.
* [x] **2-BOSQICH (Bajarildi):** Django loyihasi, `settings.py` (Neon ulanishi bilan), `models.py` va xavfsiz tranzaksiyali ro'yxatga olish (`registration.py`).
* [x] **3-BOSQICH (Bajarildi):** Django Admin paneli, filtrlash, rollar (RBAC) va `openpyxl` Excel eksporti (`id raqam, ism, familiya, telefon raqam, maktab nomeri, viloyat, tuman`).
* [x] **4-BOSQICH (Bajarildi):** aiogram 3 bot va FSM (Ism va Familiya birgalikda, Telefon, Viloyat, Tuman, Maktab ketma-ketligida, `run_bot.py` va `set_webhook.py`, avtotestlar).
* [x] **5-BOSQICH (Bajarildi):** Webhook (`/webhook/telegram/`), monitoring (`/health/`), xavfsiz zaxiralash buyruqlari (`backup_data.py`, `restore_data.py`, `broadcast_message.py`), `Procfile`, `runtime.txt` va 48 ta to'liq avtotestlar.
* [ ] **6-BOSQICH (Navbatdagi):** Render Free va Neon Free-ga joylash, UptimeRobot monitoringini sozlash va sinovdan o'tkazish.
