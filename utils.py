import pytesseract
from PIL import Image
import pandas as pd
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def normalize_entry(token: str) -> float:
    """Normalize OCR token into milk quantity (1 or 1.5 litres)"""
    token = token.lower().replace(" ", "")

    # Patterns meaning 1.5 litres
    if token in ["911", "9ii", "9ll", "q11", "9111", "3y1"]:
        return 1.5
    # Just "9" means 1 litre
    if token == "9":
        return 1.0
    return 0.0


def process_image(uploaded_file):
    """Extracts text from image and detects milk entries"""
    image = Image.open(uploaded_file).convert("RGB")
    text = pytesseract.image_to_string(image)

    milk_entries = []
    total_milk = 0.0

    # Tokenize per line
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        tokens = re.findall(r"[0-9a-zA-Z]+", line)  # catch mixed characters
        for token in tokens:
            qty = normalize_entry(token)
            if qty > 0:
                milk_entries.append({"date": line[:10], "milk_ltr": qty})
                total_milk += qty

    rate = 70  # from your bill (34.5 x 70 = 2415)
    extras = 150
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
    c.drawString(50, y, "Rate: ₹70 per litre")
    y -= 15
    c.drawString(50, y, "Extras: ₹150")
    y -= 15
    c.drawString(50, y, f"Grand Total: ₹{grand_total}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
