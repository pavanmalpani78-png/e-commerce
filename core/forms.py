
from django import forms
from .models import Customer, MilkOrder, MilkTransaction


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "address"]


# class MilkOrderForm(forms.ModelForm):
#     class Meta:
#         model = MilkOrder
#         fields = ["customer", "milk_type", "quantity", "rate"]


class MilkTransactionForm(forms.ModelForm):
    class Meta:
        model = MilkTransaction
        # fields = ["customer", "liters", "rate", "transaction_type", "note"]
        # fields = ["customer", "liters", "rate", "payment_status", "note"]
        fields = ["customer", "liters", "rate", "payment_status", "note"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "balance": forms.NumberInput(attrs={"class": "form-control"}),
        }



        
        
