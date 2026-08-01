from django.db import models

class PodWallet(models.Model):
    pod_id = models.CharField(max_length=20, unique=True)  # e.g. "Pod 1"
    pod_name = models.CharField(max_length=100)  # e.g. "Orca Pod 1 (Kestrel)"
    credit_balance = models.FloatField(default=1000.0)  # Bay Credits (BC)
    escrow_balance = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pod_name} Wallet ({self.credit_balance} BC)"

class TradeOffer(models.Model):
    RESOURCE_CHOICES = [
        ('water', 'Water'),
        ('food', 'Food'),
        ('medicine', 'Medicine'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    seller_pod = models.ForeignKey(PodWallet, on_delete=models.CASCADE, related_name="offers_posted")
    resource_offered = models.CharField(max_length=20, choices=RESOURCE_CHOICES)
    amount_offered = models.FloatField()
    price_in_credits = models.FloatField()  # Price in Bay Credits (BC)
    wanted_resource = models.CharField(max_length=20, choices=RESOURCE_CHOICES, blank=True, null=True)  # For direct barter
    wanted_amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer #{self.id}: {self.seller_pod.pod_id} offering {self.amount_offered} {self.resource_offered} for {self.price_in_credits} BC"

class TradeTransaction(models.Model):
    offer = models.ForeignKey(TradeOffer, on_delete=models.SET_NULL, null=True, blank=True)
    buyer_pod = models.ForeignKey(PodWallet, on_delete=models.CASCADE, related_name="purchases")
    seller_pod = models.ForeignKey(PodWallet, on_delete=models.CASCADE, related_name="sales")
    resource_type = models.CharField(max_length=20)
    amount = models.FloatField()
    price_paid = models.FloatField()
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tx #{self.id}: {self.buyer_pod.pod_id} bought {self.amount} {self.resource_type} from {self.seller_pod.pod_id}"
