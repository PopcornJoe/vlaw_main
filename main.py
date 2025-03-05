import streamlit as st
import pdfplumber
import re
from PIL import Image
from streamlit_option_menu import option_menu
import os
import zipfile
import io
from src.pdf_processor import extract_text_from_pdf, extract_data_from_text
from src.word_processor import process_templates, TEMPLATES
from src.utils import save_uploaded_file, cleanup_temp_files
from datetime import datetime
import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

logo = Image.open('Van-Hulsteyns-Logo-Large.png')

def main():

    st.sidebar.image(logo)
    with st.sidebar:
        selected = option_menu(
            menu_title="",         
            options=["Search and generate","Statement upload", "Summons Upload"],
            default_index=0,)
    if selected == "Statement upload":
        app.legal_document_processor()
    if selected == "Summons Upload":
        try_2.summons_upload()
    if selected =="PDF convert":
        pdf_convert.pdf_convert()
    if selected == 'Search and generate':
        search_and_gen.app()
    if selected == 'Merge PDF':
        pdf_merge.merge_pdfs()




if __name__ == "__main__":
    main()
