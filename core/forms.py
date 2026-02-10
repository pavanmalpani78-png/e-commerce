
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


from django import forms
from .models import MilkTransaction

class MilkTransactionForm(forms.ModelForm):
    class Meta:
        model = MilkTransaction
        fields = ["customer", "product_type", "qty", "unit", "rate", "payment_status", "note"]


        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_status": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


        
        
