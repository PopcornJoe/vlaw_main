import PyPDF2
import re
from datetime import datetime


def extract_debtors(matter_name):
    '''
    Extracts the debtor names from the matter name.
    If the matter name contains a '/', it splits the matter name on the first '/'.
    '''
    if '/' in matter_name:
        debtors = matter_name.split('/', 1)  # Split only on the first '/'
        return debtors[0].strip(), debtors[1].strip()
    else:
        return matter_name.strip(), ""  # If no '/', all is debtor_1 and debtor_2 is empty

def extract_text_from_pdf(pdf_path):
    '''
    Extracts text from a PDF file using PyPDF2.
    '''
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_data_from_text(full_text):
    '''
    Extracts key data fields from the full text of a legal document.
    '''
    data = {
        'matter_name': None,
        'matter_number': None,
        'debtor_1': None,
        'debtor_2': None,
        'address': None,
        'email': '',
        'title': '',
        'account_number': None,
        'balance_amount': None,
        'instalment_amount': None,
        'arrears_amount': None, 
        'property_description': '',
        'current_date': datetime.now().strftime("%d %B %Y")
    }

    # Patterns for all fields
    patterns = {
        'matter_name': r'(?:\*JNT\s+)?(.*?)\s+CONT PERSON',
        'account_number': r'ACCOUNT #\s*([\d-]+)',
        'balance_amount': r'CURRENT BALANCE\.\.:\s*([\d,.]+)',
        'instalment_amount': r'PAYMENT AMOUNT\.\.\.:\s*([\d,.]+)',
        'arrears_amount': r'PAST DUE AMOUNT\.\.:\s*([\d,.]+)',
        'address': r'CONT PERSON\.:[^\n]*\n(.*?)(?=\s+CELL PHONE|$)'
    }

    # Extract all fields
    for key, pattern in patterns.items():
        if key == 'address':
            match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        else:
            match = re.search(pattern, full_text, re.IGNORECASE)
        
        if match:
            if key == 'address':
                address_text = match.group(1).strip()
                # Remove PER PHONE and BUS PHONE parts
                address_text = re.sub(r'\s*PER PHONE.*?(?=\n|$)', '', address_text, flags=re.IGNORECASE)
                address_text = re.sub(r'\s*BUS PHONE.*?(?=\n|$)', '', address_text, flags=re.IGNORECASE)
                # Split into lines and remove empty lines
                address_lines = [line.strip() for line in address_text.split('\n') if line.strip()]
                data[key] = '\n'.join(address_lines)
            else:
                data[key] = match.group(1).strip()
        # Extract debtor_1 and debtor_2 from matter_name
    if data['matter_name']:
        data['debtor_1'], data['debtor_2'] = extract_debtors(data['matter_name'])

    return data
