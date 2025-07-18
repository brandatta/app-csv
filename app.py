import streamlit as st
import pandas as pd
import mysql.connector
import tempfile
import os

st.set_page_config(page_title="Subida CSV ABI", layout="centered")
st.title("Subida de CSV")

# HTML + CSS + JS para uploader en español
st.markdown("""
<style>
/* Oculta el uploader de Streamlit completamente */
div[data-testid="stFileUploader"] {
    display: none;
}
/* Estilo botón en español */
#custom-uploader {
    display: flex;
    flex-direction: column;
    align-items: start;
    margin-bottom: 1rem;
}
#file-label {
    background-color: #2185d0;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
}
#file-label:hover {
    background-color: #1678c2;
}
#file-input {
    display: none;
}
</style>

<div id="custom-uploader">
    <label id="file-label" for="file-input">Elegir archivo</label>
    <input type="file" id="file-input" accept=".csv,.xlsx" />
</div>

<script>
const fileInput = window.parent.document.querySelector('input[type=file]');
const customInput = window.parent.document.getElementById('file-input');
if (fileInput && customInput) {
    customInput.addEventListener('change', () => {
        const file = customInput.files[0];
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    });
}
</script>
""", unsafe_allow_html=True)

# Uploader oculto pero funcional
uploaded_file = st.file_uploader("", type=["csv", "xlsx"], label_visibility="collapsed")

if uploaded_file:
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
            temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', encoding='utf-8')
            df.to_csv(temp_csv.name, index=False)
            temp_csv.close()

            conn = mysql.connector.connect(
                host=st.secrets["DB_HOST"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                database=st.secrets["DB_NAME"],
                allow_local_infile=True
            )
            cursor = conn.cursor()

            cursor.execute("TRUNCATE TABLE test_infile_abi")

            load_query = f"""
            LOAD DATA LOCAL INFILE '{temp_csv.name.replace('\\\\', '\\\\')}'
            INTO TABLE test_infile_abi
            FIELDS TERMINATED BY ',' ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
            IGNORE 1 ROWS;
            """
            cursor.execute(load_query)

            cursor.execute("CALL update_ep()")

            conn.commit()
            cursor.close()
            conn.close()
            os.remove(temp_csv.name)

            st.success("Archivo subido, tabla actualizada y procedimiento ejecutado.")
        except Exception as e:
            st.error(f"Error: {e}")
