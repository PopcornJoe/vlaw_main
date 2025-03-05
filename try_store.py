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
import psycopg2
import pandas as pd
import search
import database_update




def get_connection():
    """
    Establish a connection to the PostgreSQL database.
    Connection details are securely stored in streamlit secrets.
    """
    return psycopg2.connect(
        host="localhost",
        database="VLaw",
        user="postgres",
        password="liverpool4"
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

def search_matter(mat):
    
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM vlaw_base WHERE mat = %s;"
    cur.execute(query, (mat,))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=colnames)



def extract_text_from_pdf(pdf_file):
   
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            st.info(f"Processing {len(pdf.pages)} pages...")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def parse_fields(text):



    patterns = {

        "MATTER NUMBER": r"CASE NO:\s*([\d-]+)",
        "FNB account number": r"Account\s+number:\s*(\d+)",
        "Case number": r"CASE\s*NO:\s*([\d\-]+)",
        "Court": r"IN\s+THE\s+HIGH\s+COURT\s+OF\s+([A-Z\s]+)",
        "Date of summons": r"filed electronically by the Registrar on\s*([\d/]+)",
        "First Def Name": r"First Defendant.*?([A-Z]+\s+[A-Z]+)",
        "First Def Surname": r"First Defendant.*?[A-Z]+\s+([A-Z]+)",
        "First Def ID": r"IDENTITY\s*NUMBER:\s*([\d\s]+)",
        'Email' : r"Per\s+Registered\s+email:\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
        "Second Def Name": r"The\s+second\s+Defendant\s+is\s+([A-Z]+\s+[A-Z]+\s+[A-Z]+)",
        "Second Def Surname": r"Second Defendant.*?[A-Z]+\s+([A-Z]+)",
        "Second Def ID": r"Second Defendant.*?IDENTITY\s*NUMBER:\s*([\d\s]+)",

        "Domicilium Address": r"the\s+Defendants\s+chose\s+(.*?)(?=\s+as\s+their\s+domicilium)",
        

        
        "Immovable property Address":r"(Erf\s+\d+[\s\S]*?subject\s+to\s+the\s+conditions\s+therein\s+contained\.)",
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
        
        "First Loan Agreement Date": r"On\s+or\s+about\s+(\d{1,2}\s+\w+\s+\d{4})\s*\(.*?\)\s+and\s+at\s+([A-Za-z]+)",
        "First Loan Agreement Place of signature": r"First\s+Loan\s+Agreement\s+Place\s+of\s+signature\s*(?:[:\-])?\s*(.+)",
        "First Loan Agreement loan amount": r"\.14\.?\s*Total\s+amount\s+repayable.*?R\s?([\d,\.]+)",
        "Interest rate in terms of agreement": r"2\.7\.?\s*Interest\s+rate.*?(\d{1,2}\.\d{1,2}%)",
        "First agreement instalment term": r"2\.11\.?\s*Term.*?([\d]+)\s+months",
        "First loan agreement Instalment amount": r"2\.10\.?\s*Repayment\s+amount.*?R\s?([\d,\.]+)",
        
        "Second Loan Agreement Date": r"Second\s+Loan\s+Agreement\s+Date\s*(?:[:\-])?\s*(.+)",
        "Second Loan Agreement of signature": r"Second\s+Loan\s+Agreement\s+(?:of|Place\s+of)\s+signature\s*(?:[:\-])?\s*(.+)",
        "Second Loan Agreement Loan Amount": r"Second\s+Loan\s+Agreement\s+Loan\s+Amount\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Second loan instalment term": r"Second\s+loan\s+instalment\s+term\s*(?:[:\-])?\s*(.+)",
        "Second Loan Agreement instalment amount": r"Second\s+Loan\s+Agreement\s+instalment\s+amount\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        
        "Demand date": r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*\n\s*Dear\s+Sir\s+and\s+Madam",
        "Statement dates": r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*\n\s*Dear\s+Sir\s+and\s+Madam",
        "Arrears Date": r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*\n\s*Dear\s+Sir\s+and\s+Madam",
        "Arrears Amount": r"Arrears\s+Amount\s+R\s?([\d,\.]+)",
        "Date of COB": r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*\n\s*Dear\s+Sir\s+and\s+Madam",
        "Capital Amount ito COB": r"Current\s+Balance\s+R\s?([\d,\.]+)",
        "Interest rate in terms of COB": r"2\.7\.?\s*Interest\s+rate.*?(\d{1,2}\.\d{1,2}%)",
        "Date of interest ito COB": r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*\n\s*Dear\s+Sir\s+and\s+Madam",
        "Instalment amount ito COB": r"Current\s+Instalment\s+R\s?([\d,\.]+)",
        
        "Date of Section 129 Letters": r"Date\s+of\s+Section\s+129\s+Letters\s*(?:[:\-])?\s*(.+)",
        "S129 Post Office": r"S129\s+Post\s+Office\s*(?:[:\-])?\s*(.+)",
        "Valuation Amount": r"Valuation\s+Amount\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Valuation Date": r"Valuation\s+Date\s*(?:[:\-])?\s*(.+)",
        "Sheriff Details": r"Sheriff\s+Details\s*(?:[:\-])?\s*(.+)",
        "DJ Set Down Date": r"DJ\s+Set\s+Down\s+Date\s*(?:[:\-])?\s*(.+)",
        "Summons Served": r"Summons\s+Served\s*(?:[:\-])?\s*(.+)",
        "Date Dies Expire": r"Date\s+Dies\s+Expire\s*(?:[:\-])?\s*(.+)",
        
        "Instalment Amount in FNB Affidavit": r"Instalment\s+Amount\s+in\s+FNB\s+Affidavit\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Date of Arrears in FNB Affidavit": r"Date\s+of\s+Arrears\s+in\s+FNB\s+Affidavit\s*(?:[:\-])?\s*(.+)",
        "Amount of Arrears in FNB Affidavit": r"Amount\s+of\s+Arrears\s+in\s+FNB\s+Affidavit\s*(?:[:\-])?\s*R\s*([\d,\.]+)",
        "Months in Arrears": r"Months\s+in\s+Arrears\s*(?:[:\-])?\s*(.+)",
        "Date of Statement Period": r"Date\s+of\s+Statement\s+Period\s*(?:[:\-])?\s*(.+)",
        
        "DATE Judgment Granted": r"DATE\s+Judgment\s+Granted\s*(?:[:\-])?\s*(.+)",
        "DATE OF SALE": r"DATE\s+OF\s+SALE\s*(?:[:\-])?\s*(.+)",
        "TIME OF SALE": r"TIME\s+OF\s+SALE\s*(?:[:\-])?\s*(.+)",
        "PROPERTY ZONE": r"PROPERTY\s+ZONE\s*(?:[:\-])?\s*(.+)",
        "RATES AND TAXES2": r"RATES\s+AND\s+TAXES2\s*(?:[:\-])?\s*(.+)",
        "LEVIES": r"LEVIES\s*(?:[:\-])?\s*(.+)",
        "DATE OF RATES AND TAXES": r"DATE\s+OF\s+RATES\s+AND\s+TAXES\s*(?:[:\-])?\s*(.+)",
        "SHERIFF CONDUCTION SALE": r"SHERIFF\s+CONDUCTION\s+SALE\s*(?:[:\-])?\s*(.+)",
        "DEFAULT SHERIFF AND ADDRESS": r"DEFAULT\s+SHERIFF\s+AND\s+ADDRESS\s*(?:[:\-])?\s*(.+)",
        "IF NOT DEFAULT SHERIFF": r"IF\s+NOT\s+DEFAULT\s+SHERIFF\s*(?:[:\-])?\s*(.+)",
        "LOCAL AUTHORITIES AND ADDRESS": r"LOCAL\s+AUTHORITIES\s+AND\s+ADDRESS\s*(?:[:\-])?\s*(.+)",
        "MANAGING AGENTS ADDRESS": r"MANAGING\s+AGENTS\s+ADDRESS\s*(?:[:\-])?\s*(.+)",
        "SECOND BOND HOLDER FOR 46\(5\)": r"SECOND\s+BOND\s+HOLDER\s+FOR\s+46\(5\)\s*(?:[:\-])?\s*(.+)",
    }



    extracted_fields = {}

    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            extracted_fields[label] = match.group(1).strip()
        else:
            extracted_fields[label] = "Not found"

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
    matter_number = st.text_input("Enter Matter Number :")
    
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
        st.info("You can now upload a document related to this matter.")
        st.header("Upload Document")
        uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"], key="pdf_uploader_unique")
        if uploaded_file:
            st.write("File uploaded successfully!")
            text = extract_text_from_pdf(uploaded_file)
            st.write("Extracted text length:", len(text))
            st.session_state["extracted_text"] = text
            if text:
                st.subheader("Extracted Text")
                st.text_area("Raw Text", text, height=300)
                fields = parse_fields(text)
                st.session_state["fields"] = fields
                st.subheader("Parsed Fields (Editable)")
                # Create a form so the user can edit the extracted data.
                with st.form(key="edit_fields_form"):
                    updated_fields = {}
                    for key, val in fields.items():
                        updated_fields[key] = st.text_input(label=key, value=val)
                    submit_button = st.form_submit_button(label="Save Changes")
                    if submit_button:
                        st.success("Fields updated!")
                        st.session_state["edited_fields"] = updated_fields
                        st.write("Updated Fields:", updated_fields)
                        database_update.update_database(updated_fields,st.session_state["searched_matter_number"])
            else:
                st.error("No text extracted from the PDF.")


                
                
                
        