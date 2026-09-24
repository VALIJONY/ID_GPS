from django.contrib import admin
from .models import *

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'firstname', 'last_name', 'position', 'is_staff', 'is_superuser']  # ko'rsatmoqchi bo'lgan maydonlar
    verbose_name = "Xodim"
    verbose_name_plural = "Xodimlar"

# Qolgan modellar
admin.site.register(Sklad)
admin.site.register(Rasxod)
admin.site.register(Sotish)
admin.site.register(DasturiyTaminot)
admin.site.register(Bugalteriya)
admin.site.register(Note)