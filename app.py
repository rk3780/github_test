import streamlit as st

st.title("Hello, Streamlit!")
st.write("Welcome to your simple Streamlit app.")

name = st.text_input("Enter your name:")
age = st.slider("Select your age:", 0, 120, 25)

if st.button("Show Info"):
    st.success(f"Hello {name}, your age is {age}.") 