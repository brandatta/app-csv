import streamlit as st
import pandas as pd
import mysql.connector
import tempfile
import os
from PIL import Image
import base64
import io

st.set_page_config(page_title="Subida CSV ABI", layout="centered")

# Convertir logo a base64
def get_base64_logo(path="logorelleno.png"):
    try:
        img = Image.open(path).resize((40, 40))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None

logo_b64 = get_base64_logo()

# Estilos personalizados
st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0rem;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 2px 0 10px 0;
        border-bottom: 2px solid #d4fdb7;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 24px;
        font-weight: bold;
        color: #d4fdb7;
    }
    .header-logo img {
        height: 40px;
    }
    button[kind="primary"] {
        background-color: #64352c !important;
        border-color: #64352c !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #4f2923 !important;
        border-color: #4f2923 !important;
    }
    .stAlert[data-baseweb="alert"] {
        border-left: 6px solid #d4fdb7;
        background-color: #f6fff0;
        color: #64352c !important;
        font-weight: bold;
    }
    label, .stSelectbox label, .stFileUploader label {
        color: #64352c !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
if logo_b64:
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">Subida de CSV</div>
        <div class="header-logo">
            <img src="data:image/png;base64,{logo_b64}" />
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="header-container">
        <div class="header-title">Subida de CSV</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- LÓGICA PRINCIPAL --------------------

uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv", "xlsx"])

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
            LINES TERMINATED BY '\n'
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
import streamlit as st
import pandas as pd
import mysql.connector
import tempfile
import os
from PIL import Image
import base64
import io

st.set_page_config(page_title="Subida CSV ABI", layout="centered")

# Convertir logo a base64
def get_base64_logo(path="logorelleno.png"):
    try:
        img = Image.open(path).resize((40, 40))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None

logo_b64 = get_base64_logo()

# Estilos personalizados
st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0rem;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 2px 0 10px 0;
        border-bottom: 2px solid #d4fdb7;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 24px;
        font-weight: bold;
        color: #d4fdb7;
    }
    .header-logo img {
        height: 40px;
    }
    button[kind="primary"] {
        background-color: #64352c !important;
        border-color: #64352c !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #4f2923 !important;
        border-color: #4f2923 !important;
    }
    .stAlert[data-baseweb="alert"] {
        border-left: 6px solid #d4fdb7;
        background-color: #f6fff0;
        color: #64352c !important;
        font-weight: bold;
    }
    label, .stSelectbox label, .stFileUploader label {
        color: #64352c !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
if logo_b64:
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">Subida de CSV</div>
        <div class="header-logo">
            <img src="data:image/png;base64,{logo_b64}" />
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="header-container">
        <div class="header-title">Subida de CSV</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- LÓGICA PRINCIPAL --------------------

uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv", "xlsx"])

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
            LINES TERMINATED BY '\n'
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
