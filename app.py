import streamlit as st
import pandas as pd
import mysql.connector
import tempfile
import os
from PIL import Image
import base64
import io

# Configurar página
st.set_page_config(page_title="Subida CSV", layout="centered")

# Función para cargar imagen como base64
def get_base64_logo(path="logorelleno.png"):
    try:
        img = Image.open(path).resize((40, 40))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        return None

logo_b64 = get_base64_logo()

# Mostrar encabezado fijo
st.markdown("""
    <style>
    .header-container {
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
    }
    .header-container img {
        height: 40px;
        margin-right: 15px;
    }
    .header-title {
        font-size: 24px;
        font-weight: bold;
        color: #31333F;
    }
    .main-content {
        margin-top: 80px;
    }
    </style>
""", unsafe_allow_html=True)

# Mostrar logo o solo texto
if logo_b64:
    st.markdown(f"""
    <div class="header-container">
        <img src="data:image/png;base64,{logo_b64}" />
        <div class="header-title">Subida de CSV</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">Subida de CSV</div>
    </div>
    """, unsafe_allow_html=True)

# ---------- CONTENIDO PRINCIPAL ----------
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Ocultar texto original del uploader
st.markdown("""
    <style>
    div[data-testid="stFileUploader"] > label > div:first-child {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("### Subí tu archivo CSV o Excel (máximo 200MB):")
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

st.markdown("</div>", unsafe_allow_html=True)
