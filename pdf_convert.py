import streamlit as st
import ocrmypdf
import tempfile
import os

# Set the TESSERACT_PATH environment variable so OCRmyPDF knows where to find Tesseract.
os.environ["TESSERACT_PATH"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def pdf_convert():

    st.title("Scanned PDF to Searchable PDF Converter")

    # Upload the scanned PDF file
    uploaded_file = st.file_uploader("Upload a scanned PDF", type=["pdf"])

    if uploaded_file is not None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_path = tmp_input.name

        # Create a temporary file path for the output PDF
        output_fd, output_path = tempfile.mkstemp(suffix=".pdf")
        os.close(output_fd)  # We only need the path; OCRmyPDF will write to it.

        st.info("Processing the file. This may take a few moments...")
        try:
            # Run OCR on the uploaded file without the tesseract_cmd argument
            ocrmypdf.ocr(input_path, output_path, deskew=True, use_threads=True)
            
            st.success("OCR processing complete!")

            # Provide a download button for the searchable PDF
            with open(output_path, "rb") as pdf_file:
                st.download_button(
                    label="Download Searchable PDF",
                    data=pdf_file,
                    file_name="searchable.pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.error(f"An error occurred during OCR processing: {e}")
        finally:
            # Clean up temporary files
            os.remove(input_path)
            os.remove(output_path)
