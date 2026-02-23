import streamlit as st
import myabeE

st.title("Calculadora Fiscal")

if st.button("Calcular"):
    resultado = myabeE.main()  # cambia esto si tu función principal tiene otro nombre
    st.write(resultado)
