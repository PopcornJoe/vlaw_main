import streamlit as st
import pdfplumber
import re
from PIL import Image
from streamlit_option_menu import option_menu
import os
import zipfile
import io
from datetime import datetime
import app
import pandas as pd
import search
import database_update
import ocrmypdf
import tempfile
import psycopg2

def get_connection():
    return psycopg2.connect(
        host=st.secrets["database"]["server"],
        dbname=st.secrets["database"]["database"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        sslmode="require"
    )
def convert_date(date_str):
    """
    Convert a date string from dd/mm/yyyy to yyyy-mm-dd format.
    If conversion fails, return the original string.
    """
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return date_str

def flatten_row(row, expected_length):
    """
    Convert a fetched row into a plain list of the expected length.
    
    - First, force the row to a list.
    - If the resulting list has a single element that is itself a list or tuple with the expected length,
      then unwrap that inner element.
    - Otherwise, return the list.
    """
    new_row = list(row)  # Force conversion to a list
    if len(new_row) == 1:
        inner = new_row[0]
        if isinstance(inner, (list, tuple)) and len(inner) == expected_length:
            return list(inner)
    return new_row

def search_matter(matter_no):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM vlaw_base WHERE mat = %s"
    cur.execute(query, (matter_no,))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    
    # Process each row using flatten_row.
    flattened_rows = [flatten_row(row, len(colnames)) for row in rows]
    
    # Debug prints (optional)
    if flattened_rows:
        print("After flattening, first row:", flattened_rows[0])
        print("Length of first row:", len(flattened_rows[0]))
    
    return pd.DataFrame(flattened_rows, columns=colnames)





def extract_text_from_pdf(pdf_file):
    """
    Try to extract text from a PDF file using pdfplumber.
    If no text is found (likely a scanned PDF), run OCR on it and extract text again.
    """
    text = ""
    try:
        # Attempt extraction from the original PDF
        with pdfplumber.open(pdf_file) as pdf:
            st.info(f"Processing {len(pdf.pages)} page(s)...")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")

    # If no text was extracted, assume it's a scanned PDF and run OCR
    if not text.strip():
        st.info("No text extracted. Running OCR to convert scanned PDF into searchable PDF...")
        pdf_file.seek(0)  # Reset file pointer to the beginning
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
                tmp_input.write(pdf_file.read())
                input_path = tmp_input.name

            output_fd, output_path = tempfile.mkstemp(suffix=".pdf")
            os.close(output_fd)

            ocrmypdf.ocr(input_path, output_path, deskew=True, use_threads=True)
            st.success("OCR processing complete!")

            with pdfplumber.open(output_path) as ocr_pdf:
                st.info(f"Extracting text from OCR'd PDF with {len(ocr_pdf.pages)} page(s)...")
                for page in ocr_pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        except Exception as e:
            st.error(f"An error occurred during OCR processing: {e}")
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    return text

def parse_fields_loan_agreement(text):
    patterns = {
        "First Loan Agreement Date":r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})(?=\s*\n\s*Date)",
        "First Loan Agreement Place of signature": r"First\s+Loan\s+Agreement\s+Place\s+of\s+signature\s*(?:[:\-])?\s*(.+)",
        "First Loan Agreement loan amount": r"2\.1\.?\s+Principal\s+debt.*?R\s?([\d,\.]+)",
        "Interest rate in terms of agreement": r"([\d\.]+\s?%)",
        "First agreement instalment term": r"2\.11[,\.]?\s*Term\s+Number\s+of\s+monthly\s+repayments.*?(\d+)\s+months",
        "First loan agreement Instalment amount": r"Monthly\s+repayment\s+amount[\s\S]*?R\s*([\d,\.]+)",
        "Second Loan Agreement Date": r"Second\s+Loan\s+Agreement\s+Date\s*(?:[:\-])?\s*(.+)",
        "Second Loan Agreement of signature": r"Second\s+Loan\s+Agreement\s+(?:of|Place\s+of)\s+signature\s*(?:[:\-])?\s*(.+)",
        "Second Loan Agreement Loan Amount": r"Second\s+Loan\s+Agreement\s+Loan\s+Amount\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Second loan instalment term": r"Second\s+loan\s+instalment\s+term\s*(?:[:\-])?\s*(.+)",
        "Second Loan Agreement instalment amount": r"Second\s+Loan\s+Agreement\s+instalment\s+amount\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
    }
    extracted_fields = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            extracted_fields[label] = match.group(1).strip()
        else:
            extracted_fields[label] = "Not found"
    return extracted_fields

def parse_fields_certificate_of_balance(text):
    patterns = {
        "Statement dates": r"(?i)NAME\s+JNT\s+DATE\s+(?P<statement_date>\d{4}/\d{2}/\d{2})",
        "Arrears Date": r"(?i)at\s+midnight\s+on\s+(?P<date_of_cob>\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
        "Arrears Amount": r"(?i)arrear\s+amount.*?R(?P<numeric>\d{1,3}(,\d{3})*\.\d{2})\s*\((?P<words>[^)]+)\)",
        "Date of COB": r"(?i)at\s+midnight\s+on\s+(?P<date_of_cob>\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
        "Capital Amount ito COB": r"(?i)amounts\s+to\s+R\s*(?P<amount>\d{1,3}(,\d{3})*\.\d{2})",
        "Date of interest ito COB": r"(?i)from\s+(?P<date_of_interest>\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
        "Instalment amount ito COB": r"(?i)the\s+monthly\s+instalment\s+is\s+(?P<raw>R[^\(]+)\(\s*(?P<words>[^)]+)\)",
    }
    extracted_fields = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            extracted_fields[label] = match.group(1).strip()
        else:
            extracted_fields[label] = "Not found"
    return extracted_fields

def bond_agreement(text):
    patterns = {
        "First Def Name": r"First Defendant.*?([A-Z]+\s+[A-Z]+)",
        "First Def Surname": r"First Defendant.*?[A-Z]+\s+([A-Z]+)",
        "First Def ID": r"IDENTITY\s*NUMBER:\s*([\d\s]+)",
        "Email": r"Per\s+Registered\s+email:\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
        "Second Def Name": r"The\s+second\s+Defendant\s+is\s+([A-Z]+\s+[A-Z]+\s+[A-Z]+)",
        "Second Def Surname": r"Second Defendant.*?[A-Z]+\s+([A-Z]+)",
        "Second Def ID": r"Second Defendant.*?IDENTITY\s*NUMBER:\s*([\d\s]+)",
        "Domicilium Address": r"the\s+Defendants\s+chose\s+(.*?)(?=\s+as\s+their\s+domicilium)",
        "Immovable property Address": r"(Erf\s+\d+[\s\S]*?subject\s+to\s+the\s+conditions\s+therein\s+contained\.)",
        "Short property description": r"Property\s+Description\s+([^\n]+)",
        "Full property description": r"(Erf\s+\d+[\s\S]*?subject\s+to\s+the\s+conditions\s+therein\s+contained\.)",
        "FIRST BOND Bond number": r"Bond\s+(?:No\.?\s*)?([A-Z]?\d+/\d+)",
        "Date of registration of First Bond": r"On\s+or\s+about\s+(\d{1,2}\s+\w+\s+\d{4})\s*\(.*?\)\s+and\s+at\s+([A-Za-z]+)",
        "Capital amount of First Bond": r"2\.5\.?\s*Capital\s+amount.*?R\s?([\d,\.]+)",
        "Additional amount of First Bond": r"2\.4\.?\s*Additional\s*amount.*?R\s?([\d,\.]+)",
        "SECOND BOND Bond Number": r"SECOND\s+BOND\s+(?:Bond\s+)?Number\s*(?:[:\-])?\s*([A-Z]?\d+/\d+)",
        "Date of registration f Second Bond": r"Date\s+of\s+registration\s+f\s+Second\s+Bond\s*(?:[:\-])?\s*(.+)",
        "Capital amount of Second Bond": r"Capital\s+amount\s+of\s+Second\s+Bond\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Additional amount of Second Bond": r"Additional\s+amount\s+of\s+Second\s+Bond\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
    }
    extracted_fields = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        extracted_fields[label] = match.group(1).strip() if match else "Not found"
    return extracted_fields

def declaration(text):
    patterns = {
        "First Def Name": r"First Defendant.*?([A-Z]+\s+[A-Z]+)",
        "First Def Surname": r"First Defendant.*?[A-Z]+\s+([A-Z]+)",
        "First Def ID": r"IDENTITY\s*NUMBER:\s*([\d\s]+)",
        "Email": r"Per\s+Registered\s+email:\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
        "Second Def Name": r"The\s+second\s+Defendant\s+is\s+([A-Z]+\s+[A-Z]+\s+[A-Z]+)",
        "Second Def Surname": r"Second Defendant.*?[A-Z]+\s+([A-Z]+)",
        "Second Def ID": r"Second Defendant.*?IDENTITY\s*NUMBER:\s*([\d\s]+)",
        "Domicilium Address": r"the\s+Defendants\s+chose\s+(.*?)(?=\s+as\s+their\s+domicilium)",
        "Immovable property Address": r"(Erf\s+\d+[\s\S]*?subject\s+to\s+the\s+conditions\s+therein\s+contained\.)",
        "Short property description": r"Property\s+Description\s+([^\n]+)",
        "Full property description": r"(Erf\s+\d+[\s\S]*?subject\s+to\s+the\s+conditions\s+therein\s+contained\.)",
        "FIRST BOND Bond number": r"Bond\s+(?:No\.?\s*)?([A-Z]?\d+/\d+)",
        "Date of registration of First Bond": r"On\s+or\s+about\s+(\d{1,2}\s+\w+\s+\d{4})\s*\(.*?\)\s+and\s+at\s+([A-Za-z]+)",
        "Capital amount of First Bond": r"2\.5\.?\s*Capital\s+amount.*?R\s?([\d,\.]+)",
        "Additional amount of First Bond": r"2\.4\.?\s*Additional\s*amount.*?R\s?([\d,\.]+)",
        "SECOND BOND Bond Number": r"SECOND\s+BOND\s+(?:Bond\s+)?Number\s*(?:[:\-])?\s*([A-Z]?\d+/\d+)",
        "Date of registration f Second Bond": r"Date\s+of\s+registration\s+f\s+Second\s+Bond\s*(?:[:\-])?\s*(.+)",
        "Capital amount of Second Bond": r"Capital\s+amount\s+of\s+Second\s+Bond\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Additional amount of Second Bond": r"Additional\s+amount\s+of\s+Second\s+Bond\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
    }
    extracted_fields = {}
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        extracted_fields[label] = match.group(1).strip() if match else "Not found"
    return extracted_fields

def summons_upload():
    st.title("Matter Search and Document Upload")
    st.sidebar.title("About")
    st.sidebar.info(
        "This app extracts key information from legal PDF documents, allows for manual input of additional fields, "
        "and generates populated Word documents based on predefined templates. "
        "It's designed to be user-friendly and requires no technical knowledge to operate."
    )

    if "searched_matter_number" not in st.session_state:
        st.session_state["searched_matter_number"] = ""
    
    # Search Section
    st.header("Search for Matter")
    matter_number = st.text_input("Enter Matter Number:")
    
    if st.button("Search"):
        if matter_number:
            df = search_matter(matter_number)
            if df.empty:
                st.warning(f"No record found for matter number: {matter_number}")
            else:
                st.success("Record(s) found:")
                st.dataframe(df)
                st.session_state["matter_found"] = True
                st.session_state["searched_matter_number"] = matter_number
        else:
            st.error("Please enter a matter number.")
    
    if st.session_state.get("matter_found", False):
        st.info("You can now upload documents related to this matter.")
        st.header("Upload Documents")
        
        # Upload Loan Agreement
        loan_agreement_file = st.file_uploader("Upload Loan Agreement PDF", type=["pdf"], key="loan_agreement_uploader")
        if loan_agreement_file:
            st.write("Loan Agreement file uploaded successfully!")
            loan_text = extract_text_from_pdf(loan_agreement_file)
            st.write("Loan Agreement extracted text length:", len(loan_text))
            st.subheader("Loan Agreement Extracted Text")
            st.text_area("Loan Agreement Raw Text", loan_text, height=300)
            loan_fields = parse_fields_loan_agreement(loan_text)
            st.session_state["loan_fields"] = loan_fields
            st.subheader("Loan Agreement Parsed Fields (Editable)")
            with st.form(key="edit_loan_fields_form"):
                updated_loan_fields = {}
                for key, val in loan_fields.items():
                    updated_loan_fields[key] = st.text_input(label=key, value=val)
                loan_submit_button = st.form_submit_button(label="Save Loan Agreement Changes")
                if loan_submit_button:
                    st.success("Loan Agreement fields updated!")
                    st.session_state["edited_loan_fields"] = updated_loan_fields
                    st.write("Updated Loan Agreement Fields:", updated_loan_fields)
                    database_update.update_database(updated_loan_fields, st.session_state["searched_matter_number"], doc_type="loan_agreement")
        
        certificate_balance_file = st.file_uploader("Upload Certificate of Balance PDF", type=["pdf"], key="certificate_balance_uploader")
        if certificate_balance_file:
            st.write("Certificate of Balance file uploaded successfully!")
            certificate_text = extract_text_from_pdf(certificate_balance_file)
            st.write("Certificate of Balance extracted text length:", len(certificate_text))
            st.subheader("Certificate of Balance Extracted Text")
            st.text_area("Certificate of Balance Raw Text", certificate_text, height=300)
            certificate_fields = parse_fields_certificate_of_balance(certificate_text)
            st.session_state["certificate_fields"] = certificate_fields
            st.subheader("Certificate of Balance Parsed Fields (Editable)")
            with st.form(key="edit_certificate_fields_form"):
                updated_certificate_fields = {}
                for key, val in certificate_fields.items():
                    updated_certificate_fields[key] = st.text_input(label=key, value=val)
                certificate_submit_button = st.form_submit_button(label="Save Certificate of Balance Changes")
                if certificate_submit_button:
                    st.success("Certificate of Balance fields updated!")
                    st.session_state["edited_certificate_fields"] = updated_certificate_fields
                    st.write("Updated Certificate Fields:", updated_certificate_fields)
                    database_update.update_database(updated_certificate_fields, st.session_state["searched_matter_number"], doc_type="certificate_balance")

        bond_agreement_file = st.file_uploader("Upload Bond agreement PDF", type=["pdf"], key="Bond_agreement_uploader")
        if bond_agreement_file:
            st.write("Bond agreement file uploaded successfully!")
            bond_text = extract_text_from_pdf(bond_agreement_file)
            st.write("Bond agreement extracted text length:", len(bond_text))
            st.subheader("Bond Agreement Extracted Text")
            st.text_area("Bond Agreement Raw Text", bond_text, height=300)
            bond_fields = bond_agreement(bond_text)
            st.session_state["bond_fields"] = bond_fields
            st.subheader("Bond Agreement Parsed Fields (Editable)")
            with st.form(key="edit_bond_fields_form"):
                updated_bond_fields = {}
                for key, val in bond_fields.items():
                    updated_bond_fields[key] = st.text_input(label=key, value=val)
                bond_submit_button = st.form_submit_button(label="Save Bond Agreement Changes")
                if bond_submit_button:
                    st.success("Bond Agreement fields updated!")
                    st.session_state["edited_bond_fields"] = updated_bond_fields
                    st.write("Updated Bond Agreement Fields:", updated_bond_fields)
                    database_update.update_database(updated_bond_fields, st.session_state["searched_matter_number"], doc_type="bond_agreement")
            
            declaration_file = st.file_uploader("Upload declaration PDF", type=["pdf"], key="Declaration_uploader")
            if declaration_file:
                st.write("Declaration file uploaded successfully!")
                declaration_text = extract_text_from_pdf(declaration_file)
                st.write("Declaration extracted text length:", len(declaration_text))
                st.subheader("Declaration Extracted Text")
                st.text_area("Declaration Raw Text", declaration_text, height=300)
                declaration_fields = bond_agreement(declaration_text)
                st.session_state["declaration_fields"] = declaration_fields
                st.subheader("Declaration Parsed Fields (Editable)")
                with st.form(key="edit_declaration_fields_form"):
                    updated_declaration_fields = {}
                    for key, val in declaration_fields.items():
                        updated_declaration_fields[key] = st.text_input(label=key, value=val)
                    declaration_submit_button = st.form_submit_button(label="Save Declaration Changes")
                    if declaration_submit_button:
                        st.success("Declaration fields updated!")
                        st.session_state["edited_declaration_fields"] = updated_declaration_fields
                        st.write("Updated Declaration Fields:", updated_declaration_fields)
                        database_update.update_database(updated_declaration_fields, st.session_state["searched_matter_number"], doc_type="declaration")
