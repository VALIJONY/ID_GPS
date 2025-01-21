from django.urls import reverse_lazy
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login,logout
from .models import Bugalteriya, CustomUser, Note, Rasxod,Sklad, Sotish, DasturiyTaminot
from django.views import View
from .forms import SkladForm,SotishForm, HodimForm
from django.views.generic import UpdateView,DeleteView,TemplateView,ListView,CreateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.db.models import Q
from itertools import zip_longest
from django.db import models
import json

class Loginview(LoginView):
    template_name = 'login.html'  

    def get_success_url(self):
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
        response.set_cookie('access_token', access_token)
        response.set_cookie('message', 'Success')  
        return response

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form,
                message="Invalid username or password"
            )
        )

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        response = redirect('login') 
        response.delete_cookie('access_token') 
        return response


class Home(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'base.html', {'user': request.user})
    
    
class SkladView(LoginRequiredMixin, View):
    def get(self,request):
        sklad_list=Sklad.objects.all().order_by('-olingan_sana')
        return render(request,'sklad.html',{'skladlist':sklad_list})
    
    
class SkladAddView(LoginRequiredMixin, View):
    template_name = 'sklad.html'
    def get(self, request):
        form = SkladForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = SkladForm(request.POST)
        if form.is_valid():
            # Asosiy ma'lumotlarni olish
            olingan_odam = form.cleaned_data['olingan_odam']
            tel_raqam = form.cleaned_data['tel_raqam']
            summa_prixod = form.cleaned_data['summa_prixod']
            olingan_sana = form.cleaned_data['olingan_sana']
            
            # Barcha GPS ID larni POST dan olish
            gps_ids = []
            i = 1
            while True:
                gps_id = request.POST.get(f'gps_id_{i}')
                if not gps_id and i == 1:
                    # Birinchi GPS ID formadan olish
                    gps_id = form.cleaned_data.get('gps_id')
                if not gps_id:
                    break
                gps_ids.append(gps_id)
                i += 1
            
            # Har bir GPS ID uchun alohida yozuv yaratish
            for gps_id in gps_ids:
                Sklad.objects.create(
                    gps_id=gps_id,
                    olingan_odam=olingan_odam,
                    tel_raqam=tel_raqam,
                    summa_prixod=summa_prixod,
                    olingan_sana=olingan_sana,
                    sotildi_sotilmadi=False
                )
            
            messages.success(request, "GPS ma'lumotlari muvaffaqiyatli saqlandi!")
            return redirect('sklad-list')
            
        return render(request, self.template_name, {'form': form})
    

class SkladUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        sklad = Sklad.objects.get(pk=pk)
        form = SkladForm(instance=sklad)
        return render(request, 'sklad_update.html', {'form': form})

    def post(self, request, pk):
        sklad = Sklad.objects.get(pk=pk)
        form = SkladForm(request.POST, instance=sklad)
        if form.is_valid():
            form.save()
            return redirect('sklad-list')
        return render(request, 'sklad_update.html', {'form': form})

class SkladDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        sklad = Sklad.objects.get(pk=pk)
        sklad.delete()
        return redirect('sklad-list')


def sklad_list(request):
    status_filter = request.GET.get('status', '')
    skladlist = Sklad.objects.all()

    if status_filter == 'sold':
        skladlist = skladlist.filter(sotildi_sotilmadi=True)
    elif status_filter == 'unsold':
        skladlist = skladlist.filter(sotildi_sotilmadi=False)
        
    skladlist = skladlist.order_by('-olingan_sana')
    return render(request, 'sklad.html', {'skladlist': skladlist})


class SotishListView(LoginRequiredMixin, View):
    def get(self, request):
        sotish_items = Sotish.objects.all().order_by('-sana')  # Sana bo'yicha tartiblangan ro'yxat
        return render(request, 'sotish.html', {'sotish_items': sotish_items})

class SotishAddView(LoginRequiredMixin, View):
    template_name = 'sotish.html'

    def get(self, request):
        form = SotishForm()
        gps_list = Sklad.objects.filter(sotildi_sotilmadi=False)
        return render(request, self.template_name, {
            'form': form,
            'gps_list': gps_list
        })
    
    def post(self, request):
        try:
            # Form ma'lumotlarini olish
            mijoz = request.POST.get('mijoz')
            mijoz_tel_raqam = request.POST.get('mijoz_tel_raqam')
            dasturiy_taminot_id = request.POST.get('dasturiy_taminot')
            username = request.POST.get('username')
            password = request.POST.get('password')
            abonent_tulov = request.POST.get('abonent_tulov')
            sana = request.POST.get('sana')
            summasi = request.POST.get('summasi')
            naqd = request.POST.get('naqd', 0)
            karta = request.POST.get('karta', 0)
            bank_schot = request.POST.get('bank_schot', 0)
            master = request.POST.get('master', '')
            master_summasi = request.POST.get('master_summasi', 0)

            # GPS ID larni olish
            gps_ids = request.POST.getlist('gps_id')
            
            # SIM karta raqamlarini olish va birlashtirish
            sim_kartalar = request.POST.getlist('sim_karta')
            sim_karta_string = ','.join(filter(None, sim_kartalar))

            # Sotish obyektini yaratish
            sotish = Sotish.objects.create(
                mijoz=mijoz,
                mijoz_tel_raqam=mijoz_tel_raqam,
                sim_karta=sim_karta_string,
                dasturiy_taminot_id=dasturiy_taminot_id,
                username=username,
                password=password,
                abonent_tulov=abonent_tulov,
                sana=sana,
                summasi=summasi,
                naqd=naqd,
                karta=karta,
                bank_schot=bank_schot,
                master=master,
                master_summasi=master_summasi
            )
            
            # GPS qurilmalarini sotilgan holatga o'tkazish va bog'lash
            for gps_id in gps_ids:
                if gps_id:  # Bo'sh bo'lmagan GPS ID lar uchun
                    gps = Sklad.objects.get(id=gps_id)
                    gps.sotildi_sotilmadi = True
                    gps.save()
                    sotish.gps_id.add(gps)
            
            messages.success(request, "Sotish muvaffaqiyatli amalga oshirildi!")
            return redirect('sotish_list')
            
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
            form = SotishForm(request.POST)
            return render(request, self.template_name, {'form': form})
        
        return render(request, self.template_name, {'form': SotishForm()})

class SotishUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        sotish = get_object_or_404(Sotish, id=pk)
        mavjud_gpslar = Sklad.objects.filter(Q(sotildi_sotilmadi=False) | Q(id__in=sotish.gps_id.all()))
        
        # GPS va SIM kartalarni juftlab olish
        gps_sim_pairs = []
        sim_kartalar = sotish.sim_karta.split(',') if sotish.sim_karta else []
        
        for i, gps in enumerate(sotish.gps_id.all()):
            sim_karta = sim_kartalar[i] if i < len(sim_kartalar) else ""
            gps_sim_pairs.append({
                'gps': gps,
                'sim': sim_karta.strip()
            })

        context = {
            'sotish': sotish,
            'mavjud_gpslar': mavjud_gpslar,
            'gps_sim_pairs': gps_sim_pairs,
            'dasturiy_taminot': DasturiyTaminot.objects.all(),
        }
        
        return render(request, 'sotish_update.html', context)

    def post(self, request, pk):
        sotish = get_object_or_404(Sotish, id=pk)
        
        try:
            # Formadan ma'lumotlarni olish
            mijoz = request.POST.get('mijoz')
            mijoz_tel = request.POST.get('mijoz_tel_raqam')
            gps_ids = request.POST.getlist('gps_id')
            sim_kartalar = request.POST.getlist('sim_karta')
            dasturiy_taminot_id = request.POST.get('dasturiy_taminot')
            username = request.POST.get('username')
            password = request.POST.get('password')
            summasi = request.POST.get('summasi')
            naqd = request.POST.get('naqd', 0)
            bank_schot = request.POST.get('bank_schot', 0)
            karta = request.POST.get('karta', 0)
            abonent_tulov = request.POST.get('abonent_tulov')
            sana = request.POST.get('sana')
            master = request.POST.get('master', '')
            master_summasi = request.POST.get('master_summasi', 0)

            # Eski GPS'larni sotilmagan holatga qaytarish
            old_gps_list = sotish.gps_id.all()
            for old_gps in old_gps_list:
                old_gps.sotildi_sotilmadi = False
                old_gps.save()
            
            # Ma'lumotlarni yangilash
            sotish.mijoz = mijoz
            sotish.mijoz_tel_raqam = mijoz_tel
            sotish.dasturiy_taminot_id = dasturiy_taminot_id
            sotish.username = username
            sotish.password = password
            sotish.summasi = summasi
            sotish.naqd = naqd
            sotish.bank_schot = bank_schot
            sotish.karta = karta
            sotish.abonent_tulov = abonent_tulov
            sotish.sana = sana
            sotish.master = master
            sotish.master_summasi = master_summasi
            
            # GPS va SIM kartalarni saqlash
            sotish.gps_id.clear()
            valid_sim_kartalar = []
            
            for i, gps_id in enumerate(gps_ids):
                if gps_id:
                    gps = Sklad.objects.get(id=gps_id)
                    gps.sotildi_sotilmadi = True
                    gps.save()
                    sotish.gps_id.add(gps)
                    
                    # SIM kartani qo'shish
                    if i < len(sim_kartalar) and sim_kartalar[i].strip():
                        valid_sim_kartalar.append(sim_kartalar[i].strip())
            
            # SIM kartalarni vergul bilan ajratib saqlash
            sotish.sim_karta = ', '.join(valid_sim_kartalar)
            sotish.save()
            
            messages.success(request, "Ma'lumotlar muvaffaqiyatli yangilandi!")
            return redirect('sotish_list')
            
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
            return redirect('sotish_update', pk=pk)

class SotishDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        sotish = Sotish.objects.get(pk=pk)
        
        # Sklad bilan bog'liq GPSlarni qayta "sotilmadi" holatiga o'zgartirish
        gpslar = sotish.gps_id.all()
        gpslar.update(sotildi_sotilmadi=False)
        
        # Sotishni o'chirish
        sotish.delete()
        return redirect('sotish_list')
    
class RasxodListView(LoginRequiredMixin, View):
    def get(self, request):
        rasxodlar = Rasxod.objects.all()
        return render(request, 'rasxod.html', {'rasxod_list': rasxodlar})
      
class RasxodAddView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'rasxod.html')

    def post(self, request):
        rasxod_nomi = request.POST.get('rasxod_nomi')
        sana = request.POST.get('sana')
        summa = request.POST.get('summasi')

        # Rasxodni yaratish
        Rasxod.objects.create(
            rasxod_nomi=rasxod_nomi,
            sana=sana,
            summa=summa
        )

        return redirect('rasxod_list')
    
class RasxodUpdateView(LoginRequiredMixin, UpdateView):
    model = Rasxod
    fields = ['rasxod_nomi', 'sana', 'summa']
    template_name = 'rasxod_update.html'  
    success_url = reverse_lazy('rasxod_list')  
    
class RasxodDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        rasxod = Rasxod.objects.get(pk=pk)
        rasxod.delete()
        return redirect('rasxod_list')
    
class MijozlarView(LoginRequiredMixin, TemplateView):
    template_name = 'mijozlar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mijozlar = Sotish.objects.all().order_by('-sana')  # Sanaga ko'ra tartiblash

        mijozlar_data = []
        for mijoz in mijozlar:
            gpslar = mijoz.gps_id.all()
            sim_kartalar = mijoz.sim_karta.split(',') if mijoz.sim_karta else []
            
            # GPS va SIM kartalar uzunligini tenglashtirish
            while len(sim_kartalar) < len(gpslar):
                sim_kartalar.append('')
            
            # Har bir GPS va SIM karta uchun qator yaratish
            for i, (gps, sim) in enumerate(zip(gpslar, sim_kartalar)):
                mijozlar_data.append({
                    'id': mijoz.id,  # Mijoz ID si
                    'mijoz': mijoz.mijoz if i == 0 else '',
                    'tel_raqam': mijoz.mijoz_tel_raqam if i == 0 else '',
                    'username': mijoz.username if i == 0 else '',
                    'password': mijoz.password if i == 0 else '',
                    'dasturiy_taminot_nomi': str(mijoz.dasturiy_taminot) if mijoz.dasturiy_taminot and i == 0 else '',  # O'zgartirildi
                    'abonent_tulov': mijoz.abonent_tulov if i == 0 else '',
                    'sana': mijoz.sana.strftime('%Y-%m-%d') if mijoz.sana and i == 0 else '',
                    'summasi': mijoz.summasi if i == 0 else '',
                    'naqd': mijoz.naqd if i == 0 else '',
                    'bank_schot': mijoz.bank_schot if i == 0 else '',
                    'karta': mijoz.karta if i == 0 else '',
                    'master': mijoz.master if i == 0 else '',
                    'master_summasi': mijoz.master_summasi if i == 0 else '',
                    'gps': gps,
                    'sim_karta': sim,
                    'rowspan': len(gpslar) if i == 0 else 0,
                    'first_row': i == 0  # Birinchi qator uchun belgi
                })

        context['mijozlar_data'] = mijozlar_data
        return context

class StatistikaView(LoginRequiredMixin, TemplateView):
    template_name = 'statistika.html'
    oylar = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
             "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]

    def get_stats(self, month, year):
        """Berilgan oy va yil uchun statistikani hisoblash"""
        # O'tgan oy va yilni hisoblash
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year

        # Abonentlar statistikasi
        abonent_stats = {
            'oldingidagi_aktiv': Sotish.objects.filter(
                sana__year=prev_year,
                sana__month=prev_month
            ).count(),
            'oylik_qoshilgan': Sotish.objects.filter(
                sana__year=year,
                sana__month=month
            ).aggregate(gps_count=models.Count('gps_id'))['gps_count'],
            'jami_aktiv': Sotish.objects.filter(
                sana__year__lte=year,
                sana__month__lte=month if year == datetime.now().year else 12
            ).aggregate(gps_count=models.Count('gps_id'))['gps_count']
        }

        # To'lovlar statistikasi
        tolov_stats = {
            'oylik_tolamaganlar': Bugalteriya.objects.filter(
                yil=year,
                oy=self.oylar[month-1],
                abonent_tolov=False
            ).count(),
            'jami_tolamaganlar': Bugalteriya.objects.filter(
                models.Q(yil=year, oy__in=self.oylar[max(0, month-3):month]) |
                models.Q(yil=prev_year, oy__in=self.oylar[9:]) if month <= 3 else models.Q(),
                abonent_tolov=False
            ).values('sotish').distinct().count()
        }

        # GPS qurilmalari statistikasi
        gps_stats = {
            'otgan_oy_sklad': Sklad.objects.filter(
                olingan_sana__year=prev_year,
                olingan_sana__month=prev_month,
                sotildi_sotilmadi=False
            ).count(),
            'hozir_skladda_bor': Sklad.objects.filter(
                sotildi_sotilmadi=False
            ).count(),
            'oylik_sotilgan': Sklad.objects.filter(
                sotildi_sotilmadi=True,
                sotish__sana__year=year,
                sotish__sana__month=month
            ).count(),
            'jami_sotilgan': Sklad.objects.filter(
                sotildi_sotilmadi=True,
                sotish__sana__year__lte=year,
                sotish__sana__month__lte=month if year == datetime.now().year else 12
            ).count()
        }

        # SIM karta statistikasi
        sim_stats = {
            'oylik': Sotish.objects.filter(
                sana__year=year,
                sana__month=month
            ).annotate(
                sim_count=models.Func(
                    models.F('sim_karta'),
                    function='LENGTH',
                    template="(LENGTH(%(expressions)s) - LENGTH(REPLACE(%(expressions)s, ',', '')) + 1)"
                )
            ).aggregate(total_sim=models.Sum('sim_count'))['total_sim'] or 0
        }

        # Summalar statistikasi
        img_sotishlar = Sotish.objects.filter(
            sana__year=year,
            sana__month=month,
            dasturiy_taminot__dasturiy_taminot_nomi='IMG'
        ).prefetch_related('gps_id')
        
        summa_stats = {
            'img': {
                'jami': img_sotishlar.aggregate(total=models.Sum('summasi'))['total'] or 0,
                # Har bir mijozning GPS soniga qarab abonent to'lovni hisoblash
                'abonent': sum(sotish.abonent_tulov * len(sotish.gps_id.all()) for sotish in img_sotishlar)
            },
            'sinotrack': {
                'jami': Sotish.objects.filter(
                    sana__year=year,
                    sana__month=month,
                    dasturiy_taminot__dasturiy_taminot_nomi='Sinotrack'
                ).aggregate(total=models.Sum('summasi'))['total'] or 0
            },
            'oylik_abonent': Bugalteriya.objects.filter(
                yil=year,
                oy=self.oylar[month-1],
                abonent_tolov=True
            ).aggregate(total=models.Sum('sotish__abonent_tulov'))['total'] or 0
        }

        return {
            'abonent': abonent_stats,
            'tolov': tolov_stats,
            'gps': gps_stats,
            'sim': sim_stats,
            'summa': summa_stats,
            'oy': self.oylar[month-1]
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        now = datetime.now()
        selected_year = int(self.request.GET.get('year', now.year))
        
        # Har bir oy uchun statistika olish
        monthly_stats = {}
        current_month = now.month if selected_year == now.year else 12
        
        for month in range(1, current_month + 1):
            monthly_stats[month] = self.get_stats(month, selected_year)
        
        context.update({
            'monthly_stats': monthly_stats,
            'current_year': selected_year,
            'current_month': now.month,
            'yillar': range(2020, now.year + 1)
        })
        
        return context

class BugalteriyaView(LoginRequiredMixin, TemplateView):
    template_name = 'bugalteriya.html'
    oylar = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
             "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Joriy yilni olish
        now = datetime.now()
        selected_year = int(self.request.GET.get('yil', now.year))
        
        # Barcha sotishlarni va GPS larni bir so'rovda olish
        sotishlar = (Sotish.objects
                    .filter(sana__year=selected_year)
                    .prefetch_related('gps_id')
                    .order_by('-sana'))
        
        # Barcha to'lovlarni bir so'rovda olish
        tolovlar = (Bugalteriya.objects
                   .filter(sotish__in=sotishlar, yil=selected_year)
                   .select_related('sotish', 'gps'))
        
        # To'lovlarni xotiraga olish
        tolovlar_dict = {}
        for tolov in tolovlar:
            key = (tolov.sotish_id, tolov.gps_id, tolov.oy)
            tolovlar_dict[key] = tolov
        
        # Ma'lumotlarni tayyorlash
        bugalteriya_data = []
        for sotish in sotishlar:
            gps_data = []
            for gps in sotish.gps_id.all():
                oylik_tolovlar = {}
                for oy in self.oylar:
                    tolov = tolovlar_dict.get((sotish.id, gps.id, oy))
                    oylik_tolovlar[oy] = {
                        'abonent': {
                            'status': tolov.abonent_tolov if tolov else False,
                            'id': tolov.id if tolov else ''
                        },
                        'sim': {
                            'status': tolov.sim_karta_tolov if tolov else False,
                            'id': tolov.id if tolov else ''
                        }
                    }
                
                gps_data.append({
                    'gps': gps,
                    'tolovlar': oylik_tolovlar
                })
            
            bugalteriya_data.append({
                'sotish': sotish,
                'gps_data': gps_data
            })
        
        context.update({
            'bugalteriya_data': bugalteriya_data,
            'oylar': self.oylar,
            'current_year': selected_year,
            'years': range(2020, now.year + 1)
        })
        
        return context

class UpdateBugalteriyaView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            tolov_id = data.get('tolov_id')
            sotish_id = data.get('sotish_id')
            gps_id = data.get('gps_id')
            oy = data.get('oy')
            yil = data.get('yil')
            tolov_type = data.get('type')

            # Agar to'lov mavjud bo'lsa
            if tolov_id and tolov_id != 'null' and tolov_id != 'undefined':
                tolov = get_object_or_404(Bugalteriya, id=tolov_id)
                
                # Faqat super admin to'langan to'lovni o'zgartira oladi
                if tolov_type == 'abonent':
                    if tolov.abonent_tolov and not request.user.is_superuser:
                        return JsonResponse({
                            'status': False,
                            'message': "Faqat super admin to'langan to'lovni o'zgartira oladi"
                        })
                    tolov.abonent_tolov = not tolov.abonent_tolov
                else:  # sim karta to'lovi
                    if tolov.sim_karta_tolov and not request.user.is_superuser:
                        return JsonResponse({
                            'status': False,
                            'message': "Faqat super admin to'langan to'lovni o'zgartira oladi"
                        })
                    tolov.sim_karta_tolov = not tolov.sim_karta_tolov
            
            # Yangi to'lov yaratish
            else:
                if not all([sotish_id, gps_id, oy, yil]):
                    return JsonResponse({
                        'status': False,
                        'message': "To'lov uchun barcha ma'lumotlar to'liq emas"
                    })

                # Mavjud to'lovni tekshirish
                tolov = Bugalteriya.objects.filter(
                    sotish_id=sotish_id,
                    gps_id=gps_id,
                    oy=oy,
                    yil=yil
                ).first()

                # Agar to'lov mavjud bo'lmasa, yangi yaratish
                if not tolov:
                    sotish = get_object_or_404(Sotish, id=sotish_id)
                    gps = get_object_or_404(Sklad, id=gps_id)
                    tolov = Bugalteriya.objects.create(
                        sotish=sotish,
                        gps=gps,
                        oy=oy,
                        yil=yil,
                        abonent_tolov=False,
                        sim_karta_tolov=False
                    )

                # To'lov turini o'zgartirish
                if tolov_type == 'abonent':
                    tolov.abonent_tolov = True
                else:  # sim karta to'lovi
                    tolov.sim_karta_tolov = True

            # To'lovni saqlash
            tolov.save()

            return JsonResponse({
                'status': True,
                'tolov_id': tolov.id,
                'abonent_status': tolov.abonent_tolov,
                'sim_status': tolov.sim_karta_tolov
            })

        except Exception as e:
            return JsonResponse({
                'status': False,
                'message': str(e)
            })

class HodimListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'hodim.html'
    context_object_name = 'hodimlar'

    def get_queryset(self):
        queryset = super().get_queryset()
        for user in queryset:
            # raw_password ni user.password ga o'rnatamiz
            user.raw_password = user._password
        return queryset
    
class HodimCreateView(LoginRequiredMixin, CreateView):
    model = CustomUser
    form_class = HodimForm
    template_name = 'hodim.html'
    success_url = reverse_lazy('hodim-list')

class HodimUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = HodimForm
    template_name = 'hodim_update.html'
    success_url = reverse_lazy('hodim-list')

class HodimDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        hodim = get_object_or_404(CustomUser, pk=pk)
        hodim.delete()
        return redirect('hodim-list')
    
class NoteView(LoginRequiredMixin, View):
    def get(self, request):
        notes = Note.objects.all().order_by('-sana')
        return render(request, 'note.html', {'notes': notes})

class NoteAddView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'note.html') 
    
    def post(self, request):
        user = request.user
        note_content = request.POST.get('note')  
        if note_content:  
            note = Note(user=user, izoh=note_content)
            note.save() 
            return redirect('note-list') 
        return render(request, 'note.html', {'error': 'Please enter a note!'}) 

class NoteEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        note = get_object_or_404(Note, pk=pk)
        if note.user != request.user:
            return redirect('note-list')
        return render(request, 'note.html', {'note': note, 'is_edit': True})

    def post(self, request, pk):
        note = get_object_or_404(Note, pk=pk)
        if note.user != request.user:
            return redirect('note-list')
        note_content = request.POST.get('note')
        if note_content:
            note.izoh = note_content
            note.save()
            return redirect('note-list')
        return render(request, 'note.html', {'error': 'Please enter a note!', 'note': note, 'is_edit': True})

class NoteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        note = get_object_or_404(Note, pk=pk)
        if note.user != request.user:
            return redirect('note-list')
        note.delete()
        return redirect('note-list')
