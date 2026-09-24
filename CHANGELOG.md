# O'zgarishlar tarixi

Format [Keep a Changelog](https://keepachangelog.com/) asosida.

## [2.0.0] — 2026-09-24

Interfeys to'liq qayta ishlandi, bir qator xatolar va xavfsizlik muammolari tuzatildi.

### Qo'shildi
- Yagona dizayn tizimi (`static/css/app.css`): yorug' va qorong'i rejim, to'liq mobil moslashuv.
  Bootstrap va Tailwind CDN olib tashlandi.
- Bosh sahifa dashboard'ga aylantirildi: KPI'lar, 6 oylik tushum/rasxod grafigi,
  joriy oy abonent to'lovlari, so'nggi sotuvlar, eslatmalar, tezkor amallar.
- Toast xabarlar — `messages` framework xabarlari endi ko'rinadi.
- Barcha ro'yxatlarda qidiruv, saralash, filtr va natijalar soni. Mobil'da jadval kartochkalarga aylanadi.
- O'chirishdan oldin tasdiqlash oynasi.
- Excel eksport: Sklad va Mijozlar.
- Sklad: bir partiyada bir nechta GPS qabul qilish (Enter bilan keyingi qator), zaxira qiymati KPI'si.
- Sotuv formasi: GPS qatorlari, jonli to'lov paneli (to'landi, qarz, oylik abonent), "To'liq naqd to'landi" tugmasi.
- Bugalteriya: ixcham belgilar, tushuntirish, joyida qoladigan ustunlar, joriy oy ajratilishi, joriy oy KPI'lari.
- Statistika: Chart.js grafiklari, yillik jami ko'rsatkichlar, to'lov intizomi foizi.
- Rasxod: oy bo'yicha filtr, joriy va o'tgan oy jami.
- Mijozlar: platforma parolini yashirish/ko'rsatish, loginni nusxalash.
- 22 ta avtomatik test (`IDGPS/tests.py`), repo hujjatlari (`README.md`, `docs/`).

### Tuzatildi
- Rasxodni tahrirlash ishlamasdi (forma maydoni `summasi`, model maydoni `summa` edi).
- Hodimlar ro'yxatida ismlar bo'sh chiqardi (`first_name` o'rniga `firstname`).
- Eslatma sanasi server ishga tushgan kunda qotib qolardi (`default=datetime.now()`).
- Statistikada "Jami sotilgan" boshqa yillarning oylarini ham qo'shardi. "Jami faol"
  "oldingi + qo'shilgan" ga teng chiqmasdi.
- `?year=abc` / `?yil=abc` sahifani 500 xato bilan buzardi.
- Sotuvni tahrirlashda xato bo'lsa, GPS qatorlari yo'qolib ketardi.
- Bugalteriyada frontend va server holatlari bir-biridan farq qilishi mumkin edi.
  Endi UI server javobidan chiziladi va A/S katakchalari birga yangilanadi.
- `/bugalteriya/update/<id>/` manzili `TypeError` berardi.
- Hodimni tahrirlashda parolni har safar qayta kiritish shart edi.
- Admin panelda hodim ismi ustuni bo'sh edi.
- Qo'lda GPS qo'shishda takroriy `gps_id` tekshirilmasdi.

### Xavfsizlik
- `sotuv/add/` va `sklad-filter/` login talab qilmasdi.
- O'chirish amallari GET orqali ishlardi (CSRF xavfi). Endi faqat POST.
- Sklad va rasxodni tahrirlash/o'chirish serverda superuser bilan cheklandi
  (avval faqat interfeysda yashirilgan edi).
- Hodimlar bo'limi serverda `is_staff` bilan himoyalandi. Hodim o'zini o'chira olmaydi,
  administratorni faqat administrator o'zgartira oladi.
- Qarz serverda hisoblanadi, brauzer yuborgan qiymatga ishonilmaydi.
- Sotuv, sklad va Excel import tranzaksiyada bajariladi.
- `access_token` cookie `HttpOnly` va `SameSite=Lax` qilindi. Login'dan keyin `next`
  manzili xavfsiz tekshiriladi.
- Parol xeshini aniqlash `identify_hasher` orqali qilinadi.
- `.gitignore` qo'shildi (`config/settings.py`, `db.sqlite3`).

### O'zgartirildi
- Statistikadagi "O'tgan oy skladdagi" ko'rsatkichi "Skladga kelgan" bilan almashtirildi.
- Sotilgan GPS'ni skladdan o'chirib bo'lmaydi.
- Shablonlar ro'yxat (`*.html`) va forma (`*_form.html`) ga ajratildi.

### Olib tashlandi
- Ishlatilmagan `static/js/{bugalteriya,skald,sotish,sotish_update}.js`.
- `*_update.html` shablonlari (`*_form.html` bilan almashtirildi).
