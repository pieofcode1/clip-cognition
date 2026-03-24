# module1.py in subdir1
import streamlit as st
from core.module2 import greet

def main():
    greet("Alice")
    st.title("Hello, Streamlit!")
    st.write("This is a simple Streamlit app.")

if __name__ == "__main__":
    main()