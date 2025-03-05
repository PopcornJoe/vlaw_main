import streamlit as st

# 1) Insert <link> to the CSS
st.components.v1.html("""
<link rel="stylesheet" href="http://localhost:8000/intro_assets/introjs.min.css">
<script src="http://localhost:8000/intro_assets/intro.min.js"></script>
<script src="http://localhost:8000/intro_assets/tour.js"></script>
""", height=0)

st.title("External Intro.js Example")

# 2) Use a button to call runTour() from tour.js
if st.button("Start External Tour"):
    st.components.v1.html("""
    <script>
      // We call the runTour() function from tour.js
      runTour();
    </script>
    """, height=0)
