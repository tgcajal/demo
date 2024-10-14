import pandas as pd 
import numpy as np
import datetime
from datetime import datetime, timedelta

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
    df['semana'] = df['fecha_solicitud'].dt.week
    df['cosecha_semana'] = df['semana'].astype(str)
    df['saldo_real'] = df['saldo_esperado'] + df['monto_cuota']*df['cuotas_pendientes']
    df['pago'] = [1 if estado in ['Pagado Retraso','Pagado a Tiempo'] else 0 for estado in df['estado']]
    df['Mora'] = df['cuotas_pendientes'].map({0: 'Al día',
                                          1:'Mora 1',
                                          2:'Mora 2',
                                          3:'Mora 3',
                                          4:'Mora 4'})
    
    df['Mora'] = df['Mora'].where(df['pago']==0, 'Pagado')

    return df


def index_chain_transform(mora_csv,cashflow_csv):

    mora  = pd.read_csv('mora.csv')
    cashflow = pd.read_csv('cashflow.csv')

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

    merged['semana'] = merged['fecha_solicitud'].dt.week
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
    ejemplo_['semana_cosecha'] = ejemplo_['fecha_solicitud'].dt.week
    ejemplo_['deuda'] = ejemplo_['monto_cuota'] - ejemplo_['pagado']

    data = ejemplo_.groupby(['vendedor','semana_cosecha']).sum()
    data['tasa_impago'] = 1 - data['fecha_pago']/data['id_credito']

    return data