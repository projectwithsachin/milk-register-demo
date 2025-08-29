import streamlit as st
from utils import process_image, generate_csv, generate_bill_pdf

st.set_page_config(page_title="Milk Bill Scanner", layout="centered")

st.title("🥛 Milk Bill Scanner (Bacchas Milk Supplier)")

uploaded_file = st.file_uploader("Upload Milk Bill Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Process image with OCR
    raw_text, milk_entries, total_milk, grand_total, debug_tokens = process_image(uploaded_file)

    # Show raw OCR text
    st.subheader("📜 Extracted Raw OCR Text")
    st.text(raw_text)

    # Show debug tokens for troubleshooting OCR mapping
    st.subheader("🔍 Debug OCR Tokens")
    st.write(debug_tokens)

    if milk_entries:
        st.subheader("📅 Milk Entries Detected")
        st.write(milk_entries)

        st.subheader("📊 Summary")
        st.write(f"**Total Milk:** {total_milk} litres")
        st.write("**Rate:** ₹70 per litre")
        st.write("**Extras:** ₹150")
        st.write(f"**Grand Total:** ₹{grand_total}")

        # Export buttons
        st.subheader("📂 Export Options")

        csv_data = generate_csv(milk_entries, total_milk, grand_total)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name="milk_register.csv",
            mime="text/csv",
        )

        pdf_data = generate_bill_pdf(milk_entries, total_milk, grand_total)
        st.download_button(
            label="⬇️ Download PDF Bill",
            data=pdf_data,
            file_name="milk_bill.pdf",
            mime="application/pdf",
        )

    else:
        st.warning("⚠️ No valid milk entries detected. Please check image quality.")
