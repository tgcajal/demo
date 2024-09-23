import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
import streamlit as st
import funciones as f

st.set_page_config(layout="wide")

#df, total, agg_df, mora_re, mora_total = f.transform('/Users/tgcajal/PycharmProjects/DemoBI/CASHFLOW.csv')
df = f.load_mora_df('/Users/tgcajal/PycharmProjects/DemoBI/mora.csv')
df_t = f.load_df_t('/Users/tgcajal/PycharmProjects/DemoBI/cashflow.csv')

agg_df = df.groupby(['pais','nombre_empresa','nombre_sucursal','vendedor','madurez'])[['id_credito','cuota','exigible_moneda','cuotas_pendientes','cuotas_totales']].agg({'id_credito':'count',
																																					   'cuota':'mean',
																																					   'exigible_moneda':'sum',
																																					   'cuotas_pendientes':'mean',
																																					   'cuotas_totales':'mean'})

st.title('Reporte de Mora')
# Mostrar fechas

tab1, tab2, tab3 = st.tabs(['Total','El Salvador','Honduras'])

with tab1:

	with st.container():

		st.header('Clientes en mora')
		col1, col2 = st.columns(2)

		col1.plotly_chart(f.histograma_mora(df),use_container_width=True)
		col2.dataframe(df_t)

	st.plotly_chart(f.impagos_diarios(df_t),use_container_width=True)

	#tabla_mora_usd = pd.DataFrame(mora_re.groupby('num_cuota')[['Cantidad','Exigible Total']].sum())
	#tabla_mora_usd['Exigible Total'] = [str('$ ')+str(round(value,2)) for value in tabla_mora_usd['Exigible Total']]
	#tabla_mora_usd.index = ['Mora 15', 'Mora 30', 'Mora 45']

	#df_t, chart_t = f.imago_time(df)

	#col1.write('Chart monto')
	#col1.plotly_chart(f.mora_madurez_usd(mora_re), use_container_width=True)

	#col2.table(tabla_mora_usd)
	#col2.plotly_chart(chart_t, use_container_width=True)

	st.divider()

	st.header('Ingresos')
	col1, col2 = st.columns(2)

	col1.plotly_chart(f.ingresos_acumulados(df_t),use_container_width=True)
	col2.dataframe(df_t)

	#col1.write('Comparación por país chart')
	#col1.plotly_chart(f.comparacion(mora_re), use_container_width=True)
	#col2.write('Comparación por país tabla')

	st.divider()

	st.header('Relación al total')
	col1, col2 = st.columns(2)

	col1.write('Chart de todos los clientes')
	col2.write('Tabla de todos los clientes')






