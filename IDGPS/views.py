import json
from collections import defaultdict
from datetime import date, datetime, timedelta

import jwt
import openpyxl
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView
from openpyxl.styles import Alignment, Font, PatternFill

from .forms import HodimForm, RasxodForm, SkladForm, SotishForm
from .models import Bugalteriya, CustomUser, MashinaMalumoti, Note, Rasxod, Sklad, Sotish

OYLAR = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
         "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
OYLAR_QISQA = ["Yan", "Fev", "Mar", "Apr", "May", "Iyn", "Iyl", "Avg", "Sen", "Okt", "Noy", "Dek"]
FIRST_YEAR = 2020


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Bu bo'lim uchun sizda ruxsat yo'q.")
            return redirect('home')
        return super().handle_no_permission()


class SuperuserRequiredMixin(StaffRequiredMixin):
    def test_func(self):
        return self.request.user.is_superuser


def parse_money(value):
    """'1 200 000' / '1,200,000' -> 1200000. Noto'g'ri qiymat 0 bo'ladi."""
    if value is None:
        return 0
    cleaned = str(value).replace(' ', '').replace(' ', '').replace(',', '')
    try:
        return max(int(float(cleaned)), 0)
    except ValueError:
        return 0


def parse_year(value, default):
    try:
        year = int(value)
    except (TypeError, ValueError):
        return default
    return year if FIRST_YEAR <= year <= date.today().year else default


def month_start(d, shift=0):
    """d oyining 1-sanasi, shift oy siljitilgan holda."""
    index = d.year * 12 + (d.month - 1) + shift
    return date(index // 12, index % 12 + 1, 1)


def xlsx_response(filename, title, headers, rows, widths=None):
    """Chiroyli sarlavhali Excel faylni HTTP javob sifatida qaytaradi."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="3B5BDB", end_color="3B5BDB", fill_type="solid")
        cell.alignment = Alignment(vertical="center")
    for row in rows:
        ws.append(row)
    for index, header in enumerate(headers, 1):
        letter = openpyxl.utils.get_column_letter(index)
        ws.column_dimensions[letter].width = (widths or {}).get(index, max(14, len(str(header)) + 4))
    ws.freeze_panes = "A2"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ---------------------------------------------------------------------------
# Autentifikatsiya
# ---------------------------------------------------------------------------

class Loginview(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, {self.request.get_host()}, self.request.is_secure()):
            return next_url
        return reverse_lazy('home')

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        payload = {
            'id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
        }
        access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        response = redirect(self.get_success_url())
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax',
                            secure=self.request.is_secure())
        return response


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        response = redirect('login')
        response.delete_cookie('access_token')
        return response

    post = get


# ---------------------------------------------------------------------------
# Bosh sahifa (dashboard)
# ---------------------------------------------------------------------------

class Home(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        this_month = month_start(today)
        prev_month = month_start(today, -1)

        sales = Sotish.objects.all()
        month_revenue = sales.filter(sana__gte=this_month).aggregate(s=Sum('summasi'))['s'] or 0
        prev_revenue = sales.filter(sana__gte=prev_month, sana__lt=this_month).aggregate(s=Sum('summasi'))['s'] or 0
        debt = sales.filter(karta__gt=0).aggregate(s=Sum('karta'), n=Count('id'))

        stock = Sklad.objects.aggregate(
            available=Count('id', filter=Q(sotildi_sotilmadi=False)),
            sold=Count('id', filter=Q(sotildi_sotilmadi=True)),
        )
        month_expense = Rasxod.objects.filter(sana__gte=this_month).aggregate(s=Sum('summa'))['s'] or 0

        payments = Bugalteriya.objects.filter(yil=today.year, oy=OYLAR[today.month - 1]).aggregate(
            paid=Count('id', filter=Q(abonent_tolov=True)),
            unpaid=Count('id', filter=Q(abonent_tolov=False)),
        )
        active_gps = Sotish.gps_id.through.objects.count()
        payments['unmarked'] = max(active_gps - payments['paid'] - payments['unpaid'], 0)

        # Oxirgi 6 oy: tushum va rasxod
        start = month_start(today, -5)
        revenue_by_month = defaultdict(int)
        for sana, summa in sales.filter(sana__gte=start).values_list('sana', 'summasi'):
            revenue_by_month[(sana.year, sana.month)] += summa or 0
        expense_by_month = defaultdict(int)
        for sana, summa in Rasxod.objects.filter(sana__gte=start).values_list('sana', 'summa'):
            expense_by_month[(sana.year, sana.month)] += summa or 0
        chart = {'labels': [], 'revenue': [], 'expense': []}
        for shift in range(-5, 1):
            m = month_start(today, shift)
            chart['labels'].append(f"{OYLAR_QISQA[m.month - 1]} {str(m.year)[2:]}")
            chart['revenue'].append(revenue_by_month[(m.year, m.month)])
            chart['expense'].append(expense_by_month[(m.year, m.month)])

        if prev_revenue:
            revenue_delta = round((month_revenue - prev_revenue) * 100 / prev_revenue)
        else:
            revenue_delta = None

        context.update({
            'month_name': OYLAR[today.month - 1],
            'month_revenue': month_revenue,
            'revenue_delta': revenue_delta,
            'debt_total': debt['s'] or 0,
            'debtors': debt['n'],
            'stock': stock,
            'clients_count': sales.count(),
            'month_expense': month_expense,
            'payments': payments,
            'active_gps': active_gps,
            'recent_sales': sales.annotate(gps_count=Count('gps_id')).order_by('-sana', '-id')[:6],
            'recent_notes': Note.objects.select_related('user').order_by('-sana', '-id')[:4],
            'chart_json': json.dumps(chart),
        })
        return context


# ---------------------------------------------------------------------------
# Sklad
# ---------------------------------------------------------------------------

class SkladView(LoginRequiredMixin, View):
    def get(self, request):
        status = request.GET.get('status', '')
        items = Sklad.objects.all()
        counts = items.aggregate(
            all=Count('id'),
            sold=Count('id', filter=Q(sotildi_sotilmadi=True)),
            unsold=Count('id', filter=Q(sotildi_sotilmadi=False)),
        )
        if status == 'sold':
            items = items.filter(sotildi_sotilmadi=True)
        elif status == 'unsold':
            items = items.filter(sotildi_sotilmadi=False)
        items = items.order_by('-olingan_sana', '-id')

        if request.GET.get('export'):
            return xlsx_response(
                f'sklad_{date.today():%Y%m%d}.xlsx', 'Sklad',
                ['GPS ID', 'Yetkazib beruvchi', 'Telefon', 'Kirim narxi', 'Olingan sana', 'Holat'],
                [[i.gps_id, i.olingan_odam, i.tel_raqam, i.summa_prixod, i.olingan_sana,
                  'Sotilgan' if i.sotildi_sotilmadi else 'Skladda'] for i in items],
                widths={1: 22, 2: 26},
            )

        stock_value = Sklad.objects.filter(sotildi_sotilmadi=False).aggregate(s=Sum('summa_prixod'))['s'] or 0
        return render(request, 'sklad.html', {
            'skladlist': items,
            'status': status,
            'counts': counts,
            'stock_value': stock_value,
        })


# Eski URL (/sklad-filter/) bilan moslik uchun
sklad_list = SkladView.as_view()


class SkladAddView(LoginRequiredMixin, View):
    template_name = 'sklad_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': SkladForm(), 'gps_ids': ['']})

    def post(self, request):
        gps_ids = [g.strip() for g in request.POST.getlist('gps_id') if g.strip()]
        data = request.POST.copy()
        data['gps_id'] = gps_ids[0] if gps_ids else ''
        form = SkladForm(data)

        if form.is_valid():
            errors = []
            seen = set()
            for gps_id in gps_ids:
                if gps_id in seen:
                    errors.append(f"«{gps_id}» ro'yxatda ikki marta kiritilgan.")
                seen.add(gps_id)
            existing = set(Sklad.objects.filter(gps_id__in=gps_ids).values_list('gps_id', flat=True))
            errors += [f"«{g}» ID li GPS skladda allaqachon mavjud." for g in sorted(existing)]

            if not errors:
                with transaction.atomic():
                    Sklad.objects.bulk_create([
                        Sklad(
                            gps_id=gps_id,
                            olingan_odam=form.cleaned_data['olingan_odam'],
                            tel_raqam=form.cleaned_data['tel_raqam'],
                            summa_prixod=form.cleaned_data['summa_prixod'],
                            olingan_sana=form.cleaned_data['olingan_sana'],
                            sotildi_sotilmadi=False,
                        ) for gps_id in gps_ids
                    ])
                messages.success(request, f"{len(gps_ids)} ta GPS skladga qo'shildi.")
                return redirect('sklad-list')
            for error in errors:
                messages.error(request, error)

        return render(request, self.template_name, {'form': form, 'gps_ids': gps_ids or ['']})


class SkladUpdateView(SuperuserRequiredMixin, View):
    template_name = 'sklad_form.html'

    def get(self, request, pk):
        sklad = get_object_or_404(Sklad, pk=pk)
        return render(request, self.template_name, {'form': SkladForm(instance=sklad), 'object': sklad})

    def post(self, request, pk):
        sklad = get_object_or_404(Sklad, pk=pk)
        form = SkladForm(request.POST, instance=sklad)
        if form.is_valid():
            form.save()
            messages.success(request, f"«{sklad.gps_id}» yangilandi.")
            return redirect('sklad-list')
        return render(request, self.template_name, {'form': form, 'object': sklad})


class SkladDeleteView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        sklad = get_object_or_404(Sklad, pk=pk)
        if sklad.sotildi_sotilmadi:
            messages.error(request, f"«{sklad.gps_id}» sotilgan. Avval uni sotuvdan olib tashlang.")
        else:
            sklad.delete()
            messages.success(request, f"«{sklad.gps_id}» skladdan o'chirildi.")
        return redirect('sklad-list')


class GPSAddExcelView(LoginRequiredMixin, View):
    COLUMNS = ['gps_id', 'olingan_odam', 'tel_raqam', 'summa_prixod', 'olingan_sana']

    def get(self, request):
        if request.GET.get('download_template'):
            today = date.today().isoformat()
            return xlsx_response(
                'gps_shablon.xlsx', "GPS Ma'lumotlari", self.COLUMNS,
                [['GPS001', 'Ali Valiyev', '+998901234567', 100000, today],
                 ['GPS002', 'Vali Aliyev', '+998907654321', 150000, today]],
                widths={1: 18, 2: 25, 3: 18, 4: 16, 5: 16},
            )
        return redirect('sklad-list')

    def post(self, request):
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "Excel fayl tanlanmagan.")
            return redirect('sklad-list')
        if not excel_file.name.lower().endswith(('.xlsx', '.xls')):
            messages.error(request, "Faqat .xlsx yoki .xls fayllar qabul qilinadi.")
            return redirect('sklad-list')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Faylni o'qib bo'lmadi: {e}")
            return redirect('sklad-list')

        missing = [col for col in self.COLUMNS if col not in df.columns]
        if missing:
            messages.error(request, f"Faylda ustunlar yetishmayapti: {', '.join(missing)}")
            return redirect('sklad-list')

        existing = set(Sklad.objects.values_list('gps_id', flat=True))
        to_create, errors = [], []
        for index, row in df.iterrows():
            if pd.isna(row['gps_id']) or str(row['gps_id']).strip() == '':
                continue
            gps_id = str(row['gps_id']).strip()
            if gps_id.endswith('.0'):  # Excel raqamli ID'larni float qilib o'qiydi
                gps_id = gps_id[:-2]
            if gps_id in existing:
                errors.append(f"{index + 2}-qator: «{gps_id}» allaqachon mavjud")
                continue
            try:
                olingan_sana = pd.to_datetime(row['olingan_sana']).date()
            except (ValueError, TypeError):
                olingan_sana = date.today()
            to_create.append(Sklad(
                gps_id=gps_id,
                olingan_odam='' if pd.isna(row['olingan_odam']) else str(row['olingan_odam']).strip(),
                tel_raqam='' if pd.isna(row['tel_raqam']) else str(row['tel_raqam']).strip()[:15],
                summa_prixod=0 if pd.isna(row['summa_prixod']) else parse_money(row['summa_prixod']),
                olingan_sana=olingan_sana,
                sotildi_sotilmadi=False,
            ))
            existing.add(gps_id)

        if to_create:
            with transaction.atomic():
                Sklad.objects.bulk_create(to_create)
            messages.success(request, f"{len(to_create)} ta GPS Excel orqali qo'shildi.")
        if errors:
            preview = '; '.join(errors[:5]) + (f" va yana {len(errors) - 5} ta" if len(errors) > 5 else '')
            messages.warning(request, f"{len(errors)} ta qator o'tkazib yuborildi: {preview}")
        if not to_create and not errors:
            messages.warning(request, "Faylda qo'shiladigan ma'lumot topilmadi.")
        return redirect('sklad-list')


# ---------------------------------------------------------------------------
# Sotuv
# ---------------------------------------------------------------------------

class SotishListView(LoginRequiredMixin, View):
    def get(self, request):
        items = (Sotish.objects.select_related('dasturiy_taminot')
                 .annotate(gps_count=Count('gps_id'))
                 .order_by('-sana', '-id'))
        totals = Sotish.objects.aggregate(
            revenue=Sum('summasi'),
            debt=Sum('karta', filter=Q(karta__gt=0)),
            debtors=Count('id', filter=Q(karta__gt=0)),
            master=Sum('master_summasi'),
        )
        return render(request, 'sotish.html', {'sotish_items': items, 'totals': totals})


class SotishFormMixin:
    """Sotuv qo'shish va tahrirlash uchun umumiy mantiq."""
    template_name = 'sotish_form.html'

    @staticmethod
    def rows_from_post(post):
        gps = post.getlist('gps_id')
        sims = post.getlist('sim_karta')
        cars = post.getlist('mashina_turi')
        plates = post.getlist('davlat_raqami')
        rows = []
        for i, gps_id in enumerate(gps):
            rows.append({
                'gps_id': gps_id,
                'sim': sims[i].strip() if i < len(sims) else '',
                'mashina_turi': cars[i].strip() if i < len(cars) else '',
                'davlat_raqami': plates[i].strip().upper() if i < len(plates) else '',
            })
        return rows

    @staticmethod
    def rows_from_instance(sotish):
        sims = [s.strip() for s in sotish.sim_karta.split(',')] if sotish.sim_karta else []
        cars = {m.gps_id: m for m in sotish.mashina_malumotlari.all()}
        rows = []
        for i, gps in enumerate(sotish.gps_id.all().order_by('id')):
            car = cars.get(gps.id)
            rows.append({
                'gps_id': str(gps.id),
                'sim': sims[i] if i < len(sims) else '',
                'mashina_turi': car.mashina_turi if car else '',
                'davlat_raqami': car.davlat_raqami if car else '',
            })
        return rows

    def render_form(self, request, form, rows, sotish=None, payment=None):
        payment = payment or {
            'summasi': sotish.summasi if sotish else '',
            'naqd': sotish.naqd if sotish else '',
            'bank_schot': sotish.bank_schot if sotish else '',
            'master_summasi': sotish.master_summasi if sotish else '',
        }
        return render(request, self.template_name, {
            'form': form,
            'sotish': sotish,
            'rows': rows or [{'gps_id': '', 'sim': '', 'mashina_turi': '', 'davlat_raqami': ''}],
            'gps_choices': form.fields['gps_id'].queryset.order_by('gps_id'),
            'payment': payment,
        })

    def save(self, request, form, sotish=None):
        rows = self.rows_from_post(request.POST)
        payment = {k: parse_money(request.POST.get(k)) for k in ('summasi', 'naqd', 'bank_schot', 'master_summasi')}
        errors = []

        selected = [r['gps_id'] for r in rows if r['gps_id']]
        if not selected:
            errors.append("Kamida bitta GPS tanlang.")
        if len(selected) != len(set(selected)):
            errors.append("Bitta GPS bir necha marta tanlangan.")
        if any(not r['gps_id'] for r in rows):
            errors.append("Har bir qatorda GPS tanlanishi kerak.")
        qarz = payment['summasi'] - payment['naqd'] - payment['bank_schot']
        if qarz < 0:
            errors.append("To'langan summa umumiy summadan oshib ketdi.")

        if not form.is_valid() or errors:
            for error in errors:
                messages.error(request, error)
            if form.errors:
                messages.error(request, "Formadagi xatoliklarni tuzating.")
            return self.render_form(request, form, rows, sotish, payment)

        gps_map = {str(g.id): g for g in form.cleaned_data['gps_id']}
        with transaction.atomic():
            if sotish:
                Sklad.objects.filter(id__in=sotish.gps_id.values('id')).update(sotildi_sotilmadi=False)
                sotish.gps_id.clear()
                sotish.mashina_malumotlari.all().delete()

            obj = form.save(commit=False)
            obj.summasi = payment['summasi']
            obj.naqd = payment['naqd']
            obj.bank_schot = payment['bank_schot']
            obj.master_summasi = payment['master_summasi']
            obj.karta = qarz  # 'karta' maydoni qarz qoldig'ini saqlaydi
            obj.sim_karta = ', '.join(r['sim'] for r in rows if r['sim'])
            obj.save()

            gps_objects = [gps_map[r['gps_id']] for r in rows]
            obj.gps_id.add(*gps_objects)
            Sklad.objects.filter(id__in=[g.id for g in gps_objects]).update(sotildi_sotilmadi=True)
            MashinaMalumoti.objects.bulk_create([
                MashinaMalumoti(sotish=obj, gps=gps_map[r['gps_id']],
                                mashina_turi=r['mashina_turi'], davlat_raqami=r['davlat_raqami'])
                for r in rows if r['mashina_turi'] or r['davlat_raqami']
            ])
        return obj


class SotishAddView(LoginRequiredMixin, SotishFormMixin, View):
    def get(self, request):
        return self.render_form(request, SotishForm(), [])

    def post(self, request):
        result = self.save(request, SotishForm(request.POST))
        if isinstance(result, Sotish):
            messages.success(request, f"{result.mijoz} uchun sotuv saqlandi.")
            return redirect('sotish_list')
        return result


class SotishUpdateView(LoginRequiredMixin, SotishFormMixin, View):
    def get(self, request, pk):
        sotish = get_object_or_404(Sotish, pk=pk)
        return self.render_form(request, SotishForm(instance=sotish), self.rows_from_instance(sotish), sotish)

    def post(self, request, pk):
        sotish = get_object_or_404(Sotish, pk=pk)
        result = self.save(request, SotishForm(request.POST, instance=sotish), sotish)
        if isinstance(result, Sotish):
            messages.success(request, f"{result.mijoz} sotuvi yangilandi.")
            return redirect('sotish_list')
        return result


class SotishDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        sotish = get_object_or_404(Sotish, pk=pk)
        with transaction.atomic():
            sotish.gps_id.all().update(sotildi_sotilmadi=False)
            sotish.mashina_malumotlari.all().delete()
            sotish.delete()
        messages.success(request, f"{sotish.mijoz} sotuvi o'chirildi, GPS'lar skladga qaytarildi.")
        return redirect('sotish_list')


# ---------------------------------------------------------------------------
# Rasxod
# ---------------------------------------------------------------------------

class RasxodListView(LoginRequiredMixin, View):
    def get(self, request):
        items = Rasxod.objects.all()
        period = request.GET.get('oy', '')  # YYYY-MM
        if period:
            try:
                start = datetime.strptime(period, '%Y-%m').date()
                items = items.filter(sana__gte=start, sana__lt=month_start(start, 1))
            except ValueError:
                period = ''
        items = items.order_by('-sana', '-id')
        this_month = month_start(date.today())
        return render(request, 'rasxod.html', {
            'rasxod_list': items,
            'period': period,
            'total': items.aggregate(s=Sum('summa'))['s'] or 0,
            'month_total': Rasxod.objects.filter(sana__gte=this_month).aggregate(s=Sum('summa'))['s'] or 0,
            'prev_month_total': Rasxod.objects.filter(
                sana__gte=month_start(this_month, -1), sana__lt=this_month).aggregate(s=Sum('summa'))['s'] or 0,
        })


class RasxodAddView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'rasxod_form.html', {'form': RasxodForm()})

    def post(self, request):
        form = RasxodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Rasxod qo'shildi.")
            return redirect('rasxod_list')
        return render(request, 'rasxod_form.html', {'form': form})


class RasxodUpdateView(SuperuserRequiredMixin, View):
    def get(self, request, pk):
        rasxod = get_object_or_404(Rasxod, pk=pk)
        return render(request, 'rasxod_form.html', {'form': RasxodForm(instance=rasxod), 'object': rasxod})

    def post(self, request, pk):
        rasxod = get_object_or_404(Rasxod, pk=pk)
        form = RasxodForm(request.POST, instance=rasxod)
        if form.is_valid():
            form.save()
            messages.success(request, "Rasxod yangilandi.")
            return redirect('rasxod_list')
        return render(request, 'rasxod_form.html', {'form': form, 'object': rasxod})


class RasxodDeleteView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        get_object_or_404(Rasxod, pk=pk).delete()
        messages.success(request, "Rasxod o'chirildi.")
        return redirect('rasxod_list')


# ---------------------------------------------------------------------------
# Mijozlar
# ---------------------------------------------------------------------------

class MijozlarView(LoginRequiredMixin, TemplateView):
    template_name = 'mijozlar.html'

    def get_clients(self):
        sales = (Sotish.objects.select_related('dasturiy_taminot')
                 .prefetch_related('gps_id', 'mashina_malumotlari')
                 .order_by('-sana', '-id'))
        clients = []
        for sale in sales:
            gps_list = sorted(sale.gps_id.all(), key=lambda g: g.id)
            sims = [s.strip() for s in sale.sim_karta.split(',')] if sale.sim_karta else []
            cars = {m.gps_id: m for m in sale.mashina_malumotlari.all()}
            devices = []
            for i, gps in enumerate(gps_list):
                car = cars.get(gps.id)
                devices.append({
                    'gps': gps,
                    'sim': sims[i] if i < len(sims) else '',
                    'mashina_turi': car.mashina_turi if car else '',
                    'davlat_raqami': car.davlat_raqami if car else '',
                })
            clients.append({
                'sale': sale,
                'devices': devices or [{'gps': None, 'sim': '', 'mashina_turi': '', 'davlat_raqami': ''}],
                'jami_summa': sale.summasi + sale.master_summasi + sale.abonent_tulov * len(gps_list),
            })
        return clients

    def get(self, request, *args, **kwargs):
        if request.GET.get('export'):
            rows = []
            for c in self.get_clients():
                s = c['sale']
                for d in c['devices']:
                    rows.append([
                        s.mijoz, s.mijoz_tel_raqam, str(s.dasturiy_taminot), s.username,
                        d['gps'].gps_id if d['gps'] else '', d['sim'], d['mashina_turi'], d['davlat_raqami'],
                        s.abonent_tulov, s.sana, s.summasi, s.naqd, s.bank_schot, s.karta,
                        s.master, s.master_summasi, c['jami_summa'],
                    ])
            return xlsx_response(
                f'mijozlar_{date.today():%Y%m%d}.xlsx', 'Mijozlar',
                ['Mijoz', 'Telefon', "Dasturiy ta'minot", 'Login', 'GPS ID', 'SIM karta', 'Mashina',
                 'Davlat raqami', 'Abonent', 'Sana', 'Summa', 'Naqd', 'Bank', 'Qarz', 'Master',
                 'Master summasi', 'Jami'],
                rows, widths={1: 24, 5: 20, 6: 18},
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = self.get_clients()
        context.update({
            'clients': clients,
            'device_count': sum(len(c['devices']) for c in clients),
            'debtors': sum(1 for c in clients if c['sale'].karta > 0),
        })
        return context


# ---------------------------------------------------------------------------
# Statistika
# ---------------------------------------------------------------------------

class StatistikaView(LoginRequiredMixin, TemplateView):
    template_name = 'statistika.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        year = parse_year(self.request.GET.get('year'), today.year)
        last_month = today.month if year == today.year else 12

        # Sotuvlar: oy bo'yicha GPS soni, SIM soni va tushum (bitta so'rov)
        gps_before_year = Sotish.gps_id.through.objects.filter(sotish__sana__year__lt=year).count()
        new_gps, new_sims, revenue, sales_count = (defaultdict(int) for _ in range(4))
        year_sales = Sotish.objects.filter(sana__year=year).annotate(n=Count('gps_id'))
        for sale in year_sales.values('sana', 'n', 'summasi', 'sim_karta'):
            m = sale['sana'].month
            new_gps[m] += sale['n']
            new_sims[m] += len([s for s in (sale['sim_karta'] or '').split(',') if s.strip()])
            revenue[m] += sale['summasi'] or 0
            sales_count[m] += 1

        # Abonent to'lovlari
        paid, unpaid, abonent_income = defaultdict(int), defaultdict(int), defaultdict(int)
        for row in (Bugalteriya.objects.filter(yil=year)
                    .values('oy', 'abonent_tolov')
                    .annotate(n=Count('id'), s=Sum('sotish__abonent_tulov'))):
            if row['oy'] not in OYLAR:
                continue
            m = OYLAR.index(row['oy']) + 1
            if row['abonent_tolov'] is True:
                paid[m] += row['n']
                abonent_income[m] += row['s'] or 0
            elif row['abonent_tolov'] is False:
                unpaid[m] += row['n']

        stock_in = defaultdict(int)
        for row in Sklad.objects.filter(olingan_sana__year=year).values('olingan_sana__month').annotate(n=Count('id')):
            stock_in[row['olingan_sana__month']] = row['n']
        expense = defaultdict(int)
        for row in Rasxod.objects.filter(sana__year=year).values('sana__month').annotate(s=Sum('summa')):
            expense[row['sana__month']] = row['s'] or 0

        months, running = [], gps_before_year
        for m in range(1, last_month + 1):
            carried = running
            running += new_gps[m]
            marked = paid[m] + unpaid[m]
            months.append({
                'num': m,
                'oy': OYLAR[m - 1],
                'oldingi_aktiv': carried,
                'qoshilgan': new_gps[m],
                'jami_aktiv': running,
                'sotuvlar': sales_count[m],
                'sim': new_sims[m],
                'skladga_kelgan': stock_in[m],
                'tolagan': paid[m],
                'tolamagan': unpaid[m],
                'tolov_foizi': round(paid[m] * 100 / marked) if marked else None,
                'tushum': revenue[m],
                'abonent_tushum': abonent_income[m],
                'rasxod': expense[m],
            })

        totals = {
            'qoshilgan': sum(new_gps.values()),
            'tushum': sum(revenue.values()),
            'abonent_tushum': sum(abonent_income.values()),
            'rasxod': sum(expense.values()),
            'sotuvlar': sum(sales_count.values()),
        }
        chart = {
            'labels': [OYLAR_QISQA[row['num'] - 1] for row in months],
            'revenue': [row['tushum'] + row['abonent_tushum'] for row in months],
            'expense': [row['rasxod'] for row in months],
            'active': [row['jami_aktiv'] for row in months],
        }
        context.update({
            'months': months,
            'totals': totals,
            'current': months[-1] if months else None,
            'current_year': year,
            'yillar': range(today.year, FIRST_YEAR - 1, -1),
            'hozir_skladda': Sklad.objects.filter(sotildi_sotilmadi=False).count(),
            'chart_json': json.dumps(chart),
        })
        return context


# ---------------------------------------------------------------------------
# Bugalteriya
# ---------------------------------------------------------------------------

def payment_state(record, field):
    if record is None:
        return 'none'
    value = getattr(record, field)
    return 'paid' if value is True else 'unpaid' if value is False else 'null'


class BugalteriyaView(LoginRequiredMixin, TemplateView):
    template_name = 'bugalteriya.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        year = parse_year(self.request.GET.get('yil'), today.year)

        sales = (Sotish.objects.filter(sana__year__lte=year)
                 .prefetch_related('gps_id')
                 .order_by('-sana', '-id'))
        records = {
            (r.sotish_id, r.gps_id, r.oy): r
            for r in Bugalteriya.objects.filter(yil=year, sotish__in=sales)
        }

        rows = []
        summary = {'paid': 0, 'unpaid': 0, 'none': 0}
        current_oy = OYLAR[today.month - 1] if year == today.year else None
        for sale in sales:
            devices = []
            for gps in sorted(sale.gps_id.all(), key=lambda g: g.id):
                cells = []
                for oy in OYLAR:
                    record = records.get((sale.id, gps.id, oy))
                    cells.append({
                        'oy': oy,
                        'id': record.id if record else '',
                        'abonent': payment_state(record, 'abonent_tolov'),
                        'sim': payment_state(record, 'sim_karta_tolov'),
                        'is_current': oy == current_oy,
                    })
                    if oy == current_oy:
                        state = payment_state(record, 'abonent_tolov')
                        summary[state if state in summary else 'none'] += 1
                devices.append({'gps': gps, 'cells': cells})
            if devices:
                rows.append({'sotish': sale, 'devices': devices})

        context.update({
            'rows': rows,
            'oylar': OYLAR,
            'current_oy': current_oy,
            'current_year': year,
            'years': range(today.year, FIRST_YEAR - 1, -1),
            'summary': summary,
        })
        return context


class UpdateBugalteriyaView(LoginRequiredMixin, View):
    NEXT_STATE = {False: True, True: None}

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except ValueError:
            return JsonResponse({'status': False, 'message': "Noto'g'ri so'rov"}, status=400)

        tolov_id = data.get('tolov_id')
        tolov_type = 'sim' if data.get('type') == 'sim' else 'abonent'
        field = 'sim_karta_tolov' if tolov_type == 'sim' else 'abonent_tolov'

        with transaction.atomic():
            if tolov_id not in (None, '', 'null', 'undefined'):
                tolov = get_object_or_404(Bugalteriya.objects.select_for_update(), id=tolov_id)
                current = getattr(tolov, field)
                if current is None:
                    if not request.user.is_superuser:
                        return JsonResponse({
                            'status': False,
                            'message': "Bu holatni faqat administrator o'zgartira oladi",
                        }, status=403)
                    setattr(tolov, field, False)
                else:
                    setattr(tolov, field, self.NEXT_STATE[current])
                tolov.save(update_fields=[field])
            else:
                oy = data.get('oy')
                yil = parse_year(data.get('yil'), None)
                if oy not in OYLAR or not yil or not data.get('sotish_id') or not data.get('gps_id'):
                    return JsonResponse({'status': False, 'message': "To'lov ma'lumotlari to'liq emas"}, status=400)
                sotish = get_object_or_404(Sotish, id=data['sotish_id'])
                gps = get_object_or_404(Sklad, id=data['gps_id'])
                tolov, _ = Bugalteriya.objects.get_or_create(
                    sotish=sotish, gps=gps, oy=oy, yil=yil,
                    defaults={'abonent_tolov': False, 'sim_karta_tolov': False},
                )

        return JsonResponse({
            'status': True,
            'tolov_id': tolov.id,
            'abonent_state': payment_state(tolov, 'abonent_tolov'),
            'sim_state': payment_state(tolov, 'sim_karta_tolov'),
            # eski mijozlar uchun moslik
            'abonent_status': tolov.abonent_tolov,
            'sim_status': tolov.sim_karta_tolov,
        })


# ---------------------------------------------------------------------------
# Hodimlar
# ---------------------------------------------------------------------------

class HodimListView(StaffRequiredMixin, View):
    def get(self, request):
        hodimlar = CustomUser.objects.order_by('-is_superuser', '-is_staff', 'firstname', 'username')
        return render(request, 'hodim.html', {'hodimlar': hodimlar})


class HodimCreateView(StaffRequiredMixin, View):
    def get(self, request):
        return render(request, 'hodim_form.html', {'form': HodimForm()})

    def post(self, request):
        form = HodimForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"{user} hodim sifatida qo'shildi.")
            return redirect('hodim-list')
        return render(request, 'hodim_form.html', {'form': form})


class HodimUpdateView(StaffRequiredMixin, View):
    def get(self, request, pk):
        hodim = get_object_or_404(CustomUser, pk=pk)
        return render(request, 'hodim_form.html', {'form': HodimForm(instance=hodim), 'object': hodim})

    def post(self, request, pk):
        hodim = get_object_or_404(CustomUser, pk=pk)
        if hodim.is_superuser and not request.user.is_superuser:
            messages.error(request, "Administratorni faqat administrator tahrirlay oladi.")
            return redirect('hodim-list')
        form = HodimForm(request.POST, instance=hodim)
        if form.is_valid():
            form.save()
            messages.success(request, f"{hodim} ma'lumotlari yangilandi.")
            return redirect('hodim-list')
        return render(request, 'hodim_form.html', {'form': form, 'object': hodim})


class HodimDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        hodim = get_object_or_404(CustomUser, pk=pk)
        if hodim.pk == request.user.pk:
            messages.error(request, "O'zingizni o'chira olmaysiz.")
        elif hodim.is_superuser and not request.user.is_superuser:
            messages.error(request, "Administratorni faqat administrator o'chira oladi.")
        else:
            hodim.delete()
            messages.success(request, f"{hodim} o'chirildi.")
        return redirect('hodim-list')


# ---------------------------------------------------------------------------
# Eslatmalar
# ---------------------------------------------------------------------------

class NoteView(LoginRequiredMixin, View):
    def get(self, request):
        notes = Note.objects.select_related('user').order_by('-sana', '-id')
        return render(request, 'note.html', {'notes': notes})


class NoteAddView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'note_form.html')

    def post(self, request):
        content = (request.POST.get('note') or '').strip()
        if content:
            Note.objects.create(user=request.user, izoh=content, sana=date.today())
            messages.success(request, "Eslatma saqlandi.")
            return redirect('note-list')
        return render(request, 'note_form.html', {'error': "Eslatma matnini kiriting."})


class NoteEditView(LoginRequiredMixin, View):
    def get_note(self, request, pk):
        note = get_object_or_404(Note, pk=pk)
        return note if note.user_id == request.user.pk else None

    def get(self, request, pk):
        note = self.get_note(request, pk)
        if not note:
            messages.error(request, "Faqat o'z eslatmangizni tahrirlay olasiz.")
            return redirect('note-list')
        return render(request, 'note_form.html', {'note': note, 'is_edit': True})

    def post(self, request, pk):
        note = self.get_note(request, pk)
        if not note:
            return redirect('note-list')
        content = (request.POST.get('note') or '').strip()
        if content:
            note.izoh = content
            note.save(update_fields=['izoh'])
            messages.success(request, "Eslatma yangilandi.")
            return redirect('note-list')
        return render(request, 'note_form.html', {'error': "Eslatma matnini kiriting.", 'note': note, 'is_edit': True})


class NoteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        note = get_object_or_404(Note, pk=pk)
        if note.user_id == request.user.pk or request.user.is_superuser:
            note.delete()
            messages.success(request, "Eslatma o'chirildi.")
        return redirect('note-list')
