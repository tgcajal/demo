import streamlit as st 
import pandas as pd 
import numpy as np
from transform import index_chain_transform

data = index_chain_transform('mora.csv','cashflow.csv')

vendedores = data.groupby(level='vendedor').sum().reset_index()['vendedor']
ventas = [list(data.loc[value]['id_credito']) for value in vendedores]
tasa_impago = [list(data.loc[value]['tasa_impago']) for value in vendedores]


data_impagos = {'Vendedor':list(vendedores),
                'Ventas Semanales': ventas,
                'Tasa Impago': tasa_impago}

column_configuration = {
    "Vendedor": st.column_config.TextColumn(
        "Vendedor", help="Vendedor", max_chars=100, width="medium"
    ),
    "Tasa Impago": st.column_config.LineChartColumn(
        "Tasa Impago (Semanal)",
        help="Tasa de impago por cosecha semanal.",
        width="large",
        y_min=0,
        y_max=1,
    ),
    "Ventas Semanales": st.column_config.BarChartColumn(
        "Ventas (Semanales)",
        help="Ventas por semana.",
        width="medium",
        y_min=0,
        y_max=100,
    ),
}



select, compare = st.tabs(["Select members", "Compare selected"])

with select:
    event = st.dataframe(
        data_impagos,
        column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )
    people = event.selection.rows
    filtered_df = data_impagos.iloc[people]
    st.dataframe(
        filtered_df,
        column_config=column_configuration,
        use_container_width=True,
    )

with compare:
    ventas_df = {}
    for person in people:
        ventas_df[data_impagos.iloc[person]["Vendedor"]] = data_impagos.iloc[person]["Ventas Semanales"]
    ventas_df = pd.DataFrame(ventas_df)

    tasa_df = {}
    for person in people:
        tasa_df[data_impagos.iloc[person]["Vendedor"]] = data_impagos.iloc[person]["tasa_impago"]
    tasa_df = pd.DataFrame(tasa_df)

    if len(people) > 0:
        st.header("Daily activity comparison")
        st.bar_chart(ventas_df)
        st.header("Yearly activity comparison")
        st.line_chart(tasa_df)
    else:
        st.markdown("No members selected.")