import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------
# OCR Preprocessing Function
# -------------------------------
def process_image(uploaded_file):
    image = Image.open(uploaded_file).convert("L")  # grayscale
    img_array = np.array(image)

    # Thresholding for black & white
    _, thresh = cv2.threshold(img_array, 150, 255, cv2.THRESH_BINARY)

    # Noise removal
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # OCR
    text = pytesseract.image_to_string(processed, config="--psm 6")

    return text


# -------------------------------
# Parse OCR Text into Milk Data
# -------------------------------
def parse_milk_data(text):
    milk_data = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Find entries like 9, 911, X
        match = re.search(r'(\d{1,3}|X)', line)
        if match:
            value = match.group(1)
            if value == "911":
                milk_data.append(1.5)
            elif value == "9":
                milk_data.append(1.0)
            elif value.upper() == "X":
                milk_data.append(0.0)

    return milk_data


# -------------------------------
# Generate Plain Text PDF Bill
# -------------------------------
def generate_pdf(dates, milk_data, rate, extra):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Bacchas Milk Supplier, Sector 168, Noida", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Customer: ___________________", styles["Normal"]))
    story.append(Paragraph("Month: ______________________", styles["Normal"]))
    story.append(Spacer(1, 12))

    total_milk = sum(milk_data)
    total_amount = total_milk * rate + extra

    story.append(Paragraph("Date - Milk (Ltr)", styles["Heading3"]))
    for d, m in zip(dates, milk_data):
        story.append(Paragraph(f"{d} - {m}", styles["Normal"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total Milk: {total_milk} Ltr", styles["Normal"]))
    story.append(Paragraph(f"Rate: ₹{rate} per Ltr", styles["Normal"]))
    story.append(Paragraph(f"Extras: ₹{extra}", styles["Normal"]))
    story.append(Paragraph(f"Grand Total: ₹{total_amount}", styles["Heading2"]))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


# -------------------------------
# Streamlit App
# -------------------------------
st.title("📒 Milk Register Extractor")

uploaded_file = st.file_uploader("Upload milk register image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Register", use_column_width=True)

    # Process OCR
    text = process_image(uploaded_file)
    st.subheader("📜 Extracted Raw OCR Text")
    st.text(text)

    # Parse milk data
    milk_data = parse_milk_data(text)

    if milk_data:
        dates = list(range(1, len(milk_data) + 1))
        df = pd.DataFrame({"Date": dates, "Milk (Ltr)": milk_data})
        st.subheader("✅ Cleaned Milk Data")
        st.dataframe(df)

        # Rate & Extras
        rate = st.number_input("Rate per litre (₹)", value=60)
        extra = st.number_input("Extra charges (₹)", value=0)

        total_milk = sum(milk_data)
        total_amount = total_milk * rate + extra

        st.write(f"**Total Milk:** {total_milk} Ltr")
        st.write(f"**Total Amount:** ₹{total_amount}")

        # Download CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", data=csv, file_name="milk_data.csv", mime="text/csv")

        # Download PDF
        pdf_data = generate_pdf(dates, milk_data, rate, extra)
        st.download_button("⬇️ Download PDF Bill", data=pdf_data, file_name="milk_bill.pdf", mime="application/pdf")

    else:
        st.error("⚠️ No valid milk entries detected. Please check image quality.")
