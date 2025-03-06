import streamlit as st
from datetime import datetime
import pyodbc

def get_connection():
    """
    Establish a connection to the Microsoft SQL Server database.
    """
    cconnection_string = (
            "DRIVER={FreeTDS};"
            "SERVER=" + st.secrets["database"]["server"] + ";"
            "PORT=1433;"
            "DATABASE=" + st.secrets["database"]["database"] + ";"
            "UID=" + st.secrets["database"]["user"] + ";"
            "PWD=" + st.secrets["database"]["password"] + ";"
            "TDS_Version=8.0;"
        )
    return pyodbc.connect(connection_string)

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

def convert_numeric(num_str):
    """
    Remove commas from a numeric string.
    If conversion fails, return the original string.
    """
    try:
        return num_str.replace(",", "")
    except Exception:
        return num_str

def update_database(updated_fields, searched_matter_num, doc_type=None):
    """
    Update the database record in vlaw_base corresponding to the matter number
    from the search (searched_matter_num) using the updated fields from the form.
    The "MATTER NUMBER" field from the extraction is ignored.
    The optional doc_type parameter can be used to indicate which document type
    is being updated.
    """
    matter_num = searched_matter_num
    if not matter_num:
        st.error("No valid matter number found. Cannot update the database.")
        return

    # Map the form field keys to database column names.
    column_mapping = {
        "MATTER NUMBER": "mat",
        "FNB account number": "fnbaccno",
        "Case number": "caseno",
        "Court": "court",
        "Date of summons": "sumdate",
        "First Def Name": "defname1",
        "First Def Surname": "defsur1",
        "First Def ID": "id1",   
        "Second Def Name": "defname2",
        "Second Def Surname": "defsur2",
        "Second Def ID": "id2",
        "Domicilium Address": "domadd",
        "Immovable property Address": "immadd",
        "Email": "email",
        "Short property description": "shortprop",
        "Full property description": "fullpropdescription",
        "FIRST BOND Bond number": "bondno1",
        "Date of registration of First Bond": "bondregdate1",
        "Capital amount of First Bond": "bondamount",
        "Additional amount of First Bond": "addamount",
        "SECOND BOND Bond Number": "bondno2",
        "Date of registration f Second Bond": "bondregdate2",
        "Capital amount of Second Bond": "bondamount2",
        "Additional amount of Second Bond": "addamount2",
        "First Loan Agreement Date": "loandate1",
        "First Loan Agreement Place of signature": "loanplace1",
        "First Loan Agreement loan amount": "loanamount1",
        "Interest rate in terms of agreement": "loanintrate",
        "First agreement instalment term": "instalmentperiod1",
        "First loan agreement Instalment amount": "instalmentamount1",
        "Second Loan Agreement Date": "loandate2",
        "Second Loan Agreement of signature": "loanplace2",
        "Second Loan Agreement Loan Amount": "loanamount2",
        "Second loan instalment term": "instalmentperiod2",
        "Second Loan Agreement instalment amount": "instalmentout2",
        "Demand date": "demanddate",
        "Statement dates": "statementdates",
        "Arrears Date": "arrearsdate",
        "Arrears Amount": "arrearsamount",
        "Date of COB": "certdate",
        "Capital Amount ito COB": "rcapital",
        "Interest rate in terms of COB": "jintrate",
        "Date of interest ito COB": "jdate",
        "Date of Section 129 Letters": "s129dates",
        "S129 Post Office": "s129postoffice",
        "Valuation Amount": "valamount",
        "Valuation Date": "valedate",
        "Sheriff Details": "sherifffulldetails",
        "Summons Served": "summonsserve",
        "Date Dies Expire": "diesexpr",
        "Instalment Amount in FNB Affidavit": "instfnbaff",
        "Date of Arrears in FNB Affidavit": "arrearsdatefnb",
        "Amount of Arrears in FNB Affidavit": "arrearsfnbaff",
        "Months in Arrears": "monthsinarrears",
        "Date of Statement Period": "stperiodfnbaff",
        "DATE Judgment Granted": "judggranted",
        "DATE OF SALE": "dateofsale",
        "TIME OF SALE": "timeofsale",
        "PROPERTY ZONE": "propertyzone",
        "RATES AND TAXES2": "ratesandtaxes",
        "LEVIES": "levies",
        "DATE OF RATES AND TAXES": "DATERATEANDTAXES",
        "SHERIFF CONDUCTION SALE": "which_sheriff",
        "DEFAULT SHERIFF AND ADDRESS": "defaultsheriffaddress",
        "IF NOT DEFAULT SHERIFF": "ifnotdefaultsheriff",
        "LOCAL AUTHORITIES AND ADDRESS": "localauthoritiesadd",
        "MANAGING AGENTS ADDRESS": "managingagentsadd",
    }

    update_fields = {}
    for key, value in updated_fields.items():
        if key == "MATTER NUMBER":
            continue
        if key in column_mapping:
            if value not in (None, "", "Not found"):
                update_fields[column_mapping[key]] = value

    date_columns = [
        "sumdate", "bondregdate1", "bondregdate2", "loandate1",
        "loandate2", "s129dates", "valdate", "judggranted", "dateofsale"
    ]
    
    # Convert each date field from dd/mm/yyyy to yyyy-mm-dd if necessary.
    for col in date_columns:
        if col in update_fields and update_fields[col] not in (None, "", "Not found"):
            update_fields[col] = convert_date(update_fields[col])

    numeric_columns = [
        "bondamount", "addamount", "bondamount2", "addamount2", 
        "loanamount1", "loanamount2", "arrearsamount", "valamount", 
        "arrearsfnbaff", "monthsinarrears", "instalmentamoount1", "instalmentout2", "rcapital"
    ]
    for col in numeric_columns:
        if col in update_fields and update_fields[col] not in (None, "", "Not found"):
            update_fields[col] = convert_numeric(update_fields[col])

    if not update_fields:
        st.warning("No valid fields to update.")
        return

    # Use SQL Server style parameter markers "?" instead of "%s"
    set_clause = ", ".join([f"{col} = ?" for col in update_fields.keys()])
    update_query = f"UPDATE vlaw_base SET {set_clause} WHERE mat = ?;"
    values = list(update_fields.values())
    values.append(matter_num)

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(update_query, values)
        conn.commit()
        cur.close()
        conn.close()
        st.success("Database updated successfully!")
    except Exception as e:
        st.error(f"Error updating database: {e}")
