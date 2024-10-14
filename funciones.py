import numpy as np
import pandas as pd
import datetime
from datetime import datetime
import plotly
import plotly.express as px
import plotly.graph_objects as go

# Crear df de csv
def load_mora_df(file):
	df = pd.read_csv(file)

	df['saldo_total'] = df['saldo_total'].where(df['pais'] == 'El Salvador', df['saldo_total'] / 25)
	df['exigible_moneda'] = df['exigible_moneda'].where(df['pais'] == 'El Salvador', df['exigible_moneda'] / 25)

	df['fecha_solicitud'] = pd.to_datetime(df['fecha_solicitud'])
	df['fecha_ultimo_pago'] = pd.to_datetime(df['fecha_ultimo_pago'])
	df['fecha_mora'] = pd.to_datetime(df['fecha_mora'])
	df['fecha_proxima_cuota'] = pd.to_datetime(df['fecha_proxima_cuota'])

	df['madurez'] = 'Mora ' + (df['cuotas_pendientes'] * 15).astype(str)

	return df


def load_df_t(file, pais=None):
	df_cashflow = pd.read_csv(file)

	if pais:
		df_cashflow = df_cashflow[df_cashflow['pais'] == pais]
	else:
		df_cashflow = df_cashflow

	df_cashflow['impago'] = [1 if x == 'Vencido' else 0 for x in df_cashflow['estado']]
	df_cashflow['pagado'] = df_cashflow['monto_cuota'].where(df_cashflow['impago'] == 0, 0)
	df_cashflow['fecha_cuota'] = pd.to_datetime(df_cashflow['fecha_cuota'])
	df_t = df_cashflow[['fecha_cuota', 'id_credito', 'impago', 'monto_cuota', 'pagado']].set_index('fecha_cuota')
	df_t = df_t.resample('D').agg({'id_credito': 'count',
								   'impago': 'sum',
								   'monto_cuota': 'sum',
								   'pagado': 'sum'})

	df_t['loss'] = df_t['monto_cuota'] - df_t['pagado']

	df_t['tasa_imago'] = df_t['impago'].astype(int) / df_t['id_credito'].astype(int)
	df_t['esperado_cumulativo'] = df_t['monto_cuota'].cumsum()
	df_t['ganado_cumulativo'] = df_t['pagado'].cumsum()
	df_t['perdida_cumulativo'] = df_t['loss'].cumsum()

	df_t['goal'] = df_t['esperado_cumulativo'] * 0.75

	df_t['meta_cantidad'] = round(df_t['id_credito']*0.25).astype(int)

	today_date = datetime.today()
	df_t = df_t[df_t.index < today_date]

	return df_t, df_cashflow


# %%
def ingresos_acumulados(df_t):
	fig = go.Figure(layout=go.Layout(
		title="Ingresos acumulados",
		width=1000,
		height=600,
		template='simple_white'
	))

	fig.add_trace(go.Scatter(x=df_t.index,
							 y=df_t.esperado_cumulativo,
							 mode='lines',
							 line=dict(width=0.5, color='coral'),
							 fill='tozeroy',
							 name='Ingreso esperado acumulado'))

	fig.add_trace(go.Scatter(x=df_t.index,
							 y=df_t.ganado_cumulativo,
							 mode='lines',
							 line=dict(width=0.5, color='green'),
							 fill='tozeroy',
							 name='Ingreso real acumulado'))

	fig.add_trace(go.Scatter(x=df_t.index, y=df_t.goal, mode='lines', line=dict(width=1.5, color='black', dash='dash'),
							 name='Meta 75%'))

	return fig


def histograma_mora(df):
	fig = px.histogram(df, y='madurez', orientation='h', color='madurez', text_auto=True,
					   color_discrete_map={'Mora 0': 'coral', 'Mora 15': 'red', 'Mora 30': 'red', 'Mora 45': 'crimson'})

	fig.update_layout(title_text='Cantidad de clientes en mora',
					  height=500, width=700,
					  template='simple_white',
					  bargap=0.1,
					  showlegend=False)

	fig.update_xaxes(title='Clientes')
	fig.update_yaxes(title=None)

	return fig


def histograma_moneda(df):

	df['exigible_moneda'] = [round(x,2) for x in df['exigible_moneda']]

	fig = px.histogram(df, y='madurez', x='exigible_moneda', orientation='h', color='madurez', text_auto=True,
					   histfunc='sum',
					   color_discrete_map={'Mora 0': 'coral', 'Mora 15': 'red', 'Mora 30': 'red', 'Mora 45': 'crimson'})

	fig.update_layout(title_text='Saldo exigible por mora',
					  height=500, width=700,
					  template='simple_white',
					  bargap=0.1,
					  showlegend=False,
					  xaxis_tickprefix="$")

	fig.update_xaxes(title='Suma de saldo exigible')
	fig.update_yaxes(title=None)

	return fig



def impagos_diarios(df_t):
	df_t['Meta'] = ['<25%' if goal < 0.25 else '>25%' for goal in df_t['tasa_imago']]
	fig = px.bar(df_t, x=df_t.index, y='impago', barmode='overlay', color='Meta',
				 color_discrete_map={'>25%': 'crimson', '<25%': 'lightblue'})
	fig.update_layout(barnorm='percent', template='simple_white')
	fig.update_yaxes(title='Tasa de Impago (%)')
	fig.update_xaxes(title=None)

	return fig


##############################################
def transform(file):
	# Leer archivo
	df = pd.read_csv(file)

	# Filtrar para hoy
	df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota']).dt.date
	df = df[df['fecha_cuota'] < datetime.date.today()]
	df.sort_values(by='fecha_cuota', ascending=False, inplace=True)

	# Mantener último saldo por crédito
	df.drop_duplicates(subset=['id_credito'], keep='first', inplace=True)

	# Agregar columnas
	df['valor_financiamiento'] = df['valor_financiamiento'].where(df['pais'] == 'El Salvador',
																  df['valor_financiamiento'] / 25)
	df['prima'] = df['prima'].where(df['pais'] == 'El Salvador', df['prima'] / 25)

	# Crear total
	total = df.groupby(['pais', 'estado'])[['id_credito', 'saldo_exigible', 'numero_periodos']].agg(
		{'id_credito': 'count',
		 'saldo_exigible': 'sum',
		 'numero_periodos': 'mean'}).rename(columns={'id_credito':'cuenta','saldo_exigible':'suma de exigible','numero_periodos':'periodos promedio'})


	total.reset_index(inplace=True)

	# Seleccionar y mapear columnas
	cols = ['id_credito', 'saldo_total', 'monto_cuota', 'saldo_exigible', 'numero_periodos', 'valor_financiamiento',
			'prima']

	mapper = {'id_credito': 'count',
			  'saldo_total': ['sum', 'mean'],
			  'monto_cuota': ['sum', 'mean'],
			  'saldo_exigible': ['sum', 'mean'],
			  'numero_periodos': 'mean',
			  'valor_financiamiento': ['sum', 'mean'],
			  'prima': ['sum', 'mean']
			  }

	agg_df = total.groupby(['estado', 'num_cuota', 'pais'])[cols].agg(mapper)
	print(agg_df)

	agg_df.columns = ['Cantidad', 'Saldo Total', 'Saldo Promedio', 'Suma monto cuota', 'Cuota Promedio',
					  'Exigible Total', 'Exigible Promedio', 'Periodos Promedio', 'Financiamiento Total',
					  'Financiamiento Promedio', 'Recuperado Total (prima)', 'Recuperado Promedio (prima)']

	agg_df['madurez'] = agg_df.index.get_level_values('num_cuota')
	agg_df['Deuda Total'] = agg_df['madurez'] * agg_df['Suma monto cuota']

	mora = agg_df.xs('Vencido', level='estado')
	mora_re = mora.reset_index()

	mora_total = mora.groupby(level='num_cuota').agg(['sum', 'mean'])

	return df, total, agg_df, mora_re, mora_total


def impago_time(file):
	df = pd.read_csv(file)

	# Filtrar para hoy
	df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota']).dt.date
	df = df[df['fecha_cuota'] < datetime.date.today()]
	df.sort_values(by='fecha_cuota', ascending=False, inplace=True)

	# Mantener último saldo por crédito
	df.drop_duplicates(subset=['id_credito'], keep='first', inplace=True)
	df['impago'] = [1 if estado == 'Vencido' else 0 for estado in df['estado']]
	df['ganado'] = df['monto_cuota'].where(df['impago'] == 0, 0)
	df['exigible'] = df['saldo_exigible'].fillna(0)
	df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota'])
	df_t = df[['fecha_cuota', 'id_credito', 'impago', 'monto_cuota', 'ganado', 'exigible']].set_index('fecha_cuota')
	df_t = df_t.resample('D').agg({'id_credito': 'count',
								   'impago': 'sum',
								   'monto_cuota': 'sum',
								   'ganado': 'sum',
								   'exigible': 'sum'})
	df_t['loss'] = df_t['monto_cuota'] - df_t['ganado']

	df_t['tasa_imago'] = df_t['impago'].astype(int) / df_t['id_credito'].astype(int)
	df_t['esperado_cumulativo'] = df_t['monto_cuota'].cumsum()
	df_t['ganado_cumulativo'] = df_t['ganado'].cumsum()
	df_t['perdida_cumulativo'] = df_t['loss'].cumsum()
	df_t['goal'] = df_t['esperado_cumulativo'] * 0.75
	df_t['meta_cantidad'] = round(df_t['id_credito']*0.25).astype(int)

	df_t['date'] = pd.to_datetime(df_t.index)
	today_date = datetime.today()
	df_t = df_t[df_t.index < today_date]

	fig = go.Figure(layout=go.Layout(
		title="Ingresos acumulados",
		width=1000,
		height=600,
		template='simple_white'
	))

	fig.add_trace(go.Scatter(x=df_t.index,
							 y=df_t.esperado_cumulativo,
							 mode='lines',
							 line=dict(width=0.5, color='coral'),
							 fill='tozeroy',
							 name='Ingreso esperado acumulado'))

	fig.add_trace(go.Scatter(x=df_t.index,
							 y=df_t.ganado_cumulativo,
							 mode='lines',
							 line=dict(width=0.5, color='green'),
							 fill='tozeroy',
							 name='Ingreso real acumulado'))

	fig.add_trace(go.Scatter(x=df_t.index, y=df_t.goal, mode='lines', line=dict(width=1.5, color='black', dash='dash'),
							 name='Meta 75%'))

	return df_t, fig

# VISUALIZACION CLIENTES EN MORA POR MADUREZ

def mora_madurez(mora_re):

	data = pd.DataFrame(mora_re.groupby('num_cuota')['Cantidad'].sum())
	data.reset_index(inplace=True)
	data.rename(columns={0:'Cantidad'})

	fig = px.bar(data, x='num_cuota', y='Cantidad', text='Cantidad')
	fig.update_layout(height=600, width=1000, template='simple_white')

	return fig

def mora_madurez_usd(mora_re):

	data = pd.DataFrame(mora_re.groupby('num_cuota')['Exigible Total'].sum())
	data.reset_index(inplace=True)
	data.rename(columns={0:'Cantidad'})

	data['num_cuota'] = data['num_cuota'].map({1:'Mora 15',
											   2:'Mora 30',
											   3:'Mora 45'})

	fig = px.bar(data, x='Exigible Total', y='num_cuota', text='Exigible Total', orientation='h', color_discrete_sequence=['red','pink'])
	fig.update_layout(height=600, width=1000, template='simple_white')

	return fig


def comparacion(mora_re):
	fig = px.bar(mora_re, x='num_cuota', y='Cantidad', color='pais', barmode='group', text='Exigible Total', color_discrete_sequence=['coral','pink','orange'])
	fig.update_layout(height=600, width=600)
	return fig


# CREAR DATA

def process2(df, df_cashflow):
	mapper = df[['id_credito','cuotas_pendientes']]
	df_cashflow = df_cashflow.merge(mapper,how='left',on='id_credito')
	union = df.merge(df_cashflow, how='outer', on='id_credito')
	union['deuda_total'] = union['cuota']*union['numero_periodos']
	data = union[['pais_x', 'id_credito', 'dias_mora','saldo_total_x', 'cuotas_pendientes_x', 'num_cuota', 'saldo_exigible','estado','valor_financiamiento','impago','pagado','deuda_total']]
	data.columns = ['País', 'ID Crédito', 'Días Mora', 'Saldo Total', 'Cuotas Pendientes', 'No Cuota', 'Saldo Exigible','Estado', 'Valor Financiamiento', 'Impago', 'Pagado', 'Monto Crédito']
	data.fillna(0, inplace=True)
	#data.drop(columns=['CP'], inplace=True)
	data['Días Mora'] = data['Días Mora'].astype(int)
	data['Cuotas Pendientes'] = data['Cuotas Pendientes'].astype(int)
	data['No Cuota'] = data['No Cuota'].astype(int)
	data['Impago'] = data['Impago'].astype(int)
	data['Estado Mora'] = data['Cuotas Pendientes'].map({0:'Sin Mora',
                                                     1:'Mora 15',
                                                     2:'Mora 30',
                                                     3:'Mora 45'})
	return data

# NUEVAS FIGURAS

def saldo_mora_fig(data):
    
    fig = px.histogram(data, y='Estado Mora', x='Saldo Total', orientation='h', color='Estado Mora', text_auto=True,category_orders={'Estado Mora':['Sin Mora','Mora 15','Mora 30','Mora 45']},color_discrete_map={'Sin Mora':'lightgreen', 'Mora 15':'violet','Mora 30':'purple', 'Mora 45':'crimson'})

    fig.update_traces(texttemplate='$%{x:,.2f}')

    fig.update_layout(title_text='Saldo por categoría de mora',
                    #text_template='Saldo Total',
                    #height=500, width=700,
                    template='simple_white',
                    bargap=0.1,
                    showlegend=False)

    fig.update_xaxes(title='Suma de Saldo Total')
    fig.update_yaxes(title=None)

    return fig

def pagos_acumulados(df_t):
    fig = go.Figure(data=[
		
		go.Bar(name='Pagos', 
			x=df_t.index, 
			y=df_t.id_credito.cumsum(),
			marker=dict(color='green'),
			opacity=0.6,
			text=df_t.monto_cuota.cumsum(),
			texttemplate='$%{text:,.2f}',
			textposition='inside'),
		
		go.Bar(name='Impagos', 
			x=df_t.index, 
			y=df_t.impago.cumsum(),
			marker=dict(
				color='indigo',
				#colorscale='Reds',
				#colorbar=dict(title="Value")
			),
			#opacity=0.6,
			text=df_t.loss.cumsum(),
			texttemplate='$%{text:,.2f}',
			textposition='inside'),
		
		go.Bar(name='Impagos esperados', 
			x=df_t.index, 
			y=df_t.meta_cantidad.cumsum(),
			marker=dict(
				color='black',
				opacity=0.3,
				#colorscale='Reds',
				#colorbar=dict(title="Value")
			),
			#opacity=0.6,
			text=df_t.loss.cumsum(),
			#customdata=np.transpose([labels, widths*data[key]]),
			#texttemplate="%{y} x %{width} =<br>%{customdata[1]}",
			texttemplate='$%{text:,.2f}',
			textposition='inside'
		),
		
		#go.Scatter(name='Límite 25% impago',
		#		   x=df_t.index,
		#		   y=df_t.meta_cantidad,
		#		   mode='lines+markers',
		#		   marker=dict(color='yellow'),)
	])
    fig.update_layout(title='Pagos acumulados', template='simple_white', barmode='overlay',height=600, width=1200)
    return fig
