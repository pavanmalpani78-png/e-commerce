from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("home/", views.home, name="home"),
    path("terms/", views.terms_page, name="terms"),

    # Shopkeeper customers
    path("customers/", views.customer_page, name="customer_page"),
    path("customer/add/", views.add_customer, name="add_customer"),
    path("customer/edit/<int:id>/", views.edit_customer, name="edit_customer"),
    path("customer/delete/<int:id>/", views.delete_customer, name="delete_customer"),

    # Orders (Shopkeeper)
    path("milkorder/", views.milk_order, name="milk_order"),
    path("orders/edit/<int:pk>/", views.edit_order, name="edit_order"),
    path("orders/delete/<int:pk>/", views.delete_order, name="delete_order"),

    # Transactions
    path("transactions/", views.transaction_page, name="transaction_page"),
    path("transaction/add/", views.add_transaction, name="add_transaction"),
    path("api/last-milk/", views.customer_last_milk, name="customer_last_milk"),

    # Report
    path("report/daily/", views.daily_milk_report, name="daily_milk_report"),
    

    # Bill
    path("bill/", views.bill_select_customer, name="bill_select_customer"),
    path("bill/view/<int:customer_id>/", views.bill_view, name="bill_view"),
    path("bill/pdf/<int:customer_id>/", views.bill_pdf, name="bill_pdf"),

    # Customer Panel
    path("c/", views.customer_home, name="customer_home"),
    path("c/login/", views.customer_login, name="customer_login"),
    path("c/logout/", views.customer_logout, name="customer_logout"),
    path("c/order/", views.customer_place_order, name="customer_place_order"),
    path("c/my-orders/", views.customer_my_orders, name="customer_my_orders"),
    path("c/success/", views.customer_order_success, name="customer_order_success"),

    # Shop pending orders
    path("shop/pending-orders/", views.shop_pending_orders, name="pending_orders"),
    path("shop/approve/<int:pk>/", views.approve_order, name="approve_order"),
    path("shop/reject/<int:pk>/", views.reject_order, name="reject_order"),
]
