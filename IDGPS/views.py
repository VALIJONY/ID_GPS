from django.urls import reverse_lazy
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login,logout
from .models import Bugalteriya, CustomUser, Rasxod,Sklad, Sotish
from django.views import View
from .forms import SkladForm,SotishForm
from django.views.generic import UpdateView,DeleteView,TemplateView
class Loginview(LoginView):
    template_name = 'login.html'  

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
        # Login muvaffaqiyatsiz bo'lsa
        return self.render_to_response(
            self.get_context_data(
                form=form,
                message="Invalid username or password"
            )
        )

class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect('login') 
        response.delete_cookie('access_token') 
        return response


class Home(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'base.html', {'user': request.user})
    
    
class SkladView(View):
    def get(self,request):
        sklad_list=Sklad.objects.all().order_by('-olingan_sana')
        return render(request,'sklad.html',{'skladlist':sklad_list})
    
    
class SkladAddView(View):
    def get(self, request):
        form = SkladForm()
        return render(request, 'sklad.html', {'form': form})

    def post(self, request):
        form = SkladForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sklad-list')  
        return render(request, 'sklad.html', {'form': form,'message':'saqlanmadi'})
    


def sklad_list(request):
    status_filter = request.GET.get('status', '')
    skladlist = Sklad.objects.all()

    if status_filter == 'sold':
        skladlist = skladlist.filter(sotildi_sotilmadi=True)
    elif status_filter == 'unsold':
        skladlist = skladlist.filter(sotildi_sotilmadi=False)
        
    skladlist = skladlist.order_by('-olingan_sana')
    return render(request, 'sklad.html', {'skladlist': skladlist})


class SotishListView(View):
    def get(self, request):
        sotish_items = Sotish.objects.all().order_by('-sana')  # Sana bo'yicha tartiblangan ro'yxat
        return render(request, 'sotish.html', {'sotish_items': sotish_items})

class SotishAddView(View):
    def get(self, request):
        gps_list = Sklad.objects.filter(sotildi_sotilmadi=False)
        return render(request, 'sotish.html', {'gps_list': gps_list})

    def post(self, request):
        # POST parametrlarini olish
        mijoz = request.POST.get('mijoz')
        mijoz_tel_raqam = request.POST.get('mijoz_tel_raqam')
        sim_karta = request.POST.get('sim_karta')
        dasturiy_taminot = request.POST.get('dasturiy_taminot')
        username = request.POST.get('username')
        tulov_sammasi = request.POST.get('tulov_sammasi')
        sana = request.POST.get('sana')
        summasi = request.POST.get('summasi')

        # gps_id[] larni olish (bu GPS IDlar ro'yxati bo'ladi)
        gps_ids = request.POST.getlist('gps_id[]')

        # Sotish ob'ektini yaratish
        sotish = Sotish.objects.create(
            mijoz=mijoz,
            mijoz_tel_raqam=mijoz_tel_raqam,
            sim_karta=sim_karta,
            dasturiy_taminot=dasturiy_taminot,
            username=username,
            tulov_sammasi=tulov_sammasi,
            sana=sana,
            summasi=summasi
        )

        # GPSlarni qo'shish va ularning sotilmaganligini yangilash
        for gps_id in gps_ids:
            gps = Sklad.objects.get(id=gps_id)  # GPSni olish
            sotish.gps_id.add(gps)  # GPSni sotishga qo'shish
            gps.sotildi_sotilmadi = True  # GPSni sotilgan deb belgilash
            gps.save()  # GPSni saqlash

        return redirect('sotish_list')


class SotishUpdateView(View):
    def get(self, request, pk):
        sotish = Sotish.objects.get(pk=pk)
        skladdan_olingan = sotish.gps_id.all()  # Hozirgi tanlangan GPSlar
        mavjud_gpslar = Sklad.objects.filter(sotildi_sotilmadi=False)  # Faqat sotilmagan GPSlar

        return render(request, 'sotish_update.html', {
            'sotish': sotish,
            'skladdan_olingan': skladdan_olingan,
            'mavjud_gpslar': mavjud_gpslar
        })

    def post(self, request, pk):
        sotish = Sotish.objects.get(pk=pk)
        gps_ids = request.POST.get("gps_ids", "").split(",")
        gps_ids = [int(gps_id) for gps_id in gps_ids if gps_id.strip().isdigit()]
        
        # Eski GPSlarni sotilmagan holatga qaytarish
        eski_gpslar = sotish.gps_id.all()
        for gps in eski_gpslar:
            gps.sotildi_sotilmadi = False
            gps.save()

        yangi_gpslar = Sklad.objects.filter(id__in=gps_ids)
        sotish.gps_id.set(yangi_gpslar)

        for gps in yangi_gpslar:
            gps.sotildi_sotilmadi = True
            gps.save()

        sotish.save()


        # Qo‘shimcha maydonlarni yangilash
        sotish.mijoz = request.POST['mijoz']
        sotish.mijoz_tel_raqam = request.POST['mijoz_tel_raqam']
        sotish.sim_karta = request.POST['sim_karta']
        sotish.dasturiy_taminot = request.POST['dasturiy_taminot']
        sotish.username = request.POST['username']
        sotish.tulov_sammasi = request.POST['tulov_sammasi']
        sotish.sana = request.POST['sana']
        sotish.summasi = request.POST['summasi']
        sotish.save()

        return redirect('sotish_list') 
    
        
class SotishDeleteView(View):
    def post(self, request, pk):
        sotish = Sotish.objects.get(pk=pk)
        
        # Sklad bilan bog'liq GPSlarni qayta "sotilmadi" holatiga o'zgartirish
        gpslar = sotish.gps_id.all()
        gpslar.update(sotildi_sotilmadi=False)
        
        # Sotishni o'chirish
        sotish.delete()
        return redirect('sotish_list')
    
class RasxodListView(View):
    def get(self, request):
        rasxodlar = Rasxod.objects.all()
        return render(request, 'rasxod.html', {'rasxod_list': rasxodlar})
      
class RasxodAddView(View):
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
    
class RasxodUpdateView(UpdateView):
    model = Rasxod
    fields = ['rasxod_nomi', 'sana', 'summa']
    template_name = 'rasxod_update.html'  
    success_url = reverse_lazy('rasxod_list')  
    
class RasxodDeleteView(View):
    def get(self, request, pk):
        rasxod = Rasxod.objects.get(pk=pk)
        rasxod.delete()
        return redirect('rasxod_list')
    
class MijozlarView(TemplateView):
    template_name = 'mijozlar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mijozlar = Sotish.objects.all()

        mijozlar_data = []
        for mijoz in mijozlar:
            gpslar = mijoz.gps_id.all()  # Mijozga tegishli GPSlar
            sim_kartalar = mijoz.sim_karta.split(',') if mijoz.sim_karta else []

            # Rowspan qiymatini aniqlash
            row_count = max(len(gpslar), len(sim_kartalar))  # GPS va SIM-kartalar sonining maksimal qiymati
            for i, gps in enumerate(gpslar):
                mijozlar_data.append({
                    'mijoz': mijoz.mijoz if i == 0 else '',  # Faqat birinchi qator uchun
                    'tel_raqam': mijoz.mijoz_tel_raqam if i == 0 else '',  # Faqat birinchi qator uchun
                    'username': mijoz.username if i == 0 else '',  # Faqat birinchi qator uchun
                    'dasturiy_taminot': mijoz.dasturiy_taminot if i == 0 else '',  # Faqat birinchi qator uchun
                    'tulov_sammasi': mijoz.tulov_sammasi if i == 0 else '',  # Faqat birinchi qator uchun
                    'gps': gps.gps_is,
                    'sim_karta': sim_kartalar[i] if i < len(sim_kartalar) else '',
                    'rowspan': row_count if i == 0 else 0,  # Faqat birinchi qator uchun rowspan qiymati
                })

        context['mijozlar_data'] = mijozlar_data
        return context

class BugalteriyaTableView(TemplateView):
    template_name = "bugalteriya.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Hozirgi yilni olish yoki GET so'rovdan yilni o'qish
        yil = self.request.GET.get('yil', datetime.now().year)
        oylar = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", 
            "Iyun", "Iyul", "Avgust", "Sentabr", 
            "Oktabr", "Noyabr", "Dekabr"
        ]
        
        # Barcha mijozlar va GPSlar bo'yicha ma'lumotni yig'ish
        sotishlar = Sotish.objects.prefetch_related('gps_id').all()
        jadval = []
        
        for sotish in sotishlar:
            gps_ids = sotish.gps_id.all()  # ManyToMany GPSlar
            for gps in gps_ids:
                satr = {"mijoz_ismi": sotish.mijoz, "gps_id": gps.gps_is, "oylar": []}
                for oy in oylar:
                    hisobot = Bugalteriya.objects.filter(
                        sotish=sotish, yil=yil, oy=oy).first()
                    satr["oylar"].append({
                        "abonent_tolov": hisobot.abonent_tolov if hisobot else False,
                        "sim_karta_tolov": hisobot.sim_karta_tolov if hisobot else False,
                        "oy": oy,
                        "hisobot_id": hisobot.id if hisobot else None,
                    })
                jadval.append(satr)
        
        # Context uchun ma'lumotlar
        context["jadval"] = jadval
        context["oylar"] = oylar
        context["yil"] = yil
        return context
    
class MultiMonthBugalteriyaCreateView(View):
    template_name = 'bugalteriya.html'  # Form ko'rinishi uchun shablon

    def get(self, request, *args, **kwargs):
        sotishlar = Sotish.objects.all()  # Mijozlar va gpslarni olish
        oylar = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
            "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
        ]
        return render(request, self.template_name, {'sotishlar': sotishlar,'oylar': oylar})

    def post(self, request, *args, **kwargs):
        # Post orqali yuborilgan ma'lumotlarni olish
        sotish_id = request.POST.get('sotish')  # Sotish ID
        oylars = request.POST.getlist('oylar')  # Tanlangan oylarning ro'yxati
        yil = request.POST.get('yil', datetime.now().year)  # Yil, standart hozirgi yil
        abonent_tolov = request.POST.get('abonent_tolov') == 'on'  # Abonent to‘lovi
        sim_karta_tolov = request.POST.get('sim_karta_tolov') == 'on'  # Sim karta to‘lovi

        sotish = Sotish.objects.get(id=sotish_id)  # Sotish obyektini olish

        # Har bir tanlangan oy uchun yangi yozuv yaratish
        for oy in oylars:
            if not Bugalteriya.objects.filter(sotish=sotish, oy=oy, yil=yil).exists():
                Bugalteriya.objects.create(
                    sotish=sotish,
                    oy=oy,
                    yil=yil,
                    abonent_tolov=abonent_tolov,
                    sim_karta_tolov=sim_karta_tolov
                )   

        return redirect(reverse_lazy('bugalteriya'))  # Yaratilgandan so'ng listga qaytarish


from django.shortcuts import render, redirect, get_object_or_404

class MultiMonthBugalteriyaUpdateView(View):
    template_name = 'bugalteriya_update.html'

    def get(self, request, *args, **kwargs):
        sotishlar = Sotish.objects.all()
        oylar = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
            "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
        ]
        return render(request, self.template_name, {'sotishlar': sotishlar, 'oylar': oylar})

    def post(self, request, *args, **kwargs):
        sotish_id = request.POST.get('sotish')
        oylar = request.POST.getlist('oylar')  # Yangilanishi kerak bo‘lgan oylardan iborat ro'yxat
        yil = int(request.POST.get('yil'))
        abonent_tolov = request.POST.get('abonent_tolov') == 'on'
        sim_karta_tolov = request.POST.get('sim_karta_tolov') == 'on'

        sotish = get_object_or_404(Sotish, id=sotish_id)
        for oy in oylar:
            # Yozuvni topib, yangilash
            Bugalteriya.objects.filter(sotish=sotish, oy=oy, yil=yil).update(
                abonent_tolov=abonent_tolov,
                sim_karta_tolov=sim_karta_tolov
            )
        return redirect('bugalteriya')  
