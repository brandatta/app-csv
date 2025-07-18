import streamlit as st
import pandas as pd
import mysql.connector
import tempfile
import os

st.set_page_config(page_title="Subida CSV ABI", layout="centered")
st.title("Subida de CSV")

# Subí tu archivo con texto en español
st.markdown("## Subí tu archivo CSV o Excel (máximo 200MB):")

# Subida de archivo
uploaded_file = st.file_uploader("", type=["csv", "xlsx"], label_visibility="collapsed")

if uploaded_file:
    # Leer archivo
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)

    st.write("Vista previa del archivo:")
    st.dataframe(df.head())

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        selected_col = st.selectbox("Seleccioná una columna para ver la suma:", numeric_cols)
        suma = df[selected_col].sum()
        st.info(f"Suma de la columna **{selected_col}**: **{suma:.2f}**")
    else:
        st.warning("No hay columnas numéricas.")

    if st.button("Confirmar Subida"):
        try:
            # Guardar archivo temporal
            temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', encoding='utf-8')
            df.to_csv(temp_csv.name, index=False)
            temp_csv.close()

            # Conexión
            conn = mysql.connector.connect(
                host=st.secrets["DB_HOST"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                database=st.secrets["DB_NAME"],
                allow_local_infile=True
            )
            cursor = conn.cursor()

            # TRUNCATE tabla destino
            cursor.execute("TRUNCATE TABLE test_infile_abi")

            # Cargar CSV con LOAD DATA
            load_query = f"""
            LOAD DATA LOCAL INFILE '{temp_csv.name.replace('\\\\', '\\\\')}'
            INTO TABLE test_infile_abi
            FIELDS TERMINATED BY ',' ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
            IGNORE 1 ROWS;
            """
            cursor.execute(load_query)

            # Ejecutar SP
            cursor.execute("CALL update_ep()")

            conn.commit()
            cursor.close()
            conn.close()
            os.remove(temp_csv.name)

            st.success("Archivo subido, tabla actualizada y procedimiento ejecutado.")

        except Exception as e:
            st.error(f"Error: {e}")
