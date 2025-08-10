# Register your models here.
from django.contrib import admin
from .models import Train, Coach, Defect

admin.site.register(Train)
admin.site.register(Coach)
admin.site.register(Defect)
