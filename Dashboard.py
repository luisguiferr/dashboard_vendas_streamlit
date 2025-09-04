import streamlit as st
import requests 
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS 🛒')

url = 'https://labdados.com/produtos' 

# Filtros
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todos o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

# Requests com filtro
query_string = {'regiao':regiao.lower(), 'ano':ano}
response = requests.get(url, params=query_string) 

dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

# Filtro vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

### Tabelas
## Tabelas de receita
# Tabela de receita por estado
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra',
                                                                   'lat', 
                                                                   'lon']].merge(receita_estados, 
                                                                                 left_on='Local da compra', 
                                                                                 right_index=True).sort_values('Preço', ascending=False)

# Tabela de receita mensal por ano
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
meses = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 
         7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month.map(meses)

# Tabela de receita por categoria de produtos
receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False).reset_index()

## Tabelas de quantidade de vendas
# Tabela de vendas por estado
vendas_estados = dados.groupby('Local da compra')[['Preço']].count()
vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra',
                                                                  'lat',
                                                                  'lon']].merge(vendas_estados,
                                                                                left_on='Local da compra',
                                                                                right_index=True).sort_values('Preço', ascending=False)

# Tabela de vendas mensal por ano
vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].sum().reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month.map(meses)

# Tabela de vendas por categoria de produtos
vendas_categorias = dados.groupby('Categoria do Produto')[['Preço']].count().sort_values('Preço', ascending=False).reset_index()

## Tabelas vendedores
receita_vendedores = dados.groupby('Vendedor')[['Preço']].sum().sort_values('Preço', ascending=False)
vendas_vendedores = dados.groupby('Vendedor')[['Preço']].count().sort_values('Preço', ascending=False)

## Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados, 
                                  lat='lat', 
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat':False, 'lon':False},
                                  title='Receita por estado',
                                  labels={'Preço':'Receita (R$)'})

fig_receita_mensal = px.line(receita_mensal,
                             x='Mes',
                             y='Preço',
                             markers=True,
                             range_y=(0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita mensal',
                             labels={'Preço':'Receita (R$)', 'Mes':'Mês'})
fig_receita_mensal.update_layout(yaxis_title='Receita', 
                                 xaxis_title='')

cores = ['#174A7E', '#4A81BF', '#6495ED', '#94AFC5', '#CDDBF3']
fig_receita_estados = px.bar(receita_estados.head(5),
                             x='Local da compra',
                             y='Preço',
                             text_auto=True,
                             title='Top estados (receita)',
                             color='Local da compra',
                             color_discrete_sequence=cores,
                             labels={'Local da compra':'Estado', 'Preço':'Receita (R$)'})
fig_receita_estados.update_layout(yaxis_title='',
                                  xaxis_title='',
                                  showlegend=False)

fig_receita_categoria = px.bar(receita_categorias,
                               x='Categoria do Produto',
                               y='Preço',
                               text_auto=True,
                               title='Receita por categoria',
                               range_y=(0, 2.5e6),
                               color_discrete_sequence=['#4A81BF'],
                               custom_data=['Categoria do Produto', 'Preço'])
fig_receita_categoria.update_layout(yaxis_title='', 
                                    xaxis_title='',                                    
                                    showlegend=False,
                                    yaxis=dict(showgrid=True))
fig_receita_categoria.update_traces(hovertemplate='Categoria do produto = %{customdata[0]}<br>Receita (R$) = %{customdata[1]}<extra></extra>')

fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                                 lat='lat', 
                                 lon='lon',
                                 scope='south america',
                                 size='Preço',
                                 template='seaborn',
                                 hover_name='Local da compra',
                                 hover_data={'lat':False, 'lon':False},
                                 title='Vendas por estado',
                                 labels={'Preço':'Quantidade de vendas'})

fig_vendas_mensal = px.line(vendas_mensal,
                            x='Mes',
                            y='Preço',
                            markers=True,
                            range_y=(0, vendas_mensal.max()),
                            color='Ano',
                            line_dash='Ano',
                            title='Vendas mensal',
                            labels={'Preço':'Quantidade de vendas', 'Mes':'Mês'})
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas', 
                                xaxis_title='')

fig_vendas_categoria = px.bar(vendas_categorias,
                              x='Categoria do Produto',
                              y='Preço',
                              text_auto=True,
                              title='Vendas por categoria',
                              range_y=(0, 2000),
                              color_discrete_sequence=['#4A81BF'],
                              custom_data=['Categoria do Produto', 'Preço'])
fig_vendas_categoria.update_layout(yaxis_title='',
                                   xaxis_title='',
                                   showlegend=False,
                                   yaxis=dict(showgrid=True))
fig_vendas_categoria.update_traces(hovertemplate='Categoria do produto = %{customdata[0]}<br>Quantidade de vendas = %{customdata[1]}<extra></extra>')

fig_vendas_estados = px.bar(vendas_estados.head(5),
                            x='Local da compra',
                            y='Preço',
                            text_auto=True,
                            title='Top estados (vendas)',
                            color='Local da compra',
                            color_discrete_sequence=cores,
                            labels={'Local da compra':'Estado', 'Preço':'Quantidade de vendas'})
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas',
                                 xaxis_title='',
                                 showlegend=False)

## Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])
with aba1:
    coluna1, coluna2 = st.columns(2) 
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categoria, use_container_width=True)

with aba2:
    coluna1, coluna2 = st.columns(2) 
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))      
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categoria, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    
    coluna1, coluna2 = st.columns(2) 
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        receita_vendedores = receita_vendedores.head(qtd_vendedores)
        fig_receita_vendedores = px.bar(receita_vendedores,
                                        x='Preço',
                                        y=receita_vendedores.index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)',
                                        labels={'Preço':'Receita (R$)'},
                                        color_discrete_sequence=['#4A81BF'])
        fig_receita_vendedores.update_layout(yaxis_title='')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)        

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))    
        vendas_vendedores = vendas_vendedores.head(qtd_vendedores)
        fig_vendas_vendedores = px.bar(vendas_vendedores,
                                       x='Preço',
                                       y=vendas_vendedores.index,
                                       text_auto=True,
                                       title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)',
                                       labels={'Preço':'Quantidade de vendas'},
                                       color_discrete_sequence=['#4A81BF']) 
        fig_vendas_vendedores.update_layout(yaxis_title='')       
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)   