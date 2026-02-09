from django.db import models
from decimal import Decimal


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class MilkOrder(models.Model):
    MILK_BRANDS = (
        ("AMUL", "Amul"),
        ("VIKAS", "Vikas"),
        ("SARASWATI", "Saraswati"),
        ("AMAR", "Amar"),
    )

    MILK_TYPES = (
    ("COW", "Cow Milk"),
    ("BUFFALO", "Buffalo Milk"),
    )


    PACK_SIZES = (
        (Decimal("0.5"), "0.5 L"),
        (Decimal("1.0"), "1 L"),
        (Decimal("2.0"), "2 L"),
        (Decimal("5.0"), "5 L"),
    )

    # Milk OR Other
    PRODUCT_TYPES = (
        ("MILK", "Milk"),
        ("GHEE", "Ghee"),
        ("PANEER", "Paneer"),
        ("CURD", "Curd"),
        ("BUTTER", "Butter"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="MILK")

    # Only for Milk
    brand = models.CharField(max_length=20, choices=MILK_BRANDS, blank=True, null=True)
    milk_type = models.CharField(max_length=10, choices=MILK_TYPES, blank=True, null=True)

    pack_size = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)  # 0.5/1/2/5
    packets = models.PositiveIntegerField(default=0)

    # For other products (manual)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # kg/pcs/l
    unit = models.CharField(max_length=10, default="")  # KG/PCS/L etc

    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_liters = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # useful for milk
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.product_type} - {self.total}"

    @staticmethod
    def base_price_half_liter(brand_code: str) -> Decimal:
        """
        Change these base prices anytime.
        This is your 'chart' in one place.
        """
        base = {
            "AMUL": Decimal("27"),
            "VIKAS": Decimal("26"),
            "SARASWATI": Decimal("27"),
            "AMAR": Decimal("26"),
        }
        return base.get(brand_code or "", Decimal("27"))

    def milk_rate_from_base(self) -> Decimal:
        base = self.base_price_half_liter(self.brand)
        # size factor compared to 0.5L
        # 0.5->1, 1->2, 2->4, 5->10
        factor = (Decimal(str(self.pack_size)) / Decimal("0.5"))
        return base * factor

    def save(self, *args, **kwargs):
        if self.product_type == "MILK":
            # required: brand, pack_size, packets
            size = Decimal(str(self.pack_size))
            pkts = Decimal(str(self.packets))

            self.rate = self.milk_rate_from_base()  # rate per packet
            self.total_liters = pkts * size
            self.total = pkts * self.rate

            # clear other fields
            self.quantity = Decimal("0")
            self.unit = ""
        else:
            q = Decimal(str(self.quantity))
            r = Decimal(str(self.rate))
            self.total = q * r
            self.total_liters = Decimal("0")

            # clear milk-only fields
            self.brand = None
            self.pack_size = None
            self.packets = 0

        super().save(*args, **kwargs)


class MilkTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("UDHAR", "Udhar"),
        ("JAMA", "Jama"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    liters = models.DecimalField(max_digits=5, decimal_places=2)
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.amount = Decimal(str(self.liters)) * Decimal(str(self.rate))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.name} - {self.transaction_type} - {self.amount}"
