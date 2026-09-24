# Serverga chiqarish (deploy)

Loyiha cPanel hostingda **Phusion Passenger** orqali ishlaydi (`passenger_wsgi.py`).
Quyidagi qadamlar shu muhit uchun yozilgan.

## Yangilashni chiqarish tartibi

```bash
cd ~/ID_GPS                      # loyiha papkasi
source <virtualenv>/bin/activate # cPanel "Setup Python App" ko'rsatgan buyruq

git pull
pip install -r requirements.txt
python manage.py check --deploy
python manage.py migrate         # ⚠️ avval "Migratsiyalar" bo'limini o'qing
python manage.py collectstatic --noinput

touch tmp/restart.txt            # Passenger ilovani qayta ishga tushiradi
```

> [!NOTE]
> CSS/JS fayllar shablonlarda `?v=2` bilan ulangan. Statik fayllarni o'zgartirsangiz,
> brauzer keshi eski versiyani ko'rsatmasligi uchun `templates/base.html` va
> `templates/registration/login.html` dagi versiyani oshiring.

## `settings.py` namunasi

`config/settings.py` repoda yo'q va `.gitignore` orqali chiqarib tashlangan. Serverda va
lokal muhitda uni shu namunadan yarating:

```python
# config/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]          # hech qachon repoga yozmang
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1")]

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "IDGPS",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",   # toast xabarlar uchun shart
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "IDGPS.middleware.JWTAuthenticationMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",       # sidebar faol bo'limi uchun shart
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_USER_MODEL = "IDGPS.CustomUser"
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/home/"
LOGOUT_REDIRECT_URL = "/"

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ADMIN_INTERFACE = {"theme": "dark"}

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

Muhit o'zgaruvchilarini cPanel → **Setup Python App → Environment variables** bo'limida
belgilang: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, kerak bo'lsa `DJANGO_DEBUG=1`.

> [!WARNING]
> Git tarixidagi eski `settings.py` da `SECRET_KEY` ochiq holda turibdi. Serverdagi kalit
> hali ham o'sha bo'lsa, uni yangisiga almashtiring:
> `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`.
> Kalit almashganda barcha foydalanuvchilar tizimdan chiqib ketadi — bu kutilgan holat.

## Migratsiyalar

`0002_alter_bugalteriya_abonent_tolov_and_more` migratsiyasi modellar bilan migratsiyalar
orasidagi farqni yopadi: `Bugalteriya.abonent_tolov` va `sim_karta_tolov` NULL qabul qiladi,
`Note.sana` standart qiymati `date.today` bo'ladi. Toza bazada `0001` → `0002` muammosiz
qo'llanadi va `makemigrations --check` hech qanday farq ko'rsatmaydi.

> [!CAUTION]
> Git tarixida avval `0002_alter_sklad_sotildi_sotilmadi` va `0003_bugalteriya`
> migratsiyalari bo'lgan, keyin ular o'chirilib, `0001_initial` qayta yaratilgan. Agar
> serverda o'sha eski fayllar yoki ularning `django_migrations` yozuvlari qolgan bo'lsa,
> `migrate` ikkita "leaf node" xatosini berishi yoki jadvalni qayta yaratishga urinishi mumkin.

Serverda birinchi marta `migrate` qilishdan oldin:

1. Bazaning zaxira nusxasini oling (pastda).
2. `python manage.py showmigrations IDGPS` bilan qo'llangan migratsiyalarni ko'ring.
3. Natija qanday bo'lishiga qarab:
   - **Faqat `[X] 0001_initial` bo'lsa** — `python manage.py migrate` yetarli.
   - **Eski `0002_alter_sklad…`/`0003_bugalteriya` ko'rinsa** — serverdagi fayllarni
     o'chirmang. Jadvallar allaqachon mavjud bo'lgani uchun avval
     `python manage.py migrate IDGPS 0002 --fake` qilish kerak bo'lishi mumkin.
     Buni faqat sxemani `python manage.py sqlmigrate IDGPS 0002` bilan solishtirgandan
     keyin bajaring.

> [!NOTE]
> `Bugalteriya.yil` validatori `datetime.now().year` ni import vaqtida hisoblaydi. Shu
> sababli har yangi yilda `makemigrations` yangi `AlterField` migratsiyasini yaratadi.
> Bu zararsiz, lekin shovqin tug'diradi. Kelajakda validatorni callable'ga o'tkazish tavsiya etiladi.

## Zaxira nusxa (backup)

Ma'lumotlar bitta SQLite faylda (`db.sqlite3`) saqlanadi. Har bir deploy va migratsiyadan oldin:

```bash
cp db.sqlite3 backups/db-$(date +%Y%m%d-%H%M).sqlite3
```

## Deploy'dan keyin tekshirish

- [ ] Kirish sahifasi ochiladi, login qilish mumkin
- [ ] Dashboard'dagi grafik chiqadi (Chart.js CDN'dan yuklanadi)
- [ ] Biror amaldan keyin toast xabar ko'rinadi (messages middleware ishlayapti)
- [ ] `/static/css/app.css` 200 qaytaradi (`collectstatic` bajarilgan)
- [ ] Bugalteriyada katakchani bosish holatni o'zgartiradi (CSRF va JSON endpoint ishlayapti)
- [ ] Sklad → Eksport `.xlsx` yuklab beradi
