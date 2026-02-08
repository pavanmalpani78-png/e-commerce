from django.contrib import admin
from .models import Customer, MilkOrder, MilkTransaction

admin.site.register(Customer)
admin.site.register(MilkOrder)
admin.site.register(MilkTransaction)
