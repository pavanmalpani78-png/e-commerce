from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, MilkOrder, MilkTransaction
# from .forms import CustomerForm, MilkTransactionForm
from decimal import Decimal
from .forms import CustomerForm, MilkTransactionForm




from django.shortcuts import render, redirect

def dashboard(request):
    return render(request, "dashboard.html")   # front page

def home(request):
    return render(request, "home.html")        # main page

def login_page(request):
    if request.method == "POST":
        return redirect("home")                # ✅ after login go home
    return render(request, "login.html")

def signup_page(request):
    if request.method == "POST":
        return redirect("home")                # ✅ after signup go home
    return render(request, "signup.html")

# hisab_kitab_app/views.py
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def customer(request):
    return render(request, 'customer.html')

def order_page(request):
    return render(request, "milk_order.html")  # or order.html if you want, but same page




# ---------------- CUSTOMER ----------------
def customer_page(request):
    customers = Customer.objects.all()
    return render(request, "customer.html", {"customers": customers})


def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("customer_page")
    else:
        form = CustomerForm()
    return render(request, "add_customer.html", {"form": form})


def edit_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.phone = request.POST.get("phone")
        customer.address = request.POST.get("address")
        customer.balance = request.POST.get("balance")
        customer.save()
        return redirect("customer_page")
    return render(request, "edit_customer.html", {"customer": customer})


def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    customer.delete()
    return redirect("customer_page")




# ---------------- MILK ORDERS (MilkOrder model) ----------------
from decimal import Decimal
from django.shortcuts import render, redirect
from .models import Customer, MilkOrder

def milk_order_view(request):
    customers = Customer.objects.all()
    orders = MilkOrder.objects.select_related("customer").order_by("-date", "-id")

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        product_type = request.POST.get("product_type")

        if product_type == "MILK":
            MilkOrder.objects.create(
                customer_id=int(customer_id),
                product_type="MILK",
                brand=request.POST.get("brand"),
                milk_type=request.POST.get("milk_type"),   # ✅ NOW VALID
                pack_size=Decimal(request.POST.get("pack_size")),
                packets=int(request.POST.get("packets")),
            )
        else:
            MilkOrder.objects.create(
                customer_id=int(customer_id),
                product_type=product_type,
                quantity=Decimal(request.POST.get("quantity")),
                unit=request.POST.get("unit"),
                rate=Decimal(request.POST.get("rate")),
            )

        return redirect("milk_order")

    return render(request, "milk_order.html", {
        "customers": customers,
        "orders": orders
    })



# ---------------- MILK TRANSACTIONS (MilkTransaction model) ----------------
from django.shortcuts import render, redirect
from django.http import JsonResponse
from decimal import Decimal
from .models import MilkTransaction, MilkOrder
from .forms import MilkTransactionForm


def transaction_page(request):
    transactions = MilkTransaction.objects.select_related("customer").order_by("-date", "-id")
    return render(request, "transaction.html", {"transactions": transactions})


def add_transaction(request):
    if request.method == "POST":
        form = MilkTransactionForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            # amount auto (liters * rate)
            t.amount = Decimal(str(t.liters)) * Decimal(str(t.rate))
            t.save()
            return redirect("transaction_page")
    else:
        form = MilkTransactionForm()

    return render(request, "add_transaction.html", {"form": form})


def customer_last_milk(request):
    """
    When user selects customer, this API returns latest milk order liters + rate
    """
    customer_id = request.GET.get("customer_id")
    if not customer_id:
        return JsonResponse({"ok": False, "liters": 0, "rate": 0})

    order = (
        MilkOrder.objects.filter(customer_id=customer_id, product_type="MILK")
        .order_by("-date", "-id")
        .first()
    )

    if not order or order.total_liters == 0:
        return JsonResponse({"ok": True, "liters": 0, "rate": 0})

    rate_per_liter = Decimal(str(order.total)) / Decimal(str(order.total_liters))

    return JsonResponse({
        "ok": True,
        "liters": float(order.total_liters),
        "rate": float(rate_per_liter),
    })

from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render
from .models import MilkOrder

def daily_milk_report(request):
    selected_date = request.GET.get("date") or timezone.localdate().isoformat()

    orders = MilkOrder.objects.filter(
        product_type="MILK",
        date=selected_date
    ).select_related("customer").order_by("-id")

    totals = orders.aggregate(
        total_liters=Sum("total_liters"),
        total_amount=Sum("total"),
    )

    return render(request, "daily_report.html", {
        "selected_date": selected_date,
        "orders": orders,
        "totals": totals,
    })
