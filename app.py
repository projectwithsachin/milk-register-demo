import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import pandas as pd

st.set_page_config(page_title="Milk Ledger OCR", page_icon="🥛", layout="centered")

st.title("🥛 Milk Ledger OCR")
st.write("Upload a milk register page and get a digital bill instantly.")

# --------- IMAGE PREPROCESSING ----------
def preprocess_image(image):
    img = np.array(image.convert("L"))  # grayscale
    _, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)  # black & white
    return Image.fromarray(img)

# --------- EXTRACT ENTRIES -------------
def extract_milk_entries(text):
    # pattern like: 01/08 2, 02-08 1, 3.8. 2 etc
    pattern = r"(\d{1,2}[/-]\d{1,2})\s+(\d+)"
    entries = re.findall(pattern, text)
    cleaned = []
    for date, litres in entries:
        try:
            cleaned.append((date, int(litres)))
        except:
            pass
    return cleaned

# --------- STREAMLIT UI ----------------
customer = st.text_input("Customer Name", "Sharma")
rate = st.number_input("Rate per liter (₹)", value=70)

uploaded_file = st.file_uploader("Upload Milk Register Page", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded Page", use_column_width=True)

    # Preprocess
    proc_img = preprocess_image(image)

    # OCR
    text = pytesseract.image_to_string(proc_img, config="--psm 6")
    st.subheader("📜 OCR Extracted Text")
    st.text(text)

    # Parse entries
    entries = extract_milk_entries(text)

    if entries:
        df = pd.DataFrame(entries, columns=["Date", "Liters"])
        df["Rate (₹)"] = rate
        df["Amount (₹)"] = df["Liters"] * rate

        total_litres = df["Liters"].sum()
        total_amount = df["Amount (₹)"].sum()

        st.subheader(f"🧾 Bill for {customer}")
        st.dataframe(df)

        st.success(f"**Total Liters:** {total_litres} | **Total Amount:** ₹{total_amount}")

        # Download Excel
        excel_file = f"{customer}_bill.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            st.download_button("📥 Download Bill (Excel)", f, file_name=excel_file)

    else:
        st.error("No valid milk entries detected. Please check image quality.")
