# Dizayn tizimi

UI build bosqichisiz ishlaydi: bitta CSS fayl (`static/css/app.css`), bitta umumiy JS
(`static/js/app.js`) va grafiklar uchun `static/js/charts.js`. Tailwind yoki Bootstrap
**ishlatilmaydi** — yangi sahifalarda ham ularni qo'shmang.

## Tokenlar

Barcha ranglar `:root` dagi CSS o'zgaruvchilari orqali beriladi. Qorong'i rejim o'sha
o'zgaruvchilarni qayta aniqlaydi. Shu sababli komponentlarda **hech qachon to'g'ridan-to'g'ri
hex rang yozmang**.

| Token | Vazifasi |
|---|---|
| `--bg`, `--surface`, `--surface-2`, `--surface-3` | Fon qatlamlari (sahifa → karta → ichki blok) |
| `--border`, `--border-strong` | Chegaralar |
| `--text`, `--text-2`, `--muted` | Asosiy, ikkilamchi va xira matn |
| `--primary`, `--primary-soft`, `--ring` | Brend rangi, uning yumshoq foni, fokus halqasi |
| `--success`, `--danger`, `--warning`, `--info` (+ `-soft`) | Holat ranglari — faqat holat uchun |
| `--series-1`, `--series-2`, `--series-3` | Grafik seriyalari (rang ko'r foydalanuvchilar uchun tekshirilgan) |
| `--radius`, `--radius-lg`, `--shadow-*` | Burchak radiusi va soyalar |

**Tema:** `<html data-theme="dark|light">`. Atribut bo'lmasa, OS sozlamasi ishlatiladi.
Tanlov `localStorage` da `idgps-theme` kaliti bilan saqlanadi. Mavzu almashganda
`themechange` hodisasi chiqadi va grafiklar yangi ranglar bilan qayta chiziladi.

## Komponentlar

| Klass | Qayerda |
|---|---|
| `.page-header` > `.page-title`, `.page-subtitle`, `.page-actions` | Har bir sahifa boshi |
| `.kpis` > `.kpi` (`.kpi__label`, `.kpi__value`, `.kpi__meta`, `.kpi__icon--success…`) | Ko'rsatkich kartochkalari |
| `.card` > `.card__header`, `.card__body`, `.card__footer` | Asosiy konteyner |
| `.toolbar` > `.search`, `.segmented`, `.toolbar__end` | Jadval ustidagi qidiruv va filtrlar |
| `.table` (+ `--stack`, `--compact`, `--grouped`) | Jadvallar |
| `.btn` (+ `--primary`, `--secondary`, `--ghost`, `--danger`, `--sm`, `--lg`, `--block`), `.btn-icon` | Tugmalar |
| `.badge` (+ `--success`, `--danger`, `--warning`, `--info`, `--primary`, `--plain`) | Holat belgilari |
| `.form-grid` (+ `--3`, `--4`), `.field`, `.label`, `.input`, `.select`, `.textarea` | Formalar |
| `.form-section` | Raqamlangan forma bo'limlari |
| `.repeater`, `.repeater-row`, `.add-row` | Takrorlanuvchi qatorlar (GPS ro'yxati) |
| `.summary`, `.progress` | Hisob-kitob paneli |
| `.empty` | Bo'sh holat |
| `.tag`, `.plate`, `.money`, `.num` | GPS ID, davlat raqami, summa, raqamlar |

### Mobil jadval (`.table--stack`)

760px dan tor ekranda har bir qator kartochkaga aylanadi. Buning uchun har bir `<td>` ga
`data-label` qo'ying:

- asosiy katak — `class="cell-primary"` (kartochka sarlavhasi bo'ladi);
- amallar katagi — `class="cell-actions"`.

`rowspan` ishlatilgan jadvallarda `table--stack` ishlatmang, ular gorizontal scroll bilan qoladi
(Mijozlar, Bugalteriya).

## JS xatti-harakatlari (`data-*` atributlari)

`app.js` global hodisa delegatsiyasi bilan ishlaydi, shuning uchun alohida sozlash kerak emas.
Atributni qo'ysangiz bas:

| Atribut | Natija |
|---|---|
| `data-table-search="#jadval-id"` | Input jadvalni yozish davomida filtrlaydi. `/` tugmasi fokus beradi |
| `tr[data-group]` | Bir guruhdagi qatorlar (rowspan) birga ko'rinadi yoki yashirinadi |
| `tr[data-search]` | Qidiruv matni qatorning ko'rinadigan matni o'rniga shu qiymatdan olinadi |
| `data-filter-table` + `data-filter-value` | Segment tugmasi `tr[data-status]` bo'yicha filtrlaydi |
| `[data-count-for="#jadval-id"]` | Ko'rinib turgan natijalar soni |
| `th[data-sort="text\|num"]` | Ustun bo'yicha saralash. Katakdagi `data-value` ustun turadi |
| `form[data-confirm="matn"]` | Yuborishdan oldin tasdiqlash oynasi (`data-confirm-title`, `data-confirm-ok` ixtiyoriy) |
| `input[data-money]` | Yozish davomida `1 250 000` formatiga keltiradi. Yuborishda probellar olib tashlanadi |
| `[data-reveal]`, `[data-reveal="#id"]` | Parolni ko'rsatish yoki yashirish |
| `[data-copy="matn"]` | Buferga nusxalash + toast |
| `[data-theme-toggle]`, `[data-nav-toggle]`, `[data-dropdown]` | Tema, mobil menyu, dropdown |

JS'dan foydalanish uchun ochiq API:

- `IDGPS.toast(matn, 'success'|'error'|'warning'|'info')`
- `IDGPS.formatMoney(n)`, `IDGPS.parseMoney(str)`
- `IDGPS.getCookie(nom)`, `IDGPS.icon(nom)`

## Ikonkalar

Ikonkalar `templates/partials/icons.html` dagi SVG to'plamidan olinadi (Lucide uslubida):

```html
<svg class="icon icon-sm"><use href="#i-plus"></use></svg>
```

Yangi ikonka qo'shish uchun o'sha faylga `<symbol id="i-nom" viewBox="0 0 24 24">…</symbol>` qo'shing.

## Shablon yordamchilari (`{% load ui %}`)

| Teg / filtr | Misol |
|---|---|
| `{% nav_active '/sklad' %}` | Sidebar'da faol bo'limni belgilaydi |
| `{{ value\|som }}` | `1250000` → `1 250 000` |
| `{{ user\|display_name }}`, `{{ user\|initials }}` | Hodim ismi, avatar harflari |
| `{{ part\|percent:whole }}` | Foiz |
| `{% include 'partials/field.html' with field=form.x suffix="so'm" full=True %}` | Label, xato va yordam matni bilan tayyor forma maydoni |

## Yangi sahifa qo'shish (namuna)

```django
{% extends 'base.html' %}
{% load ui %}
{% block title %}Hisobotlar{% endblock %}
{% block breadcrumb %}<a href="{% url 'home' %}">Bosh sahifa</a><svg class="icon icon-sm"><use href="#i-chevron-right"></use></svg><span class="current">Hisobotlar</span>{% endblock %}

{% block content %}
<div class="page-header">
  <div><h1 class="page-title">Hisobotlar</h1><p class="page-subtitle">Qisqa tavsif</p></div>
  <div class="page-actions"><a href="#" class="btn btn--primary">Amal</a></div>
</div>

<section class="card">
  <div class="toolbar">
    <div class="search"><svg class="icon icon-sm"><use href="#i-search"></use></svg>
      <input type="search" class="input" data-table-search="#t" placeholder="Qidirish…"></div>
  </div>
  <div class="table-wrap">
    <table class="table table--stack" id="t">…</table>
  </div>
</section>
{% endblock %}
```

So'ng sidebar'ga (`templates/base.html`) havola qo'shing va view'da `messages.success(...)`
bilan foydalanuvchiga natijani bildiring — xabar avtomatik toast bo'lib chiqadi.

## Grafiklar

`static/js/charts.js` Chart.js ustida yupqa qatlam. Ranglarni tokenlardan oladi:

```js
IDGPSCharts.render({
  el: 'canvas-id', type: 'bar', labels: [...], money: true,
  series: [{ label: 'Tushum', data: [...], color: '--series-1' }],
});
```

Qoidalar: bitta grafikda bitta Y o'qi bo'ladi (turli o'lchov birliklari — alohida grafik).
Seriyalar ranglari `--series-1..3` tartibida beriladi. Holat ranglarini (`--success`/`--danger`)
seriya rangi sifatida ishlatmang.
