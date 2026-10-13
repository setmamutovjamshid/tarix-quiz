# 🧠 Onlayn Test (Quiz) — O'zbek Tilidagi Veb-Dastur

Django 5 / 6, Neon (Serverless PostgreSQL) va zamonaviy Tailwind CSS asosida yaratilgan to'liq o'zbek tilidagi onlayn test dasturi.

---

## 🌟 Asosiy Xususiyatlari

- **Foydalanuvchi qismi (Login talab qilinmaydi)**:
  - Bosh sahifada jami savollar soni ko'rinadi va "Nechta savol ishlaysiz?" soni tanlanadi (standart: 20 ta).
  - Savollar tasodifiy tartibda tanlanadi.
  - Har sahifada **faqat bitta savol**: matni va A, B, C, D variantlari.
  - **Darhol baholash**: variant tanlangach, serverda tekshiriladi:
    - To'g'ri bo'lsa: yashil rang va `✅ To'g'ri!`;
    - Noto'g'ri bo'lsa: qizil rang va `❌ Noto'g'ri. To'g'ri javob: X`, to'g'ri variant esa yashil ajratiladi.
  - Variantlar darhol qulflanadi (qayta bosib bo'lmaydi).
  - Pastda "Keyingi savol" tugmasi chiqadi (avtomatik o'tmaydi, faqat tugma bosilganda o'tadi).
  - Oxirgi savolda tugma "Natijani ko'rish"ga aylanadi.
  - Tepada rangli progress bar, "Savol X / Y" va to'g'ri javoblar hisoblagichi.
  - Yakunda to'plangan ball, foiz ko'rsatkichi va "Qayta ishlash" tugmasi.
  - **Xavfsiz API**: `/api/quiz` API endpointi savollarni berganda to'g'ri javobni (`correct`) **FOSh QILMAYDI** — brauzer DevTools/Network orqali ko'rib bo'lmaydi.
  - Oddiy foydalanuvchiga hech qanday admin havolasi ko'rinmaydi.
  - Yorug' va qorong'i (Dark / Light) rejim qo'llab-quvvatlanadi (`localStorage`da saqlanadi).

- **Admin Paneli (`/admin`)**:
  - Maxfiy `ADMIN_PASSWORD` orqali kirish.
  - Muvaffaqiyatli kirgach, imzolangan, `httpOnly` cookie sessiyasi (`JWT` va `SESSION_SECRET` bilan).
  - Login urinishlariga cheklov (**Rate Limiting** — 5 ta xato urinishdan so'ng 10 daqiqaga bloklanadi).
  - Savol qo'shish, tahrirlash, o'chirish formasi (modallar orqali).
  - Qidiruv va 50 tadan sahifalash (Pagination).
  - **JSON Import**: yangi savollarni mavjudlariga qo'shadi. Format:
    ```json
    [{"q":"Savol matni","o":["A","B","C","D"],"a":1}]
    ```
    *(bu yerda `a`: 0 dan 3 gacha bo'lgan to'g'ri javob indeksi)*.
  - **JSON Eksport**: barcha savollarni bir marta bosish bilan `.json` fayl sifatida yuklab olish.
  - **Hammasini o'chirish**: `HA_OCHIRISH` yozma tasdig'i bilan xavfsiz tozalash.

---

## 🛠 Texnologiyalar

- **Backend**: Python 3.12+ / Django 5.x–6.x
- **Ma'lumotlar bazasi**: Neon (Serverless Postgres) + `psycopg 3` + `dj-database-url`
- **Frontend**: Django Templates + Tailwind CSS (Responsive, Mobile-First) + Vanilla JS (Fetch API)
- **Xavfsizlik**: PyJWT, Rate-Limiting, httpOnly Cookies, Parameterized SQL
- **Deploy**: Render (`build.sh`, `Procfile`, `render.yaml`, `gunicorn`, `whitenoise`)

---

## 🚀 1. Neon (PostgreSQL) Loyihasini Ochish

1. [Neon Console](https://console.neon.tech/) saytiga kiring va ro'yxatdan o'ting.
2. **"Create Project"** tugmasini bosing:
   - Nom bering: masalan, `uzbek-quiz-db`
   - Region: o'zingizga yaqin hudud (masalan, Frankfurt `eu-central-1` yoki `us-east-2`)
3. Neon Dashboard'da **Connection Details** oynasidan ulanish havolasini nusxalang (`postgresql://...`).

---

## 🗄 2. `schema.sql` Ni Ishga Tushirish

Neon konsolida chap menyudan **SQL Editor** bo'limiga kiring va loyihadagi `schema.sql` fayli mazmunini nusxalab ishga tushiring (yoki `Run` tugmasini bosing):

```sql
CREATE TABLE IF NOT EXISTS questions (
  id SERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  correct SMALLINT NOT NULL CHECK (correct BETWEEN 0 AND 3),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at);

-- 3 ta namunaviy savol
INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct)
VALUES
('Oʻzbekiston Respublikasi mustaqillikka qachon erishgan?', '1990-yil 1-sentyabr', '1991-yil 1-sentyabr', '1992-yil 8-dekabr', '1993-yil 2-iyul', 1),
('Python dasturlash tilining asoschisi kim?', 'Gvido van Rossum (Guido van Rossum)', 'Brendan Eich', 'Jeyms Gosling', 'Bjarne Stroustrup', 0),
('Dunyodagi eng katta va eng chuqur okean qaysi?', 'Atlantika okeani', 'Hind okeani', 'Shimoliy Muz okeani', 'Tinch okeani', 3);
```

---

## ⚙️ 3. `.env` Faylini Sozlash

Loyiha ildizida `.env.example` faylidan nusxa olib, `.env` faylini yarating:

```bash
cp .env.example .env
```

`.env` tarkibi:
```env
# Neon Postgres ma'lumotlar bazasi URL
DATABASE_URL=postgresql://user:password@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# Admin paneli paroli
ADMIN_PASSWORD=sizning_maxfiy_parolingiz_123

# Admin sessiyasi uchun JWT kaliti (kamida 32 ta belgi)
SESSION_SECRET=super_secret_session_jwt_key_kamida_32_belgidan_iborat

# Django maxfiy kaliti
SECRET_KEY=django-insecure-quiz-production-secret-key

# Sozlamalar
DEBUG=True
ALLOWED_HOSTS=*
```

> **Eslatma**: Agar lokal sinov vaqtida `DATABASE_URL` bo'sh qoldirilsa, dastur avtomatik ravishda lokal `db.sqlite3` ma'lumotlar bazasidan foydalanadi.

---

## 💻 4. Lokal Muhitda Ishga Tushirish

1. **Kutubxonalarni o'rnatish**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Migratsiyalarni qo'llash**:
   ```bash
   python manage.py migrate
   ```

3. **Namunaviy savollarni kiritish (Seed)**:
   ```bash
   python manage.py seed_quiz
   ```

4. **Statik fayllarni yig'ish (ixtiyoriy)**:
   ```bash
   python manage.py collectstatic --no-input
   ```

5. **Serverni ishga tushirish**:
   ```bash
   python manage.py runserver
   ```

Brauzerda oching:
- Foydalanuvchi sahifasi: [http://localhost:8000/](http://localhost:8000/)
- Admin paneli: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🧪 5. Avtomatlashtirilgan Testlarni Ishga Tushirish

Loyiha barcha asosiy funksiyalar (sahifalar, ommaviy API, javob tekshiruvi, JWT auth, rate-limiting, CRUD, import/export) bo'yicha to'liq testlar bilan ta'minlangan:

```bash
python manage.py test quiz
```

---

## ☁️ 6. Render Platformasiga Deploy Qilish

Loyihada Render uchun maxsus `render.yaml`, `build.sh` va `Procfile` tayyorlangan.

### Render'da o'rnatish bosqichlari:

1. Ushbu loyihani o'zingizning GitHub akkauntingizga yuklang (`git push`).
2. [Render Dashboard](https://dashboard.render.com/) ga kiring.
3. **"New +"** tugmasini bosing va **"Web Service"** ni tanlang.
4. GitHub repozitoriyangizni ulang.
5. Quyidagi parametrlarni tekshiring yoki kiriting:
   - **Name**: `uzbek-quiz-app`
   - **Environment**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn quiz_project.wsgi:application`
6. **Environment Variables** (Muhit o'zgaruvchilari) bo'limida quyidagilarni kiriting:
   - `DATABASE_URL`: Neon postgresql connection string
   - `ADMIN_PASSWORD`: Siz tanlagan admin paroli
   - `SESSION_SECRET`: Kamida 32 ta belgidan iborat tasodifiy matn
   - `SECRET_KEY`: Django maxfiy kaliti
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.onrender.com`
   - `PYTHON_VERSION`: `3.12.0` (yoki `3.13.0`)
7. **"Create Web Service"** tugmasini bosing. Render avtomatik ravishda `build.sh` orqali kutubxonalarni o'rnatadi, migratsiyalarni bajaradi, statik fayllarni yig'adi va `gunicorn` orqali ishga tushiradi!

---

## 📖 7. JSON Import/Eksport Formati

Admin panelda ommaviy savollarni yuklash va yuklab olish uchun quyidagi JSON formatidan foydalaniladi:

```json
[
  {
    "q": "Oʻzbekiston Respublikasi poytaxti qaysi shahar?",
    "o": [
      "Samarqand",
      "Toshkent",
      "Buxoro",
      "Xiva"
    ],
    "a": 1
  },
  {
    "q": "Dunyo okeanlari orasida eng kattasi qaysi?",
    "o": [
      "Atlantika",
      "Hind",
      "Shimoliy Muz",
      "Tinch"
    ],
    "a": 3
  }
]
```
- `q` — Savol matni (string)
- `o` — To'rtta variant ro'yxati (har biri matn, aniq 4 ta)
- `a` — To'g'ri javob indeksi (`0` = A, `1` = B, `2` = C, `3` = D)
