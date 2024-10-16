import pandas as pd 
import numpy as np
import datetime
from datetime import datetime, timedelta
import plotly 
import plotly.express as px 
import plotly.graph_objects as go

import streamlit as st

def transform(mora_csv, cashflow_csv):

    mora  = pd.read_csv('mora.csv')
    cashflow = pd.read_csv('cashflow.csv')
    
    today = datetime.today()

    mora_df = mora[['id_credito','fecha_solicitud','cuotas_pendientes','vendedor','nombre_empresa','nombre_sucursal']].sort_values(by='cuotas_pendientes',ascending=False)
    mora_df['fecha_solicitud'] = pd.to_datetime(mora_df['fecha_solicitud'])
    mora_df['edad_D'] = [(today - date).days for date in mora_df['fecha_solicitud']]

    cashflow_df = cashflow[['id_credito','estado','num_cuota','fecha_cuota','saldo_total','monto_cuota','saldo_exigible','fecha_pago','pais']]
    cashflow_df['fecha_cuota'] = pd.to_datetime(cashflow_df['fecha_cuota'])
    cashflow_df['fecha_pago'] = pd.to_datetime(cashflow_df['fecha_pago'])
    cashflow_df['pagado'] = cashflow_df['monto_cuota'].where(cashflow_df['estado'].isin(['Pagado a Tiempo','Pago Retraso']),0)
    cashflow_df['edad_D'] = cashflow_df['num_cuota'] * 15

    df = mora_df.merge(cashflow_df, how='inner', on=['id_credito'])
    df.rename(columns={'edad_D_x':'edad_actual_D',
                   'edad_D_y':'edad_D',
                   'saldo_total':'saldo_esperado'}, inplace=True)
    df['semana'] = df['fecha_solicitud'].dt.isocalendar().week
    df['cosecha_semana'] = df['semana'].astype(str)
    df['saldo_real'] = df['saldo_esperado'] + df['monto_cuota']*df['cuotas_pendientes']
    df['pago'] = [1 if estado in ['Pagado Retraso','Pagado a Tiempo'] else 0 for estado in df['estado']]
    df['Mora'] = df['cuotas_pendientes'].map({0: 'Al día',
                                          1:'Mora 1',
                                          2:'Mora 2',
                                          3:'Mora 3',
                                          4:'Mora 4'})
    
    df['Mora'] = df['Mora'].where(df['pago']==0, 'Pagado')

    return df, mora_df, cashflow_df


def index_chain_transform(mora_csv,cashflow_csv):

    mora  = pd.read_csv(mora_csv)
    cashflow = pd.read_csv(cashflow_csv)

    merged= cashflow.merge(mora, how='left', on='id_credito')
    today = datetime.today()
    
    merged['fecha_solicitud'] = pd.to_datetime(merged['fecha_solicitud'])
    merged['edad_D'] = [(today - date).days for date in merged['fecha_solicitud']]
    
    merged['fecha_cuota'] = pd.to_datetime(merged['fecha_cuota'])
    merged['fecha_pago'] = pd.to_datetime(merged['fecha_pago'])
    merged['pagado'] = merged['monto_cuota'].where(merged['estado'].isin(['Pagado a Tiempo','Pago Retraso']),0)
    merged['edad_D'] = merged['num_cuota'] * 15

    merged.rename(columns={'edad_D_x':'edad_actual_D',
                'edad_D_y':'edad_D'},
                #'saldo_total':'saldo_esperado'}, 
                inplace=True)

    merged['semana'] = merged['fecha_solicitud'].dt.isocalendar().week
    merged['cosecha_semana'] = merged['semana'].astype(str)
    merged['pago'] = [1 if estado in ['Pagado Retraso','Pagado a Tiempo'] else 0 for estado in merged['estado']]
    merged['Mora'] = merged['cuotas_pendientes'].map({0: 'Al día',
                                            1:'Mora 1',
                                            2:'Mora 2',
                                            3:'Mora 3',
                                            4:'Mora 4'})

    merged['Mora'] = merged['Mora'].where(merged['pago']==0, 'Pagado')

    merged_ = merged[merged['fecha_cuota']<np.datetime64('2024-10-05 00:00:00')]

    ejemplo = merged_.groupby(['Mora','pais_x','nombre_empresa','nombre_sucursal','vendedor','fecha_cuota','fecha_solicitud'])[['id_credito','fecha_pago','monto_cuota','pagado']].agg({'id_credito':'count',
                                                                                                  'fecha_pago':'count',
                                                                                                  'monto_cuota':'sum',
                                                                                                  'pagado':'sum'})
    ejemplo_ = ejemplo.reset_index()
    ejemplo_.drop_duplicates(subset=['Mora','vendedor','fecha_solicitud','id_credito','fecha_pago','monto_cuota'],keep='first',inplace=True)
    ejemplo_['fecha_solicitud'] = pd.to_datetime(ejemplo_['fecha_solicitud'])
    ejemplo_['semana_cosecha'] = ejemplo_['fecha_solicitud'].dt.isocalendar().week
    ejemplo_['deuda'] = ejemplo_['monto_cuota'] - ejemplo_['pagado']
    ejemplo_['semana_cosecha'] = ejemplo_['semana_cosecha'].astype(int)

    data = ejemplo_.groupby(['vendedor','semana_cosecha'])[ejemplo_.select_dtypes('number').columns].sum()
    data['tasa_impago'] = 1 - data['fecha_pago']/data['id_credito']

    return data
##############


##############

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df 
    

df = pd.DataFrame()
df = df.copy()

# Try to convert datetimes into a standard format (datetime, no timezone)
for col in df.columns:
    if pd.api.types.is_object_dtype(df[col]):
        try:
            df[col] = pd.to_datetime(df[col])
        except Exception:
            pass
        
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)



modification_container = st.container()

with modification_container:
    to_filter_columns = st.multiselect("Filter por: ", df.columns)

for column in to_filter_columns:
    left, right = st.columns((1, 20))
    left.write("↳")

    # Treat columns with < 10 unique values as categorical
    if pd.api.types.is_categorical_dtype(df[column]) or df[column].nunique() < 10:
        user_cat_input = right.multiselect(
            f"Valores {column}",
            df[column].unique(),
            default=list(df[column].unique()),
        )
        df = df[df[column].isin(user_cat_input)]

    elif pd.api.types.is_numeric_dtype(df[column]):
        _min = float(df[column].min())
        _max = float(df[column].max())
        step = (_max - _min) / 100
        user_num_input = right.slider(
        f"Values for {column}",
        min_value=_min,
        max_value=_max,
        value=(_min, _max),
        step=step,
        )
        df = df[df[column].between(*user_num_input)]

    elif pd.api.types.is_datetime64_any_dtype(df[column]):
        user_date_input = right.date_input(
            f"Valores for {column}",
            value=(
                df[column].min(),
                df[column].max(),
            ),
        )
        if len(user_date_input) == 2:
            user_date_input = tuple(map(pd.to_datetime, user_date_input))
            start_date, end_date = user_date_input
            df = df.loc[df[column].between(start_date, end_date)]

    else:
        user_text_input = right.text_input(
            f"Substring or regex in {column}",
        )
        if user_text_input:
            df = df[df[column].astype(str).str.contains(user_text_input)]


##########
#Latest transform

def prep(mora, cashflow):

    mora = pd.read_csv(mora)
    cashflow=pd.read_csv(cashflow)

    cashflow['fecha_cuota'] = pd.to_datetime(cashflow['fecha_cuota'])
    mora['fecha_solicitud'] = pd.to_datetime(mora['fecha_solicitud'])

    cashflow['estado_pago'] = cashflow['estado'].map({'Pagado a Tiempo':'Pagado',
                                                  'Pagado Retraso':'Pagado',
                                                  'Vencido':'Impago',
                                                  'Exigible':'Al día',
                                                  'Fijo':'Al día'})

    grouped = cashflow.groupby(['pais','estado_pago','id_credito','num_cuota','fecha_cuota'])[['id_amortizacion','monto_cuota']].agg({'id_amortizacion':'count',
                                                                                                                   'monto_cuota':'sum'}).sort_index(level=[3,4]).reset_index()

    grouped['recibido'] = grouped['estado_pago'].map({'Pagado':1,
                                                  'Impago':0})
    grouped['monto_recibido'] = grouped['recibido'] * grouped['monto_cuota']

    grouped.sort_values(by=['id_credito','num_cuota'],inplace=True)
    grouped['monto_esperado'] = grouped.groupby('id_credito')['monto_cuota'].cumsum()
    grouped['monto_recibido_acumulado'] = grouped.groupby('id_credito')['monto_recibido'].cumsum()
    grouped['pagos_esperados'] = grouped.groupby(['id_credito'])['id_amortizacion'].cumsum()
    grouped['recibido_acumulado'] = grouped.groupby('id_credito')['recibido'].cumsum()
    grouped['cuotas_pendientes'] = (grouped['pagos_esperados'] - grouped['recibido_acumulado'].fillna(0)).astype(int)
    grouped['mora'] = 'Mora '+grouped['cuotas_pendientes'].astype(str)
    grouped['mora'] = grouped['mora'].where(grouped['estado_pago']=='Impago','Al día')
    grouped['mora'] = grouped['mora'].where(grouped['estado_pago']!='Pagado','Pagado')
    grouped['semana_cosecha'] = grouped['fecha_cuota'] - timedelta(15)
    grouped['semana_cosecha'] = grouped['semana_cosecha'].where(grouped['num_cuota']==1, 0)

    data = grouped.merge(mora[['id_credito','fecha_solicitud','nombre_empresa','nombre_sucursal','vendedor']], how='left', on='id_credito')

    return data