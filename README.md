# Milk Register Extractor 🥛

A Streamlit app that extracts milk delivery records from register photos (handwritten "9", "911", "X") and generates:
- Clean Date vs Milk table
- CSV export
- PDF Bill (with totals)

## Deployment
1. Push this repo to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io)
3. Deploy the app (`app.py`)

## Usage
- Upload a milk register image
- OCR extracts entries
- Adjust rate/extra manually if needed
- Download CSV or PDF Bill

## Notes
- "9"   = 1 litre  
- "911" = 1.5 litre  
- "X"   = 0 litre
