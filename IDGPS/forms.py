from django import forms
from .models import Sotish, Sklad, DasturiyTaminot, CustomUser
from datetime import date
from django.db.models import Q

class SkladForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = ['gps_id', 'olingan_odam', 'tel_raqam', 'summa_prixod', 'olingan_sana']
        widgets = {
            'gps_id': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'olingan_odam': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'tel_raqam': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'summa_prixod': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'olingan_sana': forms.DateInput(attrs={
                'value': date.today(),
                'type': 'date',
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
        }

class SotishForm(forms.ModelForm):
    gps_id = forms.ModelMultipleChoiceField(
        queryset=Sklad.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sana'].initial = date.today()
        instance = kwargs.get('instance')
        if instance:
            # Tahrirlash uchun - mavjud GPS va sotilmagan GPS lar
            self.fields['gps_id'].queryset = Sklad.objects.filter(
                Q(sotildi_sotilmadi=False) | Q(id__in=instance.gps_id.all())
            )
            self.fields['gps_id'].initial = instance.gps_id.all()
        else:
            # Yangi yaratish uchun - faqat sotilmagan GPS lar
            self.fields['gps_id'].queryset = Sklad.objects.filter(sotildi_sotilmadi=False)
    
    class Meta:
        model = Sotish
        fields = [
            'mijoz', 'mijoz_tel_raqam', 'sim_karta', 'dasturiy_taminot',
            'username', 'password', 'abonent_tulov', 'sana', 'master', 'gps_id'
        ]
        widgets = {
            'sim_karta': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'mijoz': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'mijoz_tel_raqam': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'dasturiy_taminot': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'password': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'abonent_tulov': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'sana': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'master': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
        }

class HodimForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['firstname', 'last_name', 'position', 'username', 'password', 'is_staff']
        widgets = {
            'firstname': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'position': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500',
                'id': 'password-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-sky-600 focus:ring-sky-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs['placeholder'] = 'Parolni kiriting'
        self.fields['password'].widget.attrs['class'] = 'mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500'
        self.fields['password'].widget.attrs['type'] = 'password'
