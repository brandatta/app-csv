import streamlit as st
import pandas as pd
import mysql.connector
import tempfile
import os
import base64
from PIL import Image
import io

# ------------- Función para convertir la imagen a base64 -------------
def get_base64_image(image_path: str) -> str:
    """Convierte una imagen PNG a una cadena base64."""
    img = Image.open(image_path).resize((40, 40))        # redimensiona a 40 px de alto
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

logo_base64 = get_base64_image("logorelleno.png")        # asegúrate de que exista

# ------------------ Configuración general de la página ----------------
st.set_page_config(page_title="Subida CSV", layout="centered")

# ----------------------------- Encabezado -----------------------------
st.markdown(f"""
<style>
/* Barra fija */
.header-container {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background-color: #f0f2f6;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #ddd;
    z-index: 1000;
}}
.header-container img {{
    height: 40px;
    margin-right: 15px;
}}
.header-title {{
    font-size: 24px;
    font-weight: bold;
    color: #31333F;
}}
/* Espacio para que el contenido no quede oculto */
.main-content {{
    margin-top: 80px;
}}
</style>

<div class="header-container">
    <img src="data:image/png;base64,{logo_base64}" />
    <div class="header-title">Subida de CSV</div>
</div>
""", unsafe_allow_html=True)

# --------------------- Comienza el contenido real ---------------------
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Ocultar el texto en inglés del file_uploader
st.markdown("""
    <style>
    div[data-testid="stFileUploader"] > label > div:first-child {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("### Subí tu archivo CSV o Excel (máximo 200 MB):")
uploaded_file = st.file_uploader("", type=["csv", "xlsx"], label_visibility="collapsed")

if uploaded_file:
    # ---------- Lectura del archivo ----------
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:  # .xlsx
        df = pd.read_excel(uploaded_file)

    st.write("Vista previa del archivo:")
    st.dataframe(df.head())

    # ---------- Selección de columna y suma ----------
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        selected_col = st.selectbox("Seleccioná una columna para ver la suma:", numeric_cols)
        suma = df[selected_col].sum()
        st.info(f"Suma de la columna **{selected_col}**: **{suma:.2f}**")
    else:
        st.warning("No hay columnas numéricas.")

    # ---------- Confirmar subida ----------
    if st.button("Confirmar Subida"):
        try:
            # Guardar DataFrame como CSV temporal
            temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8")
            df.to_csv(temp_csv.name, index=False)
            temp_csv.close()

            # Conexión a MySQL
            conn = mysql.connector.connect(
                host=st.secrets["DB_HOST"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                database=st.secrets["DB_NAME"],
                allow_local_infile=True,
            )
            cursor = conn.cursor()

            # Truncar tabla y cargar datos
            cursor.execute("TRUNCATE TABLE test_infile_abi")
            load_query = f"""
                LOAD DATA LOCAL INFILE '{temp_csv.name.replace('\\\\', '\\\\')}'
                INTO TABLE test_infile_abi
                FIELDS TERMINATED BY ',' ENCLOSED BY '"'
                LINES TERMINATED BY '\\n'
                IGNORE 1 ROWS;
            """
            cursor.execute(load_query)

            # Ejecutar procedimiento almacenado
            cursor.execute("CALL update_ep()")

            conn.commit()
            cursor.close()
            conn.close()
            os.remove(temp_csv.name)

            st.success("Archivo subido, tabla actualizada y procedimiento ejecutado.")
        except Exception as e:
            st.error(f"Error: {e}")

# Cerrar div del contenido principal
st.markdown("</div>", unsafe_allow_html=True)
