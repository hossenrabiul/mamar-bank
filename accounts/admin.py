from django.contrib import admin
from . models import userBankAccount, UserAddress
# Register your models here.
admin.site.register(userBankAccount)
admin.site.register(UserAddress)
