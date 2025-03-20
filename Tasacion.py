import pdfplumber
import pandas as pd
import re
import streamlit as st

# Configuración de Streamlit
st.title("Comparador de Valores en PDFs")
st.subheader("Carga hasta 5 archivos PDF")

# Cargar archivos (permite hasta 5)
uploaded_files = st.file_uploader("Selecciona archivos PDF", type=["pdf"], accept_multiple_files=True)

# Expresiones regulares para extraer valores de la Sección 2
patterns_section2 = {
    "Valor Comercial USD": r"Valor Comercial\s*en\s*Dólares.*?US\$\s*([\d,]+\.\d+)",
    "Valor Comercial S/": r"Valor Comercial\s*en\s*Soles.*?S/\s*([\d,]+\.\d+)",
    "Valor de Realización Inmediata USD": r"Valor Realización Inmediata.*?US\$\s*([\d,]+\.\d+)",
    "Valor de Realización Inmediata S/": r"Valor Realización Inmediata.*?S/\s*([\d,]+\.\d+)"
}

# Expresión regular para extraer valores en dólares y soles
value_pattern = re.compile(r"US\$?\s*([\d,]+\.\d+)|S/\s*([\d,]+\.\d+)")

# Palabras clave para la Sección 1
keywords_section1 = ["VALOR TOTAL (RRPP + NO INSCRITO)"]

# Función para extraer valores de la Sección 1
def extract_section1_values(pdf):
    extracted_data = {}
    with pdfplumber.open(pdf) as pdf_reader:
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                for keyword in keywords_section1:
                    if keyword in text:
                        lines = text.split("\n")
                        values = []
                        for i, line in enumerate(lines):
                            if keyword in line:
                                for next_line in lines[i : i + 5]:
                                    matches = value_pattern.findall(next_line)
                                    extracted_values = [m[0] if m[0] else m[1] for m in matches if any(m)]
                                    values.extend(extracted_values)
                                if values:
                                    extracted_data[keyword] = values[:4]
                                    break
    return extracted_data

# Función para extraer valores de la Sección 2
def extract_section2_values(pdf):
    extracted_data = {}
    with pdfplumber.open(pdf) as pdf_reader:
        full_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    for key, pattern in patterns_section2.items():
        match = re.search(pattern, full_text, re.DOTALL)
        extracted_data[key] = match.group(1) if match else None
    return extracted_data

# Procesar cada archivo PDF
if uploaded_files:
    for uploaded_file in uploaded_files[:5]:  # Limitar a 5 archivos
        st.subheader(f"Resultados para: {uploaded_file.name}")

        # Extraer valores de la Sección 1
        section1_values = extract_section1_values(uploaded_file)
        if section1_values:
            filtered_values = {
                "Valor Total (RRPP + No Inscrito) USD": section1_values["VALOR TOTAL (RRPP + NO INSCRITO)"][0],
                "Valor Total (RRPP + No Inscrito) S/": section1_values["VALOR TOTAL (RRPP + NO INSCRITO)"][1],
                "Valor de Realización (RRPP + No Inscrito) USD": section1_values["VALOR TOTAL (RRPP + NO INSCRITO)"][2],
                "Valor de Realización (RRPP + No Inscrito) S/": section1_values["VALOR TOTAL (RRPP + NO INSCRITO)"][3],
            }
        else:
            st.warning(f"No se encontraron valores en la Sección 1 del archivo {uploaded_file.name}")
            continue

        # Extraer valores de la Sección 2
        section2_values = extract_section2_values(uploaded_file)
        for key in section2_values:
            if section2_values[key]:
                section2_values[key] = float(section2_values[key].replace(",", ""))

        # Convertir valores de la Sección 1 a formato numérico
        for key in filtered_values:
            filtered_values[key] = float(filtered_values[key].replace(",", ""))

        # Comparar valores entre Sección 1 y Sección 2
        comparison_results = [
            {
                "Categoría": "Valor Comercial",
                "Moneda": "USD",
                "Valor 1 (RRPP + No Inscrito)": filtered_values["Valor Total (RRPP + No Inscrito) USD"],
                "Valor 2 (Oficial)": section2_values["Valor Comercial USD"],
                "Coincide": filtered_values["Valor Total (RRPP + No Inscrito) USD"] == section2_values["Valor Comercial USD"],
            },
            {
                "Categoría": "Valor Comercial",
                "Moneda": "S/",
                "Valor 1 (RRPP + No Inscrito)": filtered_values["Valor Total (RRPP + No Inscrito) S/"],
                "Valor 2 (Oficial)": section2_values["Valor Comercial S/"],
                "Coincide": filtered_values["Valor Total (RRPP + No Inscrito) S/"] == section2_values["Valor Comercial S/"],
            },
            {
                "Categoría": "Valor de Realización",
                "Moneda": "USD",
                "Valor 1 (RRPP + No Inscrito)": filtered_values["Valor de Realización (RRPP + No Inscrito) USD"],
                "Valor 2 (Oficial)": section2_values["Valor de Realización Inmediata USD"],
                "Coincide": filtered_values["Valor de Realización (RRPP + No Inscrito) USD"] == section2_values["Valor de Realización Inmediata USD"],
            },
            {
                "Categoría": "Valor de Realización",
                "Moneda": "S/",
                "Valor 1 (RRPP + No Inscrito)": filtered_values["Valor de Realización (RRPP + No Inscrito) S/"],
                "Valor 2 (Oficial)": section2_values["Valor de Realización Inmediata S/"],
                "Coincide": filtered_values["Valor de Realización (RRPP + No Inscrito) S/"] == section2_values["Valor de Realización Inmediata S/"],
            },
        ]

        # Mostrar tabla de comparación
        df_comparison = pd.DataFrame(comparison_results)
        st.dataframe(df_comparison)
