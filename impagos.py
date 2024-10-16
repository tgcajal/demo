import streamlit as st
import pandas as pd 
import numpy as np
import datetime
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import plotly 
import plotly.express as px 
import plotly.graph_objects as go

from transform import prep, transform

data = prep('mora.csv','cashflow.csv')

df, mora_df, cashflow_df = transform('mora.csv','cashflow.csv')

def cosecha_mora(df):
    
    fig = px.histogram(df, template='simple_white', x='cosecha_semana', y='id_credito', histfunc='count', barnorm='percent',color='Mora', category_orders={'Mora':['Mora 4','Mora 3','Mora 2','Mora 1','Pagado','Al día'], 'cosecha_semana':['31','32','33','34','35','36','37','38','39']}, color_discrete_map={'Mora 4':'crimson','Mora 3':'purple','Mora 2':'purple','Mora 1':'violet','Pagado':'green','Al día':'lightgreen'}, text_auto=True)
    fig.update_traces(texttemplate='%{y:,.2f}%')
    fig.update_xaxes(title='Semana Venta')
    fig.update_yaxes(title='Porcentaje de cartera')

    return fig

st.plotly_chart(cosecha_mora(df))