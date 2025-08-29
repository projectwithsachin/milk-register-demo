import pytesseract
from PIL import Image
import pandas as pd
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def process_image(uploaded_file):
    """Extracts text from image and detects milk entries"""
    image = Image.open(uploaded_file).convert("RGB")
    text = pytesseract.image_to_string(image)

    milk_entries = []
    total_milk = 0.0

    # Regex: match "9" or "911" style entries
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # "911" means 1.5 litres, just "9" means 1 litre
        match = re.findall(r"\b(?:911|9)\b", line)
        if match:
            for m in match:
                if m == "911":
                    qty = 1.5
                else:
                    qty = 1.0
                milk_entries.append({"date": line[:10], "milk_ltr": qty})
                total_milk += qty

    rate = 60
    extras = 100
    grand_total = (total_milk * rate) + extras

    return text, milk_entries, total_milk, grand_total


def generate_csv(milk_entries, total_milk, grand_total):
    """Exports milk register as CSV"""
    df = pd.DataFrame(milk_entries)
    df.loc[len(df)] = {"date": "TOTAL", "milk_ltr": total_milk}
    df.loc[len(df)] = {"date": "GRAND TOTAL", "milk_ltr": grand_total}
    return df.to_csv(index=False).encode("utf-8")


def generate_bill_pdf(milk_entries, total_milk, grand_total):
    """Generates plain PDF bill"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Bacchas Milk Supplier, Sector 168, Noida")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Customer: ___________")
    y -= 15
    c.drawString(50, y, "Month: ___________")
    y -= 30

    c.drawString(50, y, "Date        Milk (Ltr)")
    y -= 20

    for entry in milk_entries:
        c.drawString(50, y, f"{entry['date']}    {entry['milk_ltr']}")
        y -= 15

    y -= 20
    c.drawString(50, y, f"Total Milk: {total_milk} litres")
    y -= 15
    c.drawString(50, y, "Rate: ₹60 per litre")
    y -= 15
    c.drawString(50, y, "Extras: ₹100")
    y -= 15
    c.drawString(50, y, f"Grand Total: ₹{grand_total}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
