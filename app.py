# app.py
import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Milk Register Digitizer", layout="centered")
st.title("📒 Milk Register Digitizer (Demo)")

# Inputs
customer_name = st.text_input("Customer name", "Sharma Ji")
month_text = st.text_input("Month (for bill)", "July 2025")
rate = st.number_input("Rate per liter (₹)", min_value=1, value=70)
uploaded_file = st.file_uploader("Upload register photo (jpg/png)", type=["jpg", "jpeg", "png"])

def preprocess_image(img: Image.Image) -> Image.Image:
    img = img.convert("L")  # grayscale
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    # resize if very large (optional)
    max_w = 1200
    if img.width > max_w:
        h = int(max_w * img.height / img.width)
        img = img.resize((max_w, h))
    return img

def parse_milk_text(text: str):
    text = text.replace('\r','\n')
    # look for explicit totals like "39 x 70 = 2730"
    total_match = re.search(r'(\d{1,4})\s*[×xX*]\s*(\d{1,5})\s*=\s*(\d{1,7})', text)
    extra_match = re.search(r'\+\s*(\d{1,7})', text)
    if total_match:
        liters = int(total_match.group(1))
        detected_rate = int(total_match.group(2))
        amount = int(total_match.group(3)) + (int(extra_match.group(1)) if extra_match else 0)
        method = "explicit_total"
        extra = int(extra_match.group(1)) if extra_match else 0
        return {"liters": liters, "rate": detected_rate, "extra": extra, "amount": amount, "method": method}
    # fallback: count likely '1' marks or patterns like '911' or '1 L'
    tokens = re.findall(r'\b911\b|\b1\b|\b\d+\s*ltr\b|\b\d+\s*L\b', text, flags=re.IGNORECASE)
    liters = 0
    for tok in tokens:
        m = re.search(r'(\d+)', tok)
        if m:
            liters += int(m.group(1))
    if liters == 0:
        # conservative fallback: count '1' characters in non-total lines
        lines = [ln for ln in text.splitlines() if '=' not in ln and 'x' not in ln and 'X' not in ln and '×' not in ln]
        one_count = sum(ln.count('1') for ln in lines)
        liters = one_count
    return {"liters": liters, "rate": rate, "extra": 0, "amount": liters * rate, "method": "heuristic_count"}

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Original image", use_column_width=True)
    st.info("Preprocessing image and running OCR (may take a few seconds).")
    imgp = preprocess_image(image)
    st.image(imgp, caption="Preprocessed (grayscale/autocontrast)", use_column_width=True)
    try:
        ocr_text = pytesseract.image_to_string(imgp, lang='eng+hin')
    except Exception as e:
        st.error("OCR failed inside app: " + str(e))
        ocr_text = ""
    st.subheader("Extracted text (OCR)")
    st.text_area("OCR output", ocr_text, height=240)

    parsed = parse_milk_text(ocr_text)
    st.subheader("Auto-detected summary (best-effort)")
    st.write(f"Detected liters: **{parsed['liters']}**")
    st.write(f"Rate used: **₹{parsed.get('rate', rate)}**")
    st.write(f"Extra charges detected: **₹{parsed.get('extra',0)}**")
    st.write(f"Total amount (computed): **₹{parsed.get('amount', parsed['liters']*rate)}**")
    st.write(f"Extraction method: `{parsed['method']}`")

    # allow manual correction
    user_liters = st.number_input("If detected liters are incorrect, enter correct liters here", min_value=0, value=int(parsed['liters']))
    user_extra = st.number_input("Extra charges (if any)", min_value=0, value=int(parsed.get('extra',0)))
    computed_total = user_liters * rate + user_extra
    st.write(f"Final total to generate in bill: **₹{computed_total}**")

    if st.button("Generate Excel & PDF bill"):
        # Excel
        df = pd.DataFrame([{
            "Customer": customer_name,
            "Month": month_text,
            "Total Liters": user_liters,
            "Rate (₹/L)": rate,
            "Extra Charges (₹)": user_extra,
            "Total Amount (₹)": computed_total
        }])
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button("📥 Download Bill (Excel)", data=towrite, file_name=f"{customer_name}_bill_{month_text}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # PDF (simple)
        pdf_buf = io.BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=A4)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(72, 800, f"Monthly Milk Bill - {customer_name}")
        c.setFont("Helvetica", 12)
        c.drawString(72, 770, f"Month: {month_text}")
        c.drawString(72, 750, f"Total Liters: {user_liters}")
        c.drawString(72, 730, f"Rate per Liter: ₹{rate}")
        c.drawString(72, 710, f"Extra Charges: ₹{user_extra}")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, 680, f"TOTAL AMOUNT DUE: ₹{computed_total}")
        c.setFont("Helvetica", 10)
        c.drawString(72, 650, f"Extraction method used: {parsed['method']}")
        c.drawString(72, 630, "NOTE: This is an automated best-effort extraction. Verify amounts before collection.")
        c.save()
        pdf_buf.seek(0)
        st.download_button("📥 Download Bill (PDF)", data=pdf_buf, file_name=f"{customer_name}_bill_{month_text}.pdf", mime="application/pdf")
