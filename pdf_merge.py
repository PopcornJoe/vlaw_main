import streamlit as st
import PyPDF2
from io import BytesIO

def merge_pdfs():
    st.title("PDF Merger and Page Reordering App")
    st.write("Upload your PDFs, set their order, and specify the page order for each before merging them.")

    # Allow the user to upload multiple PDF files
    uploaded_files = st.file_uploader("Choose PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        file_settings = []
        # Loop over each uploaded file and display options for ordering
        for i, uploaded_file in enumerate(uploaded_files):
            st.subheader(f"File: {uploaded_file.name}")
            
            # Input for overall file order in the merge
            order = st.number_input(
                f"Merge order for {uploaded_file.name}", min_value=1, value=i+1, key=f"order_{i}"
            )
            
            # Read the number of pages for this PDF
            try:
                uploaded_file.seek(0)
                reader = PyPDF2.PdfReader(uploaded_file)
                num_pages = len(reader.pages)
                default_page_order = ",".join(str(x) for x in range(1, num_pages+1))
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")
                default_page_order = ""
                num_pages = 0
            
            # Input for page order for this PDF, default is natural order (1,2,3,...)
            page_order = st.text_input(
                f"Page order for {uploaded_file.name} (comma-separated)", 
                default_page_order, key=f"page_order_{i}"
            )
            
            file_settings.append({
                "file": uploaded_file,
                "order": order,
                "page_order": page_order,
                "num_pages": num_pages,
            })

        # Let the user specify the name of the final merged PDF
        output_filename = st.text_input("Enter the output file name", "merged.pdf")

        if st.button("Merge PDFs"):
            # Sort the files according to the specified merge order
            file_settings_sorted = sorted(file_settings, key=lambda x: x["order"])
            writer = PyPDF2.PdfWriter()

            # Process each file in the chosen order
            for settings in file_settings_sorted:
                file_obj = settings["file"]
                page_order_str = settings["page_order"]

                # Convert the page order string (e.g., "3,1,2") to a list of integers
                try:
                    order_list = [int(num.strip()) for num in page_order_str.split(",") if num.strip()]
                except Exception as e:
                    st.error(f"Invalid page order for {settings['file'].name}: {e}")
                    return

                # Verify the page order is a permutation of all pages in the PDF
                if sorted(order_list) != list(range(1, settings["num_pages"] + 1)):
                    st.error(
                        f"Invalid page order for {settings['file'].name}. "
                        f"It must be a permutation of numbers from 1 to {settings['num_pages']}."
                    )
                    return

                file_obj.seek(0)
                reader = PyPDF2.PdfReader(file_obj)
                for page_num in order_list:
                    writer.add_page(reader.pages[page_num - 1])

            # Write the merged output to an in-memory buffer
            output = BytesIO()
            writer.write(output)
            output.seek(0)

            # Ensure the output filename ends with .pdf
            if not output_filename.lower().endswith('.pdf'):
                output_filename += '.pdf'

            st.download_button(
                label="Download merged PDF",
                data=output,
                file_name=output_filename,
                mime="application/pdf"
            )
    else:
        st.info("Please upload one or more PDF files.")
