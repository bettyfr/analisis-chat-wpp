import pandas as pd
import re
import regex
import demoji
import numpy as np
from collections import Counter
import plotly.express as px
import matplotlib.pyplot as plt
from PIL import Image
from wordcloud import WordCloud, STOPWORDS
import streamlit as st

# Configuración de la página de Streamlit
st.set_page_config(page_title='Análisis de WhatsApp', layout='wide')

# Función para iniciar con fecha y hora
def IniciaConFechaYHora(s):
    patron = r'^(\d{1,2})/(\d{1,2})/(\d{2,4}), (\d{1,2}):(\d{2}) -'
    resultado = re.match(patron, s)
    return bool(resultado)

# Función para encontrar miembros del grupo
def EncontrarMiembro(s):
    patrones = ['Betty Flores Rosales:', 'Gato:']
    patron = '^' + '|'.join(patrones)
    resultado = re.match(patron, s)
    return bool(resultado)

# Función para obtener partes de cada línea del txt
def ObtenerPartes(linea):
    splitLinea = linea.split(' - ')
    FechaHora = splitLinea[0]
    splitFechaHora = FechaHora.split(', ')
    Fecha = splitFechaHora[0]
    Hora = splitFechaHora[1]
    MensajeCompleto = ' - '.join(splitLinea[1:])
    for patron in ['Betty Flores Rosales:', 'Gato:']:
        if patron in MensajeCompleto:
            Miembro, Mensaje = MensajeCompleto.split(patron, 1)
            Miembro = patron[:-1]
            Mensaje = Mensaje.strip()
            return Fecha, Hora, Miembro, Mensaje
    return Fecha, Hora, None, MensajeCompleto.strip()

# Leer el archivo txt descargado del chat de WhatsApp
RutaChat = 'Data/chat.txt'
DatosLista = []
with open(RutaChat, encoding="utf-8") as fp:
    fp.readline()
    while True:
        linea = fp.readline()
        if not linea:
            break
        linea = linea.strip()
        if IniciaConFechaYHora(linea):
            Fecha, Hora, Miembro, Mensaje = ObtenerPartes(linea)
            DatosLista.append([Fecha, Hora, Miembro, Mensaje])
        elif DatosLista:
            DatosLista[-1][-1] += ' ' + linea

df = pd.DataFrame(DatosLista, columns=['Fecha', 'Hora', 'Miembro', 'Mensaje'])
df['Fecha'] = pd.to_datetime(df['Fecha'], format="%d/%m/%Y")
df = df.dropna()
df.reset_index(drop=True, inplace=True)

def ObtenerEmojis(Mensaje):
    emoji_lista = []
    data = regex.findall(r'\X', Mensaje)
    for caracter in data:
        if demoji.replace(caracter) != caracter:
            emoji_lista.append(caracter)
    return emoji_lista

total_mensajes = df.shape[0]
multimedia_mensajes = df[df['Mensaje'] == '<Multimedia omitido>'].shape[0]
df['Emojis'] = df['Mensaje'].apply(ObtenerEmojis)
emojis = sum(df['Emojis'].str.len())
url_patron = r'(https?://\S+)'
df['URLs'] = df.Mensaje.apply(lambda x: len(re.findall(url_patron, x)))
links = sum(df['URLs'])
encuestas = df[df['Mensaje'] == 'POLL:'].shape[0]

estadistica_dict = {'Tipo': ['Mensajes', 'Multimedia', 'Emojis', 'Links', 'Encuestas'],
                    'Cantidad': [total_mensajes, multimedia_mensajes, emojis, links, encuestas]}
estadistica_df = pd.DataFrame(estadistica_dict, columns=['Tipo', 'Cantidad']).set_index('Tipo')

emojis_lista = list([a for b in df.Emojis for a in b])
emoji_diccionario = dict(Counter(emojis_lista))
emoji_diccionario = sorted(emoji_diccionario.items(), key=lambda x: x[1], reverse=True)
emoji_df = pd.DataFrame(emoji_diccionario, columns=['Emoji', 'Cantidad']).set_index('Emoji').head(10)

fig_emojis = px.pie(emoji_df, values='Cantidad', names=emoji_df.index, hole=.3, template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Pastel2)
fig_emojis.update_traces(textposition='inside', textinfo='percent+label', textfont_size=20)
fig_emojis.update_layout(showlegend=False)

df_MiembrosActivos = df.groupby('Miembro')['Mensaje'].count().sort_values(ascending=False).to_frame()
df_MiembrosActivos.reset_index(inplace=True)
df_MiembrosActivos.index = np.arange(1, len(df_MiembrosActivos)+1)
df_MiembrosActivos['% Mensaje'] = (df_MiembrosActivos['Mensaje'] / df_MiembrosActivos['Mensaje'].sum()) * 100

multimedia_df = df[df['Mensaje'] == '<Multimedia omitido>']
mensajes_df = df.drop(multimedia_df.index)
mensajes_df['Letras'] = mensajes_df['Mensaje'].apply(lambda s: len(s))
mensajes_df['Palabras'] = mensajes_df['Mensaje'].apply(lambda s: len(s.split(' ')))
miembros = mensajes_df.Miembro.unique()
dictionario = {}

for i in range(len(miembros)):
    lista = []
    miembro_df = mensajes_df[mensajes_df['Miembro'] == miembros[i]]
    lista.append(miembro_df.shape[0])
    palabras_por_msj = (np.sum(miembro_df['Palabras']))/miembro_df.shape[0]
    lista.append(palabras_por_msj)
    multimedia = multimedia_df[multimedia_df['Miembro'] == miembros[i]].shape[0]
    lista.append(multimedia)
    emojis = sum(miembro_df['Emojis'].str.len())
    lista.append(emojis)
    links = sum(miembro_df['URLs'])
    lista.append(links)
    dictionario[miembros[i]] = lista

miembro_stats_df = pd.DataFrame.from_dict(dictionario)
estadísticas = ['Mensajes', 'Palabras por mensaje', 'Multimedia', 'Emojis', 'Links']
miembro_stats_df['Estadísticas'] = estadísticas
miembro_stats_df.set_index('Estadísticas', inplace=True)
miembro_stats_df = miembro_stats_df.T
miembro_stats_df['Mensajes'] = miembro_stats_df['Mensajes'].apply(int)
miembro_stats_df['Multimedia'] = miembro_stats_df['Multimedia'].apply(int)
miembro_stats_df['Emojis'] = miembro_stats_df['Emojis'].apply(int)
miembro_stats_df['Links'] = miembro_stats_df['Links'].apply(int)
miembro_stats_df = miembro_stats_df.sort_values(by=['Mensajes'], ascending=False)

df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M', errors='coerce')
df = df.dropna(subset=['Fecha', 'Hora'])
df['rangoHora'] = df['Hora'].apply(lambda x: f'{x.hour:02d} - {(x + pd.Timedelta(hours=1)).hour:02d} h')
df['DiaSemana'] = df['Fecha'].dt.strftime('%A')
mapeo_dias_espanol = {'Monday': '1 Lunes','Tuesday': '2 Martes','Wednesday': '3 Miércoles','Thursday': '4 Jueves',
                      'Friday': '5 Viernes','Saturday': '6 Sábado','Sunday': '7 Domingo'}
df['DiaSemana'] = df['DiaSemana'].map(mapeo_dias_espanol)
df = df.dropna(subset=['Miembro', 'Mensaje'])
df.reset_index(drop=True, inplace=True)
df['# Mensajes por hora'] = 1
date_df_hora = df.groupby('rangoHora').count().reset_index()

fig_hora = px.line(date_df_hora, x='rangoHora', y='# Mensajes por hora', color_discrete_sequence=['salmon'], template='plotly_dark')
fig_hora.update_traces(mode='markers+lines', marker=dict(size=10))
fig_hora.update_xaxes(title_text='Rango de hora', tickangle=30)
fig_hora.update_yaxes(title_text='# Mensajes')

df['# Mensajes por día'] = 1
date_df_dia = df.groupby('DiaSemana').count().reset_index()

fig_dia = px.line(date_df_dia, x='DiaSemana', y='# Mensajes por día', color_discrete_sequence=['salmon'], template='plotly_dark')
fig_dia.update_traces(mode='markers+lines', marker=dict(size=10))
fig_dia.update_xaxes(title_text='Día', tickangle=30)
fig_dia.update_yaxes(title_text='# Mensajes')

#date_df_fecha = df.groupby('Fecha').sum().reset_index()
date_df_fecha = df.groupby('Fecha').sum(numeric_only=True).reset_index()


fig_fecha = px.line(date_df_fecha, x='Fecha', y='# Mensajes por día', color_discrete_sequence=['salmon'], template='plotly_dark')
fig_fecha.update_xaxes(title_text='Fecha', tickangle=45, nticks=35)
fig_fecha.update_yaxes(title_text='# Mensajes')

total_palabras = ' '
stopwords = STOPWORDS.update(['que', 'qué', 'con', 'de', 'te', 'en', 'la', 'lo', 'le', 'el', 'las', 'los', 'les', 'por', 'es',
                              'son', 'se', 'para', 'un', 'una', 'chicos', 'su', 'si', 'chic','nos', 'ya', 'hay', 'esta',
                              'pero', 'del', 'mas', 'más', 'eso', 'este', 'como', 'así', 'todo', 'https','Multimedia','omitido',
                              'y', 'mi', 'o', 'q', 'yo', 'al', 'fue', 'era', 'pues', 'ese', 'sea', 've', 'ni', 'sé'])

mask = np.array(Image.open('Resources/heart.jpg'))
for mensaje in mensajes_df['Mensaje'].values:
    palabras = str(mensaje).lower().split()
    for palabra in palabras:
        total_palabras += palabra + ' '

wordcloud = WordCloud(width=800, height=800, background_color='black', stopwords=stopwords, max_words=100, min_font_size=5, mask=mask, colormap='OrRd').generate(total_palabras)

# Selección de página
st.sidebar.title("Navegación")
opciones = ["Análisis del Chat", "Mensaje Especial"]
eleccion = st.sidebar.radio("Ir a", opciones)

if eleccion == "Análisis del Chat":
    st.title('Análisis de nuestro chat de WhatsApp')
    st.header('📊 Estadísticas generales')
    st.write("Aquí tienes un resumen de nuestros mensajes 🥰")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write(estadistica_df)
    with col2:
        st.write(df_MiembrosActivos)
    st.subheader('👀 Cómo se distribuyen nuestros mensajes ')
    st.write("Tienes más mensajes solo porque yo mando más notas de voz 😝")
    st.write(miembro_stats_df)
    st.header('🤗 Emojis más usados')
    st.write("Sabía que ese iba a ser el emoji más usado, y no hay ningún corazón 🥺")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write(emoji_df)
    with col2:
        st.plotly_chart(fig_emojis)
    st.header('⏰ Mensajes por hora')
    st.plotly_chart(fig_hora)
    st.header('📆 Mensajes por día')
    st.plotly_chart(fig_dia)
    st.header('📈 Mensajes a lo largo del tiempo')
    st.plotly_chart(fig_fecha)
    st.header('☁️ Nuestro word cloud')
    st.write("No sé porque no me sorprende que los jajajaja sean los más recurrentes")
    st.image(wordcloud.to_array(), caption='Las palabras que más usamos', use_column_width=True)
elif eleccion == "Mensaje Especial":
    st.title('Escrito especialmente para ti ❤️')
    
    multi = '''Desde que formas parte de mi vida, soy más feliz, has cambiado tanto mis días que ya no recuerdo como era la vida sin ti. No tienes idea cuanto agradezco haberte conocido.
    
Por más que hago memoria, aún no sé cuándo empezó todo, solo sé que tengo tantos recuerdos de nosotros siendo felices, que no importa tanto encontrar exactamente el momento donde comenzó, aunque si me intriga, pero es más que suficiente pensar en todo el camino que hemos compartido hasta hoy, yo deseo con todas mis fuerzas que podamos vivir muchos recuerdos más juntos. 

Deseo seguir trayendo felicidad a tu vida, así como tu a la mía. Espero que cada día que pase, me sigas eligiendo como yo a ti. No quiero ponerle un límite, solo quiero que disfrutes mi compañía tanto como yo disfruto de la tuya y estar para ti sin importar si es bueno o mal momento, eso es lo de menos, solo quiero ser tu apoyo y quererte cada día más.
    
Me encanta estar contigo, sin importar el lugar y que estemos haciendo, me encanta así nada más. Podría hablar contigo de mil cosas al mismo tiempo sin cansarme, me gusta tanto conocerte cada vez más, siento que con el paso del tiempo te he llegado a conocer tanto, no soy nivel experto pero ya puedo verte o escucharte y saber más o menos como estás, pero bueno sigo aprendiendo de ti mi amor, y obvio me encantan tus besos y abrazos, bueno en general me encantas tu.
    
Mi amor, mi amor, mi amor eres de las personas mas importantes en mi vida, estoy muy enamorada de ti y aunque te lo digo a cada rato, tengo que escribirlo aquí también; te quiero demasiado. 
    
Tu lograste adueñarte de mis pensamientos y te ganaste por completo mi corazón, y aunque me digas toxica de vez en cuando, yo confío en ti.
    
Quería hacer algo para ti diferente, espero te haya gustado mi fabuloso análisis estadístico y mi mensaje no tan largo pero muy significativo para mí 😍
    '''
    st.markdown(multi)
    st.markdown("&mdash;\
            Betty")
    
    # Agrega más fotos y mensajes según lo necesites
