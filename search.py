import streamlit as st
import psycopg2
import pandas as pd


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

def run_search():

    st.title("Matter Search")
    
    matter_number = st.text_input("Enter Matter Number (caseno):")
    
    if st.button("Search"):
        if matter_number:
            df = search_matter(matter_number)
            if df.empty:
                st.warning(f"No record found for matter number: {matter_number}")
            else:
                st.success("Record(s) found:")
                st.dataframe(df)
        else:
            st.error("Please enter a matter number.")

if __name__ == "__main__":
    run_search()