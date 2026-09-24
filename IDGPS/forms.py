from datetime import date

from django import forms
from django.db.models import Q

from .models import CustomUser, Rasxod, Sklad, Sotish


class MoneyField(forms.IntegerField):
    """'1 250 000' yoki '1,250,000' ko'rinishidagi summani butun songa aylantiradi."""

    widget = forms.TextInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('min_value', 0)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            value = value.replace(' ', '').replace(' ', '').replace(',', '')
        return super().to_python(value)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.pop('min', None)
        attrs.update({'inputmode': 'numeric', 'data-money': '', 'autocomplete': 'off', 'placeholder': '0'})
        return attrs


class StyledFormMixin:
    """Har bir widgetga dizayn tizimidagi klassni qo'shadi va xatolikni belgilaydi."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            if isinstance(widget, forms.Textarea):
                css = 'textarea'
            elif isinstance(widget, forms.Select):
                css = 'select'
            else:
                css = 'input'
            widget.attrs['class'] = f"{css} {widget.attrs.get('class', '')}".strip()

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs['class'] = f"{widget.attrs.get('class', '')} is-invalid".strip()


def date_input():
    return forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class SkladForm(StyledFormMixin, forms.ModelForm):
    summa_prixod = MoneyField(label="Kirim narxi (1 dona)")

    class Meta:
        model = Sklad
        fields = ['gps_id', 'olingan_odam', 'tel_raqam', 'summa_prixod', 'olingan_sana']
        labels = {
            'gps_id': 'GPS ID',
            'olingan_odam': "Yetkazib beruvchi",
            'tel_raqam': 'Telefon raqam',
            'olingan_sana': 'Olingan sana',
        }
        widgets = {
            'gps_id': forms.TextInput(attrs={'placeholder': 'Masalan: 862095061234567', 'class': 'mono'}),
            'olingan_odam': forms.TextInput(attrs={'placeholder': "Ism familiya yoki kompaniya"}),
            'tel_raqam': forms.TextInput(attrs={'placeholder': '+998 90 123 45 67', 'inputmode': 'tel'}),
            'olingan_sana': date_input(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['olingan_sana'].initial = date.today()

    def clean_gps_id(self):
        gps_id = self.cleaned_data['gps_id'].strip()
        if self.instance.pk and gps_id == self.instance.gps_id:
            return gps_id
        duplicates = Sklad.objects.filter(gps_id=gps_id).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError(f"«{gps_id}» ID li GPS skladda allaqachon mavjud.")
        return gps_id


class SotishForm(StyledFormMixin, forms.ModelForm):
    gps_id = forms.ModelMultipleChoiceField(queryset=Sklad.objects.none(), required=False)
    abonent_tulov = MoneyField(label="Abonent to'lov (1 GPS, oyiga)")

    class Meta:
        model = Sotish
        fields = [
            'mijoz', 'mijoz_tel_raqam', 'sim_karta', 'dasturiy_taminot',
            'username', 'password', 'abonent_tulov', 'sana', 'master', 'gps_id'
        ]
        labels = {
            'mijoz': 'Mijoz',
            'mijoz_tel_raqam': 'Telefon raqam',
            'dasturiy_taminot': "Dasturiy ta'minot",
            'username': 'Platforma logini',
            'password': 'Platforma paroli',
            'sana': 'Sotuv sanasi',
            'master': "O'rnatuvchi usta",
        }
        widgets = {
            'mijoz': forms.TextInput(attrs={'placeholder': "Ism familiya yoki tashkilot"}),
            'mijoz_tel_raqam': forms.TextInput(attrs={'placeholder': '+998 90 123 45 67', 'inputmode': 'tel'}),
            'sim_karta': forms.HiddenInput(),
            'username': forms.TextInput(attrs={'autocomplete': 'off', 'class': 'mono'}),
            'password': forms.TextInput(attrs={'autocomplete': 'off', 'class': 'mono'}),
            'sana': date_input(),
            'master': forms.TextInput(attrs={'placeholder': 'Usta ismi'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # SIM kartalar alohida qatorlarda keladi va view'da yig'iladi
        self.fields['sim_karta'].required = False
        self.fields['dasturiy_taminot'].empty_label = 'Tanlang…'
        if self.instance.pk:
            self.fields['gps_id'].queryset = Sklad.objects.filter(
                Q(sotildi_sotilmadi=False) | Q(id__in=self.instance.gps_id.all())
            )
        else:
            self.fields['sana'].initial = date.today()
            self.fields['gps_id'].queryset = Sklad.objects.filter(sotildi_sotilmadi=False)


class RasxodForm(StyledFormMixin, forms.ModelForm):
    summa = MoneyField(label='Summa')

    class Meta:
        model = Rasxod
        fields = ['rasxod_nomi', 'sana', 'summa']
        labels = {'rasxod_nomi': 'Rasxod nomi', 'sana': 'Sana'}
        widgets = {
            'rasxod_nomi': forms.Textarea(attrs={'rows': 3, 'placeholder': "Masalan: SIM kartalar uchun to'lov, ofis ijarasi…"}),
            'sana': date_input(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rasxod_nomi'].widget.attrs['style'] = 'min-height:96px'
        if not self.instance.pk:
            self.fields['sana'].initial = date.today()


class HodimForm(StyledFormMixin, forms.ModelForm):
    password = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': '••••••••'}),
    )

    class Meta:
        model = CustomUser
        fields = ['firstname', 'last_name', 'position', 'username', 'password', 'is_staff']
        labels = {
            'firstname': 'Ism',
            'last_name': 'Familiya',
            'position': 'Lavozim',
            'username': 'Login',
            'is_staff': "Hodimlarni boshqarish huquqi",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ''
        if self.instance.pk:
            # Tahrirlashda parol ixtiyoriy: bo'sh qolsa eskisi saqlanadi
            self.fields['password'].required = False
            self.fields['password'].help_text = "O'zgartirmaslik uchun bo'sh qoldiring"
            self.fields['password'].widget.attrs['placeholder'] = "O'zgarmaydi"

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password and self.instance.pk:
            return CustomUser.objects.get(pk=self.instance.pk).password
        if password and len(password) < 4:
            raise forms.ValidationError("Parol kamida 4 ta belgidan iborat bo'lsin.")
        return password
