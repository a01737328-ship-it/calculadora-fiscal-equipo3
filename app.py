import streamlit as st
import myabe

st.title("Calculadora Fiscal")

if st.button("Calcular"):
    resultado = myabe.main()  # cambia esto si tu función principal tiene otro nombre
    st.write(resultado)
