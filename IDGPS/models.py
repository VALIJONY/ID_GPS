from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

# Pozitsiyalar uchun choices
POSITION_CHOICES = [
    ('Menejer', 'Meneger'),
    ('Xodim', 'Xodim'),
    ('Direktor', 'Direktor'),
    ('Sotuvchi', 'Sotuvchi'),
]

# Custom User Model
class CustomUser(AbstractUser):
    firstname = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,  
        default='Xodim',  
    )
    username=models.CharField(unique=True,max_length=50)
    password=models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)


    def __str__(self):
        return f'{self.firstname} {self.last_name}'

# Sklad Model
class Sklad(models.Model):
    gps_is = models.CharField(max_length=255)
    olingan_odam = models.CharField(max_length=255)
    tel_raqam = models.CharField(max_length=15)
    summa_prixod = models.BigIntegerField()
    olingan_sana = models.DateField()
    sotildi_sotilmadi = models.BooleanField(null=True)

    def __str__(self):
        return f'{self.gps_is} - {self.olingan_odam}'

# Rasxod Model
class Rasxod(models.Model):
    rasxod_nomi = models.TextField()
    sana = models.DateField()
    summa = models.BigIntegerField()

    def __str__(self):
        return f'{self.rasxod_nomi} - {self.sana}'

# Sotish Model
class Sotish(models.Model):
    gps_id = models.ManyToManyField(Sklad) 
    mijoz = models.CharField(max_length=255)
    mijoz_tel_raqam = models.CharField(max_length=15)
    sim_karta = models.CharField(max_length=20)
    dasturiy_taminot = models.CharField(max_length=255)
    username = models.CharField(max_length=100)
    tulov_sammasi = models.BigIntegerField()
    sana = models.DateField()
    summasi = models.BigIntegerField()

    def __str__(self):
        return f'{self.mijoz} - {self.sana}'



class Bugalteriya(models.Model):
    sotish = models.ForeignKey('Sotish', on_delete=models.CASCADE)  # Sotish modeli bilan bog'lanish
    
    oy = models.CharField(max_length=15, choices=[
        ("Yanvar", "Yanvar"), ("Fevral", "Fevral"), ("Mart", "Mart"),
        ("Aprel", "Aprel"), ("May", "May"), ("Iyun", "Iyun"),
        ("Iyul", "Iyul"), ("Avgust", "Avgust"), ("Sentabr", "Sentabr"),
        ("Oktabr", "Oktabr"), ("Noyabr", "Noyabr"), ("Dekabr", "Dekabr"),
    ])
    yil = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(datetime.now().year)],
        help_text="Yil 2000 va hozirgi yil orasida bo'lishi kerak."
    )
    abonent_tolov = models.BooleanField(default=False)  # Abonent to‘lovi
    sim_karta_tolov = models.BooleanField(default=False)  # Sim karta uchun to‘lov
    izoh = models.TextField(blank=True, null=True)  # Hisobot yoki eslatma uchun

    def __str__(self):
        return f"{self.sotish} - {self.oy} {self.yil}"

    class Meta:
        unique_together = ('sotish', 'oy', 'yil')
        verbose_name_plural = "Bugalteriya hisobotlari"
