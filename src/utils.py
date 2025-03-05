# src/utils.py
import os
import tempfile

def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            return tmp.name
    except Exception as e:
        raise Exception(f"Error saving uploaded file: {str(e)}")

def cleanup_temp_files(file_paths):
    for file_path in file_paths:
        try:
            os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting temporary file {file_path}: {str(e)}")



