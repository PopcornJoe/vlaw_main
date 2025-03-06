import streamlit as st
import os
import zipfile
import io
from src.pdf_processor import extract_text_from_pdf, extract_data_from_text
from src.word_processor import process_templates, TEMPLATES
from src.utils import save_uploaded_file, cleanup_temp_files
import pyodbc  # Updated: using pyodbc for SQL Server
from datetime import datetime



def clean_numeric(value):
    """Convert string numbers with commas into proper float values."""
    if value:
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None

def none_if_blank(val):
    """Return None if the value is an empty string, otherwise return the value."""
    if isinstance(val, str) and val.strip() == "":
        return None
    return val

# Updated insert query for SQL Server using parameter markers (?) and the OUTPUT clause.
insert_query = """
    INSERT INTO vlaw_base (
        matter_name,
        mat,
        defname1,
        defname2,
        domadd,
        email,
        title,
        fnbaccno,
        rcapital,
        instalmentamount,
        arrearsamount,
        fullpropdescription
    ) OUTPUT INSERTED.id1
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

def legal_document_processor():
    st.title("Legal Document Processor ⚖️")
    st.write("""
    This app extracts key information from legal PDF documents, allows for additional manual input,
    and generates populated Word documents based on the extracted data.
    Upload a PDF file to begin.
    """)

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        try:
            pdf_path = save_uploaded_file(uploaded_file)
            full_text = extract_text_from_pdf(pdf_path)
            extracted_data = extract_data_from_text(full_text)
            
            st.subheader("Extracted and Manual Input Data:")
            with st.form("data_form"):
                form_data = {}
                for key, value in extracted_data.items():
                    if key == 'address':
                        st.write("Address:")
                        address_lines = value.split('\n')
                        form_data['address'] = []
                        for i, line in enumerate(address_lines):
                            form_data['address'].append(st.text_input(f"Line {i+1}", line, key=f"address_line_{i}"))
                    elif key == 'title':
                        form_data[key] = st.text_input(f"{key.replace('_', ' ').title()}:", value, key="title")
                    else:
                        form_data[key] = st.text_input(f"{key.replace('_', ' ').title()}:", value, key=key)
                
                st.write("Select templates to generate:")
                selected_templates = []
                for template_name in TEMPLATES.keys():
                    if st.checkbox(template_name, value=True):
                        selected_templates.append(template_name)
                
                submit_button = st.form_submit_button("Update Data and Generate Documents")
            
            if submit_button:
                connection_string = (
                    "DRIVER={FreeTDS};"
                    "SERVER=" + st.secrets["database"]["server"] + ";"
                    "PORT=1433;"
                    "DATABASE=" + st.secrets["database"]["database"] + ";"
                    "UID=" + st.secrets["database"]["user"] + ";"
                    "PWD=" + st.secrets["database"]["password"] + ";"
                    "TDS_Version=8.0;"
                )
                try:
                    conn = pyodbc.connect(connection_string)
                    cur = conn.cursor()
                    st.success("Connected successfully!")
                except Exception as e:
                    st.error(f"Error connecting: {e}")
                
                # Update extracted_data with values from form_data
                for key, value in form_data.items():
                    if key == 'address':
                        extracted_data[key] = '\n'.join([line for line in value if line])
                    else:
                        extracted_data[key] = value
                
                # Process selected templates
                generated_docs = process_templates(selected_templates, extracted_data)
                st.success("Documents generated successfully!")
                
                # Create a zip file containing all generated documents
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for template_name, doc_path in generated_docs.items():
                        zip_file.write(doc_path, os.path.basename(doc_path))
                
                values = (
                    none_if_blank(extracted_data.get("matter_name")),
                    none_if_blank(extracted_data.get("matter_number")),
                    none_if_blank(extracted_data.get("debtor_1")),
                    none_if_blank(extracted_data.get("debtor_2")),
                    none_if_blank(extracted_data.get("address")),
                    none_if_blank(extracted_data.get("email")),
                    none_if_blank(extracted_data.get("title")),
                    none_if_blank(extracted_data.get("account_number")),
                    clean_numeric(extracted_data.get("balance_amount")),
                    clean_numeric(extracted_data.get("instalment_amount")),
                    clean_numeric(extracted_data.get("arrears_amount")),
                    none_if_blank(extracted_data.get("property_description"))
                )
                
                cur.execute(insert_query, values)
                new_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                conn.close()
                
                st.download_button(
                    label="Download All Documents",
                    data=zip_buffer.getvalue(),
                    file_name=f"all_documents_{extracted_data.get('matter_number')}.zip",
                    mime="application/zip"
                )
                
                st.success("Data updated and documents generated successfully!")
                st.write("Updated data:", extracted_data)
            
            if st.checkbox("Show full extracted text"):
                st.text_area("Full Text", full_text, height=300)
            
            cleanup_temp_files([pdf_path])
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    st.sidebar.title("About")
    st.sidebar.info(
        "This app extracts key information from legal PDF documents, allows for manual input of additional fields, "
        "and generates populated Word documents based on predefined templates. "
        "It's designed to be user-friendly and requires no technical knowledge to operate."
    )
