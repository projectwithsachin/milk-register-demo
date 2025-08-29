import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import pandas as pd

# ---------- Image Processing Function ----------
def process_image(uploaded_file):
    # Read image
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # OCR extraction
    raw_text = pytesseract.image_to_string(thresh)

    # Clean OCR text for easier matching
    clean_text = (
        raw_text.replace(" ", "")
        .replace("|", "")
        .replace("I", "1")
        .replace("l", "1")
        .lower()
    )

    # Extract milk entries (911 = 1.5L, 9 = 1L, x = no milk)
    entries = re.findall(r"(911|9|x)", clean_text)

    total_litres = 0.0
    for e in entries:
        if e == "911":
            total_litres += 1.5
        elif e == "9":
            total_litres += 1.0
        # 'x' means skip

    return raw_text, entries, total_litres


# ---------- Streamlit UI ----------
st.set_page_config(page_title="Milk Register Demo", layout="wide")

st.title("🥛 Milk Register OCR Demo")
st.write("Upload a bill/register image and extract milk entries automatically.")

uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Show uploaded image
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    # Process image
    raw_text, entries, total_litres = process_image(uploaded_file)

    # Display OCR result
    st.subheader("📜 Extracted Raw OCR Text")
    st.text(raw_text)

    if entries:
        st.subheader("✅ Milk Entries Detected")
        df = pd.DataFrame({"Entry": entries})
        st.dataframe(df, use_container_width=True)

        st.write(f"**Total Milk: {total_litres} litres**")
    else:
        st.warning("⚠️ No valid milk entries detected. Please check image quality.")
