# src/pdf_processor.py
import PyPDF2

def extract_full_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
    return full_text

# app.py
import streamlit as st
import tempfile
import os
from src.pdf_processor import extract_full_text_from_pdf

st.title("PDF Text Extractor")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # Extract full text from the PDF
    full_text = extract_full_text_from_pdf(tmp_file_path)

    # Display the full text
    st.subheader("Extracted Full Text:")
    st.text_area("PDF Content", full_text, height=300)

    # Clean up the temporary file
    os.unlink(tmp_file_path)

    # Add a button to copy the text
    if st.button("Copy Full Text"):
        st.write("Text copied to clipboard!")
        st.session_state.clipboard = full_text

    # Optionally, you can add a text input for users to test regex patterns
    st.subheader("Test Regex Pattern")
    regex_pattern = st.text_input("Enter a regex pattern to test")
    if regex_pattern:
        import re
        matches = re.findall(regex_pattern, full_text)
        st.write("Matches found:", matches)