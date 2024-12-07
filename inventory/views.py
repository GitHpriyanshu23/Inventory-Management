from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Medicine
from .forms import MedicineForm
import cv2
import json
import re
from django.shortcuts import render
from django.shortcuts import redirect
from datetime import datetime



def scan_qr_code(request):
    """
    Scans a QR code using the device camera and processes the data.
    If the QR code matches a medicine in the database, it updates the fields.
    Otherwise, it creates a new medicine entry.
    """
    # Start video capture (using the default camera)
    cap = cv2.VideoCapture(0)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                return JsonResponse({'error': 'Unable to access the camera.'}, status=500)

            # Initialize QR code detector
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(frame)

            if data:  # QR code detected
                print(f"Scanned Data: {data}")  # Debugging output

                # Extract specific fields from the QR code data
                name_match = re.search(r"Name:\s*(.+)", data)
                description_match = re.search(r"Description:\s*(.+)", data)
                expiry_date_match = re.search(r"Expiry Date:\s*(.+)", data)

                if not (name_match and description_match and expiry_date_match):
                    cap.release()
                    cv2.destroyAllWindows()
                    return JsonResponse({'error': 'Invalid QR code format.'}, status=400)

                # Extract values from matches
                name = name_match.group(1).strip()
                description = description_match.group(1).strip()
                expiry_date = expiry_date_match.group(1).strip()

                # Validate expiry date format
                try:
                    expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                except ValueError:
                    cap.release()
                    cv2.destroyAllWindows()
                    return JsonResponse({'error': 'Invalid expiry date format.'}, status=400)

                # Release resources
                cap.release()
                cv2.destroyAllWindows()

                # Redirect to the add medicine page with pre-filled data
                return redirect(
                    f"/admin/inventory/medicine/add/?name={name}&description={description}&expiry_date={expiry_date}"
                )

            # Display the video feed
            cv2.imshow('QR Code Scanner', frame)

            # Allow exiting the scanner with 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return JsonResponse({'error': 'No QR code detected.'}, status=400)

def edit_medicine(request, pk):
    """
    View to edit a medicine's details. This is the target page after a successful QR scan.
    """
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('admin:inventory_medicine_changelist')  # Redirect to a list of medicines after saving
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'edit_medicine.html', {'form': form})
    
@csrf_exempt
def update_stock(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            medicine_id = data['medicine_id']
            quantity_change = data['quantity_change']  # Positive for adding stock, negative for deductions

            # Get the medicine
            medicine = Medicine.objects.get(id=medicine_id)

            # Update the stock quantity
            medicine.stock_quantity += quantity_change
            if medicine.stock_quantity < 0:
                return JsonResponse({'error': 'Insufficient stock'}, status=400)

            medicine.save()

            return JsonResponse({'message': 'Stock updated successfully'}, status=200)
        except Medicine.DoesNotExist:
            return JsonResponse({'error': 'Medicine not found'}, status=404)
        except KeyError:
            return JsonResponse({'error': 'Invalid data format'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def qr_scanner_view(request):
    if request.method == "POST":
        try:
            # Parse the data from the scanned QR code
            data = json.loads(request.body)
            medicine_name = data.get("name")
            stock_quantity = data.get("stock_quantity", 0)
            expiry_date = data.get("expiry_date")  # Format: YYYY-MM-DD

            # Check if the medicine exists
            medicine, created = Medicine.objects.get_or_create(name=medicine_name)

            if not created:
                # Update stock if it exists
                medicine.stock_quantity += stock_quantity
            else:
                # Add new stock and expiry date for new medicine
                medicine.stock_quantity = stock_quantity
                medicine.expiry_date = expiry_date

            # Save the medicine object
            medicine.save()

            return JsonResponse({"message": "Medicine added/updated successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return render(request, "admin/qr_scanner.html")  # Render the scanner page