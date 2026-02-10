from django.urls import path
from . import views

urlpatterns = [
    
    path("", views.dashboard, name="dashboard"),   # ✅ first page (front)
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("home/", views.home, name="home"),        # ✅ main home page


              
    path('customer/', views.customer, name='customer'),
 
    path("milkorder/", views.milk_order_view, name="milk_order"),

    


    path("customers/", views.customer_page, name="customer_page"),
    path("customer/add/", views.add_customer, name="add_customer"),
    path("customer/edit/<int:id>/", views.edit_customer, name="edit_customer"),
    path("customer/delete/<int:id>/", views.delete_customer, name="delete_customer"),

    path("transactions/", views.transaction_page, name="transaction_page"),
    path("transaction/add/", views.add_transaction, name="add_transaction"),
    

    
    path("transtpage/", views.transaction_page, name="transaction_page"),
    path("add_transaction/", views.add_transaction, name="add_transaction"),

    # API for auto-fill
    path("api/last-milk/", views.customer_last_milk, name="customer_last_milk"),

    path("report/daily/", views.daily_milk_report, name="daily_milk_report"),

    # ---------- BILL SECTION ----------
    path("bill/", views.bill_select_customer, name="bill_select_customer"),
    path("bill/view/<int:customer_id>/", views.bill_view, name="bill_view"),
    path("bill/pdf/<int:customer_id>/", views.bill_pdf, name="bill_pdf"),



]


