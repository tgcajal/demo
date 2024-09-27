import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
import streamlit as st
import hmac
import funciones as f
#users = ['test','user']
#passwords = ['t3$t!','u$3r!']
st.set_page_config(layout="wide")

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credenciales"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


if not check_password():
    st.stop()

#df, total, agg_df, mora_re, mora_total = f.transform('/Users/tgcajal/PycharmProjects/DemoBI/CASHFLOW.csv')
df = f.load_mora_df('mora.csv')
df_t = f.load_df_t('cashflow.csv', pais=None)

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
		col2.plotly_chart(f.histograma_moneda(df),use_container_width=True)

	st.plotly_chart(f.impagos_diarios(df_t),use_container_width=True)

	st.divider()

	st.header('Ingresos')
	col1, col2 = st.columns(2)

	col1.plotly_chart(f.ingresos_acumulados(df_t),use_container_width=True)
	col2.dataframe(df_t)

	st.divider()

	st.dataframe(agg_df)

with tab2:
	df = f.load_mora_df('mora.csv')
	df = df[df['pais']=='El Salvador']
	df_t = f.load_df_t('cashflow.csv',pais='El Salvador')

	agg_df = df.groupby(['pais', 'nombre_empresa', 'nombre_sucursal', 'vendedor', 'madurez'])[
		['id_credito', 'cuota', 'exigible_moneda', 'cuotas_pendientes', 'cuotas_totales']].agg({'id_credito': 'count',
																								'cuota': 'mean',
																								'exigible_moneda': 'sum',
																								'cuotas_pendientes': 'mean',
																								'cuotas_totales': 'mean'})

	with st.container():

		st.header('Clientes en mora')
		col1, col2 = st.columns(2)

		col1.plotly_chart(f.histograma_mora(df),use_container_width=True)
		col2.plotly_chart(f.histograma_moneda(df),use_container_width=True)
		#col2.dataframe(df_t)

	st.plotly_chart(f.impagos_diarios(df_t),use_container_width=True)

	st.divider()

	st.header('Ingresos')
	col1, col2 = st.columns(2)

	col1.plotly_chart(f.ingresos_acumulados(df_t),use_container_width=True)
	col2.dataframe(df_t)

	st.divider()
	st.dataframe(agg_df)

with tab3:
	df = f.load_mora_df('mora.csv')
	df = df[df['pais']=='Honduras']
	df_t = f.load_df_t('cashflow.csv', pais='Honduras')

	agg_df = df.groupby(['pais', 'nombre_empresa', 'nombre_sucursal', 'vendedor', 'madurez'])[
		['id_credito', 'cuota', 'exigible_moneda', 'cuotas_pendientes', 'cuotas_totales']].agg({'id_credito': 'count',
																								'cuota': 'mean',
																								'exigible_moneda': 'sum',
																								'cuotas_pendientes': 'mean',
																								'cuotas_totales': 'mean'})
	with st.container():

		st.header('Clientes en mora')
		col1, col2 = st.columns(2)

		col1.plotly_chart(f.histograma_mora(df),use_container_width=True)
		col2.plotly_chart(f.histograma_moneda(df),use_container_width=True)
		#col2.dataframe(df_t)

	st.plotly_chart(f.impagos_diarios(df_t),use_container_width=True)

	st.divider()

	st.header('Ingresos')
	col1, col2 = st.columns(2)

	col1.plotly_chart(f.ingresos_acumulados(df_t),use_container_width=True)
	col2.dataframe(df_t)

	st.divider()
	st.dataframe(agg_df)
