from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from django.contrib import messages

from .models import Customer, MilkOrder, MilkTransaction
from .forms import CustomerForm, MilkTransactionForm

def D(x, default="0"):
    try:
        if x is None:
            return Decimal(default)
        x = str(x).strip()
        if x == "":
            return Decimal(default)
        return Decimal(x)
    except (InvalidOperation, ValueError):
        return Decimal(default)

# ---------- BASIC PAGES ----------
def dashboard(request):
    return render(request, "dashboard.html")

def home(request):
    return render(request, "home.html")

def login_page(request):
    if request.method == "POST":
        return redirect("home")
    return render(request, "login.html")

def signup_page(request):
    if request.method == "POST":
        return redirect("home")
    return render(request, "signup.html")

def terms_page(request):
    return render(request, "terms.html")

# ---------- CUSTOMER CRUD (SHOPKEEPER) ----------
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
        customer.balance = request.POST.get("balance") or 0
        customer.save()
        return redirect("customer_page")
    return render(request, "edit_customer.html", {"customer": customer})

def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    customer.delete()
    return redirect("customer_page")

# ---------- MILK ORDER (SHOPKEEPER) ----------
def milk_order(request):
    customers = Customer.objects.all().order_by("name")

    selected_date = request.GET.get("date")
    if selected_date:
        orders = MilkOrder.objects.filter(date=selected_date).order_by("-id")
    else:
        selected_date = timezone.localdate().isoformat()
        orders = MilkOrder.objects.filter(date=selected_date).order_by("-id")

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        product_type = request.POST.get("product_type")

        date_str = request.POST.get("date") or selected_date

        brand = request.POST.get("brand") or None
        milk_type = request.POST.get("milk_type") or None
        pack_size = request.POST.get("pack_size") or None
        packets = request.POST.get("packets") or 0

        quantity = request.POST.get("quantity") or 0
        unit = request.POST.get("unit") or ""
        rate = request.POST.get("rate") or 0

        obj = MilkOrder(
            customer_id=customer_id,
            product_type=product_type,
            date=date_str,
            brand=brand,
            milk_type=milk_type,
            pack_size=pack_size,
            packets=packets,
            quantity=quantity,
            unit=unit,
            rate=rate,
            placed_by="SHOPKEEPER",
            status="APPROVED",
        )
        obj.save()
        return redirect(f"/milkorder/?date={date_str}")

    return render(request, "milk_order.html", {
        "customers": customers,
        "orders": orders,
        "selected_date": selected_date,
    })

def edit_order(request, pk):
    order = get_object_or_404(MilkOrder, pk=pk)
    customers = Customer.objects.all().order_by("name")

    if request.method == "POST":
        order.customer_id = request.POST.get("customer")
        order.product_type = request.POST.get("product_type")
        order.date = request.POST.get("date") or order.date

        if order.product_type == "MILK":
            order.brand = request.POST.get("brand") or None
            order.milk_type = request.POST.get("milk_type") or None
            order.pack_size = request.POST.get("pack_size") or None
            order.packets = int(request.POST.get("packets") or 0)

            order.quantity = Decimal("0")
            order.unit = ""
            order.rate = Decimal("0")
        else:
            order.quantity = D(request.POST.get("quantity"), "0")
            order.unit = request.POST.get("unit") or "KG"
            order.rate = D(request.POST.get("rate"), "0")

            order.brand = None
            order.milk_type = None
            order.pack_size = None
            order.packets = 0

        order.save()
        return redirect(f"/milkorder/?date={order.date}")

    return render(request, "edit_order.html", {"order": order, "customers": customers})

def delete_order(request, pk):
    order = get_object_or_404(MilkOrder, pk=pk)
    d = order.date
    order.delete()
    return redirect(f"/milkorder/?date={d}")

# ---------- TRANSACTIONS ----------
def transaction_page(request):
    transactions = MilkTransaction.objects.select_related("customer").order_by("-date", "-id")
    return render(request, "transaction.html", {"transactions": transactions})

def add_transaction(request):
    if request.method == "POST":
        form = MilkTransactionForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.amount = D(t.qty, "0") * D(t.rate, "0")
            t.save()
            return redirect("transaction_page")
    else:
        form = MilkTransactionForm()
    return render(request, "add_transaction.html", {"form": form})

# API auto-fill
def customer_last_milk(request):
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
    return JsonResponse({"ok": True, "liters": float(order.total_liters), "rate": float(rate_per_liter)})

# ---------- DAILY REPORT ----------
def daily_milk_report(request):
    selected_date = request.GET.get("date") or timezone.localdate().isoformat()

    orders = (
        MilkOrder.objects
        .filter(date=selected_date)
        .select_related("customer")
        .order_by("-id")
    )

    totals = orders.aggregate(
        total_amount=Sum("total"),
        total_liters=Sum("total_liters"),
        total_qty=Sum("quantity"),
    )

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

# ---------- BILL (HTML + PDF) ----------
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import os

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

    orders = MilkOrder.objects.filter(customer=customer).order_by("-date", "-id")

    totals = orders.aggregate(
        total_liters=Sum("total_liters"),
        total_qty=Sum("quantity"),
        total_amount=Sum("total"),
    )

    return render(request, "bill_view.html", {
        "customer": customer,
        "orders": orders,
        "total_liters": totals["total_liters"] or 0,
        "total_qty": totals["total_qty"] or 0,
        "total_amount": totals["total_amount"] or 0,
    })


# 3️⃣ Bill PDF (download)
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

    def money(x):
        try:
            return f"₹ {float(x):.2f}"
        except Exception:
            return f"₹ {x}"

    # ---------- Header ----------
    c.setFillColorRGB(0.06, 0.25, 0.55)
    c.rect(0, height - 95, width, 95, stroke=0, fill=1)

    # optional logo
    logo_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "logo.png")
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, height - 85, width=55, height=55, mask="auto")
        except Exception:
            pass

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(110, height - 55, "MILK KHATA - INVOICE")

    c.setFont("Helvetica", 10)
    c.drawString(110, height - 73, "Dairy Orders Billing System")

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 40, height - 55, f"Invoice No: {invoice_no}")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, height - 72, f"Date: {today}")

    c.setFillColor(colors.black)

    # ---------- Shop + Customer ----------
    y = height - 125
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

    # ---------- Table ----------
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

    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.rect(table_left, y, table_right - table_left, row_h + 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)

    x = table_left + 8
    for title, w in columns:
        c.drawString(x, y + 6, title)
        x += w

    y -= (row_h + 6)

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)

    def new_page():
        nonlocal y
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(35, height - 40, "MILK KHATA - INVOICE")
        c.setFont("Helvetica", 10)
        c.drawString(35, height - 55, f"Customer: {customer.name}    Invoice: {invoice_no}    Date: {today}")
        y = height - 90

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

        y -= row_h

    # ---------- Totals ----------
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

    c.showPage()
    c.save()
    return response

# ---------- CUSTOMER PANEL ----------
def customer_home(request):
    return render(request, "customer_panel/home.html")

def customer_login(request):
    if request.method == "POST":
        phone = (request.POST.get("phone") or "").strip()
        password = (request.POST.get("password") or "").strip()

        customer = Customer.objects.filter(login_phone=phone, login_password=password).first()
        if not customer:
            messages.error(request, "Invalid phone or password")
            return redirect("customer_login")

        request.session["customer_id"] = customer.id
        request.session["customer_name"] = customer.name
        return redirect("customer_place_order")

    return render(request, "customer_panel/login.html")

def customer_logout(request):
    request.session.pop("customer_id", None)
    request.session.pop("customer_name", None)
    return redirect("customer_home")

def customer_order_success(request):
    return render(request, "customer_panel/order_success.html")

def customer_place_order(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")

    if request.method == "POST":
        product_type = request.POST.get("product_type")

        brand = request.POST.get("brand") or None
        milk_type = request.POST.get("milk_type") or None
        pack_size = request.POST.get("pack_size") or None
        packets = request.POST.get("packets") or 0

        quantity = D(request.POST.get("quantity"), "0")
        unit = (request.POST.get("unit") or "").strip()
        rate = D(request.POST.get("rate"), "0")

        # Safety: other products must have rate, if missing then 0 remains
        if product_type != "MILK" and rate == 0:
            # you can show message, but still allow (your choice)
            pass

        MilkOrder.objects.create(
            customer_id=customer_id,
            product_type=product_type,
            quantity=quantity,
            unit=unit,
            rate=rate,
            brand=brand,
            milk_type=milk_type,
            pack_size=pack_size,
            packets=packets,
            placed_by="CUSTOMER",
            status="PENDING",
        )

        return redirect("customer_order_success")

    return render(request, "customer_panel/place_order.html", {
        "customer_name": request.session.get("customer_name"),
    })

def customer_my_orders(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")

    orders = MilkOrder.objects.filter(customer_id=customer_id).order_by("-date", "-id")
    return render(request, "customer_panel/my_orders.html", {"orders": orders})

# ---------- SHOP: PENDING ORDERS + APPROVE/REJECT ----------
def shop_pending_orders(request):
    orders = MilkOrder.objects.filter(placed_by="CUSTOMER", status="PENDING").order_by("-date", "-id")
    # ✅ your template is in templates root => "pending_orders.html"
    return render(request, "pending_orders.html", {"orders": orders})

def approve_order(request, pk):
    o = get_object_or_404(MilkOrder, pk=pk)
    o.status = "APPROVED"
    o.save()
    return redirect("pending_orders")

def reject_order(request, pk):
    o = get_object_or_404(MilkOrder, pk=pk)
    o.status = "REJECTED"
    o.save()
    return redirect("pending_orders")
