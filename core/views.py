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

        if not customer_id or not product_type:
            return redirect("milk_order")

        if product_type == "MILK":
            brand = request.POST.get("brand")
            milk_type = request.POST.get("milk_type")
            pack_size = request.POST.get("pack_size")
            packets = request.POST.get("packets")

            MilkOrder.objects.create(
                customer_id=int(customer_id),
                product_type="MILK",
                brand=brand,
                milk_type=milk_type,
                pack_size=Decimal(str(pack_size)),
                packets=int(packets),
                quantity=Decimal("0"),
                unit="",
            )

        else:
            quantity = request.POST.get("quantity")
            unit = request.POST.get("unit")
            rate = request.POST.get("rate")

            MilkOrder.objects.create(
                customer_id=int(customer_id),
                product_type=product_type,
                quantity=Decimal(str(quantity)),
                unit=unit,
                rate=Decimal(str(rate)),
                brand=None,
                milk_type=None,
                pack_size=None,
                packets=0,
            )

        return redirect("milk_order")

    return render(request, "milk_order.html", {
        "customers": customers,
        "orders": orders,
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

            # ✅ If your field name is qty (renamed from liters)
            t.amount = Decimal(str(t.qty)) * Decimal(str(t.rate))

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

    # ✅ ALL products for that day
    orders = (
        MilkOrder.objects
        .filter(date=selected_date)
        .select_related("customer")
        .order_by("-id")
    )

    # ✅ total amount of all products
    totals = orders.aggregate(
        total_amount=Sum("total"),
        total_liters=Sum("total_liters"),   # only meaningful for milk
        total_qty=Sum("quantity"),         # meaningful for other products
    )

    # ✅ product wise summary
    product_summary = (
        orders.values("product_type")
        .annotate(amount=Sum("total"))
        .order_by("product_type")
    )

    return render(request, "daily_report.html", {
        "selected_date": selected_date,
        "orders": orders,
        "totals": totals,
        "product_summary": product_summary,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import Customer, MilkOrder


# 1️⃣ Bill home – select customer
def bill_select_customer(request):
    customers = Customer.objects.all().order_by("name")

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        return redirect("bill_view", customer_id=customer_id)

    return render(request, "bill_select_customer.html", {
        "customers": customers
    })


# 2️⃣ Bill view (HTML)
def bill_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    orders = MilkOrder.objects.filter(
        customer=customer
    ).order_by("-date", "-id")

    totals = orders.aggregate(
    total_liters=Sum("total_liters"),
    total_qty=Sum("quantity"),
    total_amount=Sum("total")
)

    return render(request, "bill_view.html", {
    "customer": customer,
    "orders": orders,
    "total_liters": totals["total_liters"] or 0,
    "total_qty": totals["total_qty"] or 0,
    "total_amount": totals["total_amount"] or 0,
})



# 3️⃣ Bill PDF (download)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import os

from .models import Customer, MilkOrder


def bill_pdf(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    orders = (
        MilkOrder.objects
        .filter(customer=customer)
        .order_by("date", "id")
    )

    totals = orders.aggregate(
        total_liters=Sum("total_liters"),
        total_amount=Sum("total"),
    )

    total_liters = totals["total_liters"] or 0
    grand_total = totals["total_amount"] or 0

    today = timezone.localdate()
    invoice_no = f"INV-{customer.id}-{today.strftime('%Y%m%d')}"

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{customer.name}_{today}.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # ---------- Helpers ----------
    def money(x):
        try:
            return f"₹ {float(x):.2f}"
        except Exception:
            return f"₹ {x}"

    # ---------- Header ----------
    y = height - 40

    # Header background bar
    c.setFillColorRGB(0.06, 0.25, 0.55)  # deep blue
    c.rect(0, height - 95, width, 95, stroke=0, fill=1)

    # Logo (optional)
    logo_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "logo.png")
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, height - 85, width=55, height=55, mask="auto")
        except Exception:
            pass

    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(110, height - 55, "MILK KHATA - INVOICE")

    c.setFont("Helvetica", 10)
    c.drawString(110, height - 73, "Dairy Orders Billing System")

    # Invoice meta (right)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 40, height - 55, f"Invoice No: {invoice_no}")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, height - 72, f"Date: {today}")

    # Reset fill
    c.setFillColor(colors.black)

    # ---------- Shop + Customer Box ----------
    y = height - 125

    # Box border
    c.setStrokeColor(colors.lightgrey)
    c.setFillColorRGB(0.97, 0.98, 1.0)
    c.rect(35, y - 90, width - 70, 90, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y - 25, "From (Shop)")
    c.drawString(width/2 + 10, y - 25, "Bill To (Customer)")

    c.setFont("Helvetica", 10)
    c.drawString(50, y - 42, "Milk Khata Dairy Store")
    c.drawString(50, y - 56, "Address: Your Shop Address")
    c.drawString(50, y - 70, "Phone: +91-XXXXXXXXXX")

    c.drawString(width/2 + 10, y - 42, f"Name: {customer.name}")
    c.drawString(width/2 + 10, y - 56, f"Phone: {customer.phone or '-'}")
    c.drawString(width/2 + 10, y - 70, f"Address: {customer.address or '-'}")

    y = y - 115

    # ---------- Table Header ----------
    table_left = 35
    table_right = width - 35
    row_h = 18

    columns = [
        ("Date", 55),
        ("Product", 90),
        ("Brand", 70),
        ("Pack", 45),
        ("Pkts", 40),
        ("Liters", 55),
        ("Total", 70),
    ]

    # Header background
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.rect(table_left, y, table_right - table_left, row_h + 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)

    x = table_left + 8
    for title, w in columns:
        c.drawString(x, y + 6, title)
        x += w

    y -= (row_h + 6)

    # ---------- Rows ----------
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.lightgrey)

    def new_page():
        nonlocal y
        c.showPage()
        # re-draw a simpler header on new page
        c.setFont("Helvetica-Bold", 14)
        c.drawString(35, height - 40, "MILK KHATA - INVOICE")
        c.setFont("Helvetica", 10)
        c.drawString(35, height - 55, f"Customer: {customer.name}    Invoice: {invoice_no}    Date: {today}")
        y = height - 90

        # table header again
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.rect(table_left, y, table_right - table_left, row_h + 6, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        x2 = table_left + 8
        for title, w in columns:
            c.drawString(x2, y + 6, title)
            x2 += w
        y -= (row_h + 6)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)

    alt = False
    for o in orders:
        if y < 140:
            new_page()

        # alternate row background
        if alt:
            c.setFillColorRGB(0.98, 0.99, 1.0)
            c.rect(table_left, y, table_right - table_left, row_h, stroke=0, fill=1)
        c.setFillColor(colors.black)
        alt = not alt

        x = table_left + 8
        c.drawString(x, y + 4, str(o.date)); x += columns[0][1]
        c.drawString(x, y + 4, str(o.product_type)); x += columns[1][1]
        c.drawString(x, y + 4, str(o.brand or "-")); x += columns[2][1]
        c.drawString(x, y + 4, str(o.pack_size or "-")); x += columns[3][1]
        c.drawString(x, y + 4, str(o.packets or 0)); x += columns[4][1]
        c.drawString(x, y + 4, str(o.total_liters or 0)); x += columns[5][1]
        c.drawString(x, y + 4, money(o.total or 0)); x += columns[6][1]

        # row bottom line
        c.setStrokeColor(colors.whitesmoke)
        c.line(table_left, y, table_right, y)
        y -= row_h

    # ---------- Totals Box ----------
    y -= 10
    if y < 120:
        new_page()

    c.setStrokeColor(colors.lightgrey)
    c.setFillColorRGB(0.97, 0.98, 1.0)
    c.rect(width - 240, y - 55, 205, 55, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(width - 230, y - 20, f"Total Liters: {total_liters}")
    c.drawString(width - 230, y - 40, f"Grand Total: {money(grand_total)}")

    # ---------- Footer / Signature ----------
    y -= 85
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawString(35, y, "Note: This is a system-generated invoice. Download and share via WhatsApp/Email.")
    y -= 25

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, y, "Authorized Signature")
    c.setStrokeColor(colors.black)
    c.line(width - 180, y - 5, width - 40, y - 5)

    c.showPage()
    c.save()
    return response
