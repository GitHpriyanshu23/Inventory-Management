from django.core.mail import send_mail
from datetime import datetime, timedelta
from .models import Medicine, PurchaseOrder, Supplier
from inventory.models import Medicine
from django.db.models import F
from django.db import models



def auto_generate_purchase_orders():
    low_stock_meds = Medicine.objects.filter(stock_quantity__lte=10)

    for med in low_stock_meds:
        # Check if a pending order already exists
        if not PurchaseOrder.objects.filter(medicine=med, status='Pending').exists():
            # Use the medicine's supplier for the order
            supplier = med.supplier  # Assuming Medicine is linked to a Supplier
            if supplier:
                PurchaseOrder.objects.create(
                    medicine=med,
                    supplier=supplier,
                    quantity=50,  # Default reorder quantity
                )

def check_low_stock():
    # Fetch all medicines and filter manually
    medicines = Medicine.objects.all()
    low_stock_medicines = []

    # Filter medicines with low stock using Python
    for medicine in medicines:
        if medicine.stock_quantity <= medicine.low_stock_threshold:
            low_stock_medicines.append(medicine)

    for medicine in low_stock_medicines:
        # Check if an alert was sent in the last 24 hours
        if not medicine.last_alerted or (datetime.now() - medicine.last_alerted).days >= 1:
            # Send email alert
            subject = f"Low Stock Alert: {medicine.name}"
            message = f"""
            The stock for {medicine.name} is critically low.

            Current Stock: {medicine.stock_quantity}
            Threshold: {medicine.low_stock_threshold}

            Please restock immediately.
            """
            recipient_list = ['admin@example.com']  # Replace with the admin's email
            send_mail(subject, message, 'noreply@example.com', recipient_list)

            # Update the last_alerted timestamp
            medicine.last_alerted = datetime.now()
            medicine.save()
