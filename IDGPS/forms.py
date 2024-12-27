from django import forms
from .models import Sklad,Sotish
from datetime import date
class SkladForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = ['gps_is', 'olingan_odam', 'tel_raqam', 'summa_prixod', 'olingan_sana', 'sotildi_sotilmadi']
        widgets = {
            'gps_is': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'olingan_odam': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'tel_raqam': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '+998-XX-XXX-XX-XX'}),
            'summa_prixod': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'olingan_sana': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date',
                'value': date.today().strftime('%Y-%m-%d'),  
            }),
            'sotildi_sotilmadi': forms.CheckboxInput(attrs={
                'class': 'inline-flex items-center space-x-4', 
            }),
        }
class SotishForm(forms.ModelForm):
    class Meta:
        model = Sotish
        fields = ['gps_id', 'mijoz', 'mijoz_tel_raqam', 'sim_karta', 'dasturiy_taminot', 'username', 'tulov_sammasi', 'sana', 'summasi']
        widgets = {
            'gps_id': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'mijoz': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Mijoz ismini kiriting',
            }),
            'mijoz_tel_raqam': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Mijoz telefon raqamini kiriting',
            }),
            'sim_karta': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'SIM karta maʼlumotlarini kiriting',
            }),
            'dasturiy_taminot': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Dasturiy taʼminot haqida maʼlumot kiriting',
            }),
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Username kiriting',
            }),
            'tulov_sammasi': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'To‘lov summasini kiriting',
            }),
            'sana': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date',
            }),
            'summasi': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Summani kiriting',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat sotilmagan GPS qurilmalarni ko'rsatish uchun
        self.fields['gps_id'].queryset = Sklad.objects.filter(sotildi_sotilmadi=False)