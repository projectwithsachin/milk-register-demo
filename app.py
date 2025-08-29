import streamlit as st
import cv2
import pytesseract
import numpy as np
import pandas as pd
from PIL import Image
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.title("Milk Register Extractor 🥛")

# --- Decode logic for litres ---
def decode_milk(entry: str) -> float:
    entry = entry.strip().upper()
    if entry == "X":
        return 0.0
    elif entry == "911":
        return 1.5
    elif entry == "9":
        return 1.0
    else:
        return 0.0   # fallback

# --- Generate PDF Invoice ---
def generate_pdf(df, total_qty, rate, extra, total_amount):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Supplier header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, height - 50, "Milk Supply Bill")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 80, "Bacchas Milk Supplier")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 95, "Sector 168, Noida")

    # Customer & Month placeholders
    c.drawString(350, height - 80, "Customer: __________")
    c.drawString(350, height - 95, "Month: ____________")

    # Table header
    y = height - 130
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Date")
    c.drawString(150, y, "Milk (Ltr)")

    # Table rows
    c.setFont("Helvetica", 10)
    y -= 20
    for _, row in df.iterrows():
        c.drawString(50, y, str(row["Date"]))
        c.drawString(150, y, str(row["Milk (Ltr)"]))
        y -= 15
        if y < 100:  # avoid overflow
            c.showPage()
            y = height - 100

    # Summary
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"Total Milk: {total_qty} litres")
    y -= 15
    c.drawString(50, y, f"Rate per Litre: ₹{rate}")
    y -= 15
    c.drawString(50, y, f"Extra Charges: ₹{extra}")
    y -= 15
    c.drawString(50, y, f"Grand Total: ₹{total_amount}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# File uploader
uploaded_file = st.file_uploader("Upload Milk Register Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    img = np.array(image)

    # Preprocess
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # OCR
    custom_config = r'--oem 3 --psm 6'
    extracted_text = pytesseract.image_to_string(thresh, config=custom_config)

    st.subheader("📜 Extracted Raw OCR Text")
    st.text(extracted_text)

    # Parse table
    milk_data = []
    for line in extracted_text.split("\n"):
        line = line.strip()
        if re.match(r"^\d+\s+[0-9Xx]+", line):
            parts = line.split()
            date = parts[0]
            milk = parts[1]
            qty = decode_milk(milk)
            milk_data.append({"Date": date, "Milk (Ltr)": qty})

    if milk_data:
        df = pd.DataFrame(milk_data)

        st.subheader("📊 Extracted Table")
        st.dataframe(df)

        # Auto-detect rate/extra
        rate_match = re.search(r"(\d+(\.\d+)?)\s*[Xx]\s*(\d+(\.\d+)?)", extracted_text)
        extra_match = re.search(r"\+?\s*(\d{2,4})", extracted_text)

        auto_rate = float(rate_match.group(3)) if rate_match else 70
        auto_extra = float(extra_match.group(1)) if extra_match else 0

        # Manual overrides
        rate = st.number_input("Rate per Litre (₹)", value=auto_rate, step=1.0)
        extra = st.number_input("Extra Amount (₹)", value=auto_extra, step=1.0)

        # Calculations
        total_qty = df["Milk (Ltr)"].sum()
        total_amount = total_qty * rate + extra

        st.subheader("📈 Summary")
        st.write(f"Total Milk Delivered: **{total_qty} litres**")
        st.write(f"Rate per Litre: **₹{rate}**")
        st.write(f"Extra Charges: **₹{extra}**")
        st.write(f"Grand Total: **₹{total_amount}**")

        # Download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "milk_data.csv", "text/csv")

        # Download PDF
        pdf_file = generate_pdf(df, total_qty, rate, extra, total_amount)
        st.download_button("Download PDF Bill", pdf_file, "milk_bill.pdf", "application/pdf")
