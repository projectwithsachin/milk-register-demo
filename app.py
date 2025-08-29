import streamlit as st
from utils import process_image, generate_bill_pdf, generate_csv
from io import BytesIO

st.set_page_config(page_title="Milk Register", layout="centered")

st.title("🥛 Milk Register - Bacchas Milk Supplier, Sector 168, Noida")

uploaded_file = st.file_uploader("📤 Upload Milk Bill Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Bill", use_container_width=True)

    # OCR Processing
    with st.spinner("🔍 Processing image..."):
        ocr_text, milk_entries, total_milk, grand_total = process_image(uploaded_file)

    st.subheader("📜 Extracted Raw OCR Text")
    st.text(ocr_text)

    if len(milk_entries) > 0:
        st.success("✅ Milk Entries Detected")
        st.write(f"**Total Milk:** {total_milk} litres")
        st.write(f"**Grand Total:** ₹{grand_total}")

        # Generate CSV
        csv_data = generate_csv(milk_entries, total_milk, grand_total)
        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name="milk_register.csv",
            mime="text/csv"
        )

        # Generate PDF
        pdf_bytes = generate_bill_pdf(milk_entries, total_milk, grand_total)
        st.download_button(
            "⬇️ Download PDF Bill",
            data=pdf_bytes,
            file_name="milk_bill.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("⚠️ No valid milk entries detected. Please check image quality.")
