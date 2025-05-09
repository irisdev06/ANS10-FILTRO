# app_completa.py
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import datetime
import math
st.set_page_config(page_title="Procesos ANS10", page_icon="🧪")

# Sidebar para seleccionar proceso
st.sidebar.title("🔧 Menú de Procesos")
opcion = st.sidebar.selectbox("Selecciona el proceso que quieres ejecutar:", ["📅 Filtro por Fechas de Corte", "📊 Muestreo"])

# ----------------------------------------------------------------------
# PROCESO 1: FILTRO POR FECHAS (Código 1)
# ----------------------------------------------------------------------
if opcion == "📅 Filtro por Fechas de Corte":
    st.title("🔍 Filtro ANS10 - Notificación Efectiva por Fecha")

    archivo = st.file_uploader("📤 Sube el archivo Excel (.xlsx)", type=["xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha de inicio", value=datetime.date(datetime.datetime.today().year, 1, 1), disabled=st.session_state.get("processing", False))
    with col2:
        fecha_fin = st.date_input("📅 Fecha de fin", value=datetime.date.today(), disabled=st.session_state.get("processing", False))

    ejecutar_filtro = st.button("🔍 Ejecutar Filtro", key="filtro", use_container_width=True, disabled=st.session_state.get("processing", False))

    if ejecutar_filtro:
        st.session_state.processing = True

        with st.spinner('Filtrando los datos...'):
            if archivo:
                try:
                    df_dto = pd.read_excel(archivo, sheet_name="DTO")
                    df_pcl = pd.read_excel(archivo, sheet_name="PCL")

                    for df in [df_dto, df_pcl]:
                        df["FECHA_VISADO"] = pd.to_datetime(df["FECHA_VISADO"], errors="coerce")

                    dto_filtrado = df_dto[
                        (df_dto["ESTADO_INFORME"] == "NOTIFICACIÓN EFECTIVA") &
                        (df_dto["FECHA_VISADO"] >= pd.to_datetime(fecha_inicio)) &
                        (df_dto["FECHA_VISADO"] <= pd.to_datetime(fecha_fin))
                    ]
                    pcl_filtrado = df_pcl[
                        (df_pcl["ESTADO_INFORME"] == "NOTIFICACIÓN EFECTIVA") &
                        (df_pcl["FECHA_VISADO"] >= pd.to_datetime(fecha_inicio)) &
                        (df_pcl["FECHA_VISADO"] <= pd.to_datetime(fecha_fin))
                    ]

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        dto_filtrado.to_excel(writer, sheet_name="ANS10_DTO", index=False)
                        pcl_filtrado.to_excel(writer, sheet_name="ANS10_PCL", index=False)

                        workbook = writer.book
                        for sheet, df in zip(["ANS10_DTO", "ANS10_PCL"], [dto_filtrado, pcl_filtrado]):
                            worksheet = writer.sheets[sheet]
                            worksheet.add_table(0, 0, len(df), len(df.columns)-1, {
                                'name': f'Tabla_{sheet}',
                                'columns': [{'header': col} for col in df.columns],
                                'style': 'Table Style Medium 9'
                            })

                    output.seek(0)
                    st.success(f"✅ Archivo filtrado listo para el rango de fechas: {fecha_inicio} - {fecha_fin}")
                    st.download_button(
                        label="📥 Descargar Excel Filtrado",
                        data=output,
                        file_name=f"ANS10_Filtrado_{fecha_inicio}_{fecha_fin}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ No se ha cargado un archivo válido.")

        st.session_state.processing = False

# ----------------------------------------------------------------------
# PROCESO 2: ANÁLISIS Y MUESTREO (Código 2)
# ----------------------------------------------------------------------
elif opcion ==  "📊 Muestreo":
    st.title("Muestra 🔎")
    uploaded_file = st.file_uploader("Sube tu archivo Excel para Analizar. ⏫", type=["xlsx"])

    if uploaded_file is not None:
        excel_data = pd.ExcelFile(uploaded_file)
        sheet_names = excel_data.sheet_names

        st.write(f"📚 En el libro de Excel están las hojas: {', '.join(sheet_names)}")

        seleccion_manual_hoja = st.radio("¿Quieres seleccionar una hoja específica para analizar?", ['No', 'Sí'], horizontal=True)

        if seleccion_manual_hoja == 'Sí':
            hoja_seleccionada = st.selectbox("📄 Selecciona una hoja para analizar", sheet_names)
            hojas_a_analizar = [hoja_seleccionada]
        else:
            hojas_a_analizar = sheet_names

        if hojas_a_analizar:
            data_completa = pd.DataFrame()
            for hoja in hojas_a_analizar:
                try:
                    df = pd.read_excel(uploaded_file, sheet_name=hoja)
                    df['__HOJA__'] = hoja
                    data_completa = pd.concat([data_completa, df], ignore_index=True)
                except Exception as e:
                    st.warning(f"⚠️ Error leyendo la hoja '{hoja}': {e}")

            if 'NOTIFICADOR' in data_completa.columns:
                notificadores = data_completa['NOTIFICADOR'].dropna().unique()

                notificadores_seleccionados = st.multiselect("Selecciona uno o más notificadores:", notificadores, default=[])

                if not notificadores_seleccionados:
                    st.warning("👆 No seleccionaste notificadores, por lo que se tomarán todos los notificadores automáticamente.")
                    notificadores_seleccionados = notificadores
                    st.markdown("<h2 style='font-size:28px;'>👩🏽👨🏽Los notificadores disponibles son:</h2>", unsafe_allow_html=True)

                total_conteo = 0
                for notificador in notificadores_seleccionados:
                    conteo = (data_completa['NOTIFICADOR'] == notificador).sum()
                    st.write(f"📌 '{notificador}' tiene {conteo} registros en total.")
                    total_conteo += conteo

                st.write(f"📊 Total de registros combinados para los notificadores seleccionados: **{total_conteo}**")

                resumen = []
                for hoja in hojas_a_analizar:
                    df = pd.read_excel(uploaded_file, sheet_name=hoja)
                    if 'NOTIFICADOR' in df.columns:
                        conteo = df['NOTIFICADOR'].value_counts().reset_index()
                        conteo.columns = ['NOTIFICADOR', 'TOTAL']
                        conteo['HOJA'] = hoja
                        resumen.append(conteo)

                if resumen:
                    df_final = pd.concat(resumen)
                    df_final = df_final[df_final['NOTIFICADOR'].isin(notificadores_seleccionados)]
                    tabla_dinamica = df_final.pivot_table(index='HOJA', columns='NOTIFICADOR', values='TOTAL', aggfunc='sum', fill_value=0)
                    tabla_dinamica.loc['Total general'] = tabla_dinamica.sum()

                    st.write("### 🧮 Resumen Notificadores")
                    st.dataframe(tabla_dinamica)
                else:
                    st.warning("⚠️ No se encontraron datos válidos con 'NOTIFICADOR' en las hojas seleccionadas.")

                z = 1.96
                e = 0.05
                p = 0.5

                st.write("## 🧪 Cálculo del tamaño de muestra por notificador (95-5)")

                tablas_notificadores = {}
                indicadores_hojas = {}

                for notificador in notificadores_seleccionados:
                    df_notificador = data_completa[data_completa['NOTIFICADOR'] == notificador].copy()
                    df_notificador = df_notificador.drop_duplicates()
                    N = len(df_notificador)

                    if N == 0:
                        continue

                    numerador = N * (z ** 2) * p * (1 - p)
                    denominador = ((e ** 2) * (N - 1)) + ((z ** 2) * p * (1 - p))
                    n = min(math.ceil(numerador / denominador), N)

                    datos = pd.DataFrame()

                    if notificador == "UTMDL":
                        df_notificador['EMPRESA'] = df_notificador['EMPRESA'].astype(str).str.lower()
                        pattern_fiscalia = r'\b[fph][iy1]sc[aá]l[il1y][aáe]?\b'

                        df_fiscalia = df_notificador[df_notificador['EMPRESA'].str.contains(pattern_fiscalia, na=False, regex=True)]
                        df_otros = df_notificador[~df_notificador['EMPRESA'].str.contains(pattern_fiscalia, na=False, regex=True)]

                        if not df_fiscalia.empty:
                            st.info("👮‍♀️ Se encontraron registros de Fiscalía para el notificador UTMDL. Se tomará una muestra con 25% Fiscalía y 75% otras empresas.")
                        else:
                            st.warning("⚠️ No se encontraron registros de Fiscalía para UTMDL. Se tomará el 100% de la muestra desde otras empresas.")

                        n_fisc = max(1, math.ceil(n * 0.25)) if len(df_fiscalia) > 0 else 0
                        n_otros = n - n_fisc

                        datos_fisc = df_fiscalia.sample(n=n_fisc, random_state=42) if n_fisc > 0 else pd.DataFrame()
                        datos_otros = df_otros.sample(n=n_otros, random_state=42) if n_otros > 0 else pd.DataFrame()
                        datos = pd.concat([datos_fisc, datos_otros])
                    else:
                        datos = df_notificador.sample(n=n, random_state=42)

                    datos['OPORTUNIDAD FINAL'] = ""
                    datos['OBSERVACIÓN'] = ""
                    datos['DEFINICIÓN'] = ""

                    columnas_finales = [
                        'ID_FURAT_FUREP', 'TIPO_DE_CALIFICACIÓN', 'ID_TRABAJADOR',
                        'FECHA_VISADO', 'FECHA_NOTIFICACION', 'ESTADO_INFORME',
                        'EMPRESA', 'NOTIFICADOR', 'OPORTUNIDAD FINAL',
                        'OBSERVACIÓN', 'DEFINICIÓN'
                    ]
                    datos = datos[[col for col in columnas_finales if col in datos.columns]]

                    tabla = pd.DataFrame({
                        'NOTIFICADOR': [notificador],
                        'POBLACIÓN (N)': [N],
                        'MUESTRA REQUERIDA (n)': [n],
                        'MARGEN DE ERROR (%)': [5.0]
                    })

                    st.subheader(f"📊 {notificador}")
                    st.dataframe(tabla)

                    st.markdown("#### 🎯 Datos seleccionados")
                    st.dataframe(datos)

                    tablas_notificadores[notificador] = {
                        'resumen': tabla,
                        'datos': datos
                    }

                    medicion = (n / n) * 100
                    indicador_df = pd.DataFrame({
                        'Indicador': ['Calidad de notificaciones'],
                        'Numerador': [n],
                        'Denominador': [n],
                        'Medición': [f"{medicion:.2f}%"],
                        'Meta': [f"{98.00:.2f}%"]
                    })
                    indicadores_hojas[notificador] = indicador_df

                    st.markdown("#### 📈 Indicador de Calidad")
                    st.dataframe(indicador_df)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    for notificador, data in tablas_notificadores.items():
                        data['resumen'].to_excel(writer, sheet_name=f'{notificador}_Resumen', index=False)
                        data['datos'].to_excel(writer, sheet_name=f'datos_{notificador}', index=False)
                        indicadores_hojas[notificador].to_excel(writer, sheet_name=f'{notificador}_Indicador', index=False)

                    if resumen:
                        tabla_dinamica.to_excel(writer, sheet_name='Resumen Notificadores')

                output.seek(0)

                st.download_button(
                    label="📥 Descargar todas las tablas (notificadores, datos e indicadores) en Excel",
                    data=output,
                    file_name="reporte_datos_completo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("🚫 No se encontró la columna 'NOTIFICADOR' en los datos cargados.")
        else:
            st.info("👆 Por favor, selecciona una opción para proceder.")
    else:
        st.info("Por favor, sube un archivo Excel para comenzar.")
