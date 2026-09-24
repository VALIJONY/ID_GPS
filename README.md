# ID GPS — boshqaruv tizimi

GPS-kuzatuv qurilmalarini sotadigan va o'rnatadigan kompaniya uchun ichki boshqaruv paneli.
Tizim GPS qurilmalar skladini, mijozlarga sotuvlarni, oylik abonent va SIM karta to'lovlarini,
rasxodlarni va statistikani bitta joyda yuritadi.

![Stack](https://img.shields.io/badge/Django-5.x-0C4B33) ![UI](https://img.shields.io/badge/UI-vanilla%20CSS%20%2B%20JS-3B5BDB) ![Tests](https://img.shields.io/badge/tests-22%20passing-15803D)

## Imkoniyatlar

| Bo'lim | Nima qiladi |
|---|---|
| **Bosh sahifa** | Joriy oy tushumi, sklad qoldig'i, qarzdorlik, faol GPS soni, 6 oylik tushum/rasxod grafigi, so'nggi sotuvlar |
| **Sklad** | GPS qabul qilish (bir partiyada bir nechta), Excel import/eksport, holat bo'yicha filtr, dublikat ID'larni bloklash |
| **Sotuvlar** | Mijozga bir yoki bir nechta GPS sotish, SIM karta va mashina ma'lumotlari, qarzni avtomatik hisoblash |
| **Mijozlar** | Har bir mijozning qurilmalari, platforma login/paroli (yashirin), to'lovlari; Excel eksport |
| **Bugalteriya** | Har bir GPS uchun oylik abonent (A) va SIM (S) to'lovlarini bir bosishda belgilash |
| **Statistika** | Faol abonentlar o'sishi, to'lov intizomi, tushum va rasxod — yil bo'yicha |
| **Rasxodlar** | Xarajatlar hisobi, oy bo'yicha filtr |
| **Eslatmalar** | Jamoa uchun qisqa eslatmalar |
| **Hodimlar** | Foydalanuvchilar va ularning huquqlari (faqat `is_staff`) |

Interfeys o'zbek tilida, yorug' va qorong'i rejimni qo'llab-quvvatlaydi va telefonda ham to'liq ishlaydi.

## Texnologiyalar

- **Backend:** Python 3.10+, Django 5, SQLite
- **Frontend:** build bosqichisiz — o'z dizayn tizimimiz (`static/css/app.css`) va kutubxonasiz JS (`static/js/app.js`)
- **Grafiklar:** Chart.js 4 (jsDelivr CDN), shrift: Inter (Google Fonts)
- **Excel:** `pandas` + `openpyxl`
- **Admin panel:** `django-admin-interface`

## Tezkor boshlash (lokal)

```bash
git clone <repo-url> ID_GPS && cd ID_GPS
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`config/settings.py` repoda **yo'q** (maxfiy ma'lumotlar tufayli `.gitignore` da). Uni
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#settingspy-namunasi) dagi namunadan yarating, so'ng:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Brauzerda `http://127.0.0.1:8000/` ni oching va yaratgan superuser bilan kiring.

## Testlar

```bash
python manage.py test IDGPS
```

Testlar autentifikatsiya va ruxsatlar, sklad, sotuv (qarz, GPS almashtirish, qaytarish),
bugalteriya holat mashinasi, statistika, rasxod, hodim va eslatmalarni qamrab oladi
(`IDGPS/tests.py`).

## Loyiha tuzilishi

```
ID_GPS/
├── config/              # Django loyiha sozlamalari (urls, wsgi; settings.py serverda)
├── IDGPS/               # Asosiy ilova
│   ├── models.py        # Sklad, Sotish, Bugalteriya, Rasxod, Note, CustomUser …
│   ├── views.py         # Barcha sahifalar va biznes-mantiq
│   ├── forms.py         # ModelForm'lar, MoneyField, StyledFormMixin
│   ├── urls.py
│   ├── templatetags/ui.py   # som, display_name, initials, nav_active …
│   └── tests.py
├── templates/
│   ├── base.html        # Layout: sidebar, topbar, toast, tasdiqlash oynasi
│   ├── partials/        # icons.html (SVG to'plami), field.html (forma maydoni)
│   └── *.html           # Sahifalar: ro'yxat (*.html) va forma (*_form.html)
├── static/
│   ├── css/app.css      # Dizayn tizimi
│   └── js/app.js, charts.js
├── docs/                # Batafsil hujjatlar
└── passenger_wsgi.py    # cPanel / Passenger kirish nuqtasi
```

## Rollar va huquqlar

| Amal | Oddiy xodim | `is_staff` | Superuser |
|---|:-:|:-:|:-:|
| Ko'rish, sotuv qo'shish/tahrirlash, GPS qabul qilish, rasxod qo'shish | ✅ | ✅ | ✅ |
| Bugalteriyada to'lov belgilash | ✅ | ✅ | ✅ |
| Bugalteriyada "Null" holatni qayta ochish | — | — | ✅ |
| Sklad va rasxodni tahrirlash/o'chirish, kirim narxini ko'rish | — | — | ✅ |
| Hodimlarni boshqarish | — | ✅ | ✅ |
| Administratorni tahrirlash/o'chirish | — | — | ✅ |

## Hujjatlar

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — ma'lumotlar modeli, biznes qoidalar, URL xaritasi
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — serverga chiqarish, `settings.py`, migratsiyalar
- [docs/DESIGN-SYSTEM.md](docs/DESIGN-SYSTEM.md) — UI tokenlar, komponentlar, yangi sahifa qo'shish
- [CHANGELOG.md](CHANGELOG.md) — o'zgarishlar tarixi
