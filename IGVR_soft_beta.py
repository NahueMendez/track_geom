# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 09:53:03 2025

@author: CENADIF
"""

import folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

tolerancias_por_clase = {
    'I':   {'trocha_sup': 1037, 'trocha_inf': 990,  'peralte_sup': 110, 'peralte_inf': -110, 'alabeo_sup': 51},
    'II':  {'trocha_sup': 1035, 'trocha_inf': 991,  'peralte_sup': 110, 'peralte_inf': -110, 'alabeo_sup': 42},
    'III': {'trocha_sup': 1032, 'trocha_inf': 992,  'peralte_sup': 110, 'peralte_inf': -110, 'alabeo_sup': 36},
    'IV':  {'trocha_sup': 1029, 'trocha_inf': 992,  'peralte_sup': 110, 'peralte_inf': -110, 'alabeo_sup': 33},
    'V':   {'trocha_sup': 1026, 'trocha_inf': 993,  'peralte_sup': 110,  'peralte_inf': -110,  'alabeo_sup': 28},
}


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371000 # Radius of earth in meters. Use 3956 for miles. Determines return value units.
    return c * r
    

def limpiar_gps(df_sucio):
    """
    Reemplaza 'No fix' y 'No data' con NaN en las columnas 'latitud' y 'longitud'.

    Args:
        df (pd.DataFrame): DataFrame con columnas 'latitud' y 'longitud'.

    Returns:
        pd.DataFrame: DataFrame con NaN en lugar de 'No fix' y 'No data'.
    """
    df = df_sucio.copy()
    # Convertir a numérico con errores a NaN y luego inferir objetos
    df['Latitud'] = pd.to_numeric(df['Latitud'].replace(['No fix', 'No data'], np.nan).astype(float), errors='coerce')
    df['Longitud'] = pd.to_numeric(df['Longitud'].replace(['No fix', 'No data'], np.nan).astype(float), errors='coerce')
    df['Velocidad(km/h)'] = pd.to_numeric(df['Velocidad(km/h)'].replace('0.0', np.nan).astype(float), errors='coerce')
    df = df.infer_objects(copy=False)
    
    #.Interpolo linealmente
    # Verificar si hay suficientes datos para interpolar
    valid_lat_long = (~df['Latitud'].isna() & ~df['Longitud'].isna()).sum()
    
    if valid_lat_long >= 2:  # Necesitamos al menos 2 puntos válidos para interpolar
        df['Latitud'] = df['Latitud'].interpolate(method='linear')
        df['Longitud'] = df['Longitud'].interpolate(method='linear')
        df['Velocidad(km/h)'] = df['Velocidad(km/h)'].interpolate(method='linear')


    return df


def graficar_trayectoria(df, test_number,dia,zona,nombre_mapa="trayectoria.html"):
    """
    Grafica la trayectoria desde un DataFrame de pandas con latitud y longitud.

    Args:
        df (pd.DataFrame): DataFrame con columnas 'latitud' y 'longitud'.
        nombre_mapa (str): Nombre del archivo HTML para guardar el mapa.
    """
    mapa = folium.Map(location=[df_clean['Latitud'].iloc[0], df_clean['Longitud'].iloc[0]], zoom_start=15,width=900, height=300)
    # Agregar líneas entre los puntos
    puntos = list(zip(df['Latitud'], df['Longitud']))
    texto_mapa=f"""<b> TIA S.A </b> <br />
                <em> Medición de geometría de vía </em> <br />
                Zona de prueba: {zona} <br />
                Fecha:{dia} <br />
                Número de prueba: {str(test_number)}
                
                """
    
    #.Iterar sobre los puntos para crear segmentos coloreados
    for i in range(len(df) - 1):
        lat1, lon1 = df['Latitud'].iloc[i], df['Longitud'].iloc[i]
        lat2, lon2 = df['Latitud'].iloc[i + 1], df['Longitud'].iloc[i + 1]

        # Verificar si alguno de los parámetros está fuera de tolerancia en este punto
        fuera_de_tolerancia = df['fuera_trocha'].iloc[i] or df['fuera_peralte'].iloc[i] or (df['fuera_alabeo'].iloc[i] if 'fuera_alabeo' in df.columns and i < len(df['fuera_alabeo']) else False)

        color = 'red' if fuera_de_tolerancia else 'green'

        # Agregar el segmento al mapa
        folium.PolyLine(locations=[(lat1, lon1), (lat2, lon2)], color=color, weight=2, tooltip=texto_mapa).add_to(mapa)
    return mapa

if __name__ == "__main__":
    #.Datos operativos
    metadatos=pd.read_csv('metadatos.txt',sep=':',header=None)
    zona=metadatos[metadatos[0]=='Lugar de prueba'][1].values[0].strip()
    ramal=metadatos[metadatos[0]=='Ramal/Linea de prueba'][1].values[0].strip()
    dia=metadatos[metadatos[0]=='Dia de prueba'][1].values[0].strip()
    cliente=metadatos[metadatos[0]=='Cliente'][1].values[0].strip()
    lat_ref=float(metadatos[metadatos[0]=='Latitud de referencia'][1].values[0].strip())
    lon_ref=float(metadatos[metadatos[0]=='Longitud de referencia'][1].values[0].strip())
    pk_inicial=float(metadatos[metadatos[0]=='PK inicio'][1].values[0].strip())
    clase_via = metadatos[metadatos[0] == 'Clase de via'][1].values[0].strip()
    print(f"Clase de vía: {clase_via}")
    #.Sentido de la medición
    sentido = float(metadatos[metadatos[0]=='Sentido'][1].values[0])
    print(f"Sentido de la medición: {'Ascendente' if sentido == 1 else 'Descendente'}")
    # Ejemplo de DataFrame (reemplaza esto con tus datos)
    data_raw = pd.read_csv('track.txt',header=0)
    #.Inicios
    begin=data_raw[data_raw[data_raw.columns[0]]=='Trocha(mm)'].index.tolist()
    # Agregar el final del DataFrame como el último punto de corte
    begin.append(len(data_raw))

    # Inicializar el contador de grabaciones
    test_number = 1
    #.Creo estructura de carpetas para resultados
    dirname = os.getcwd()
    report_path = os.path.join(dirname, 'reports')
    maps_path = os.path.join(dirname, 'maps')
    plots_path = os.path.join(dirname, 'plots')
    sheets_path = os.path.join(dirname, 'sheets')
    if not os.path.exists(report_path):
        os.makedirs(report_path)
    if not os.path.exists(maps_path):
        os.makedirs(maps_path)
    if not os.path.exists(plots_path):
        os.makedirs(plots_path)
    if not os.path.exists(sheets_path):
        os.makedirs(sheets_path)    
    # Iterar sobre los inicios de las grabaciones
    flagoffset=True
    distancia_acumulada=0
    for i in range(len(begin) - 1):
        # Recortar el DataFrame para la grabación actual
        start = begin[i] + 1  # Comenzar después del encabezado
        end = begin[i + 1]
        data_segment = data_raw.iloc[start:end].copy()
        data_segment.columns = ['Trocha(mm)', 'Peralte(mm)', 'Distancia(m)', 'Latitud', 'Longitud','Velocidad(km/h)','HoraGPS']
        #.Elimino whitespaces
        data_segment['Latitud'] = data_segment['Latitud'].str.strip()
        data_segment['Longitud'] = data_segment['Longitud'].str.strip()
        #.Limpio GPS e interpolo
        df_clean=limpiar_gps(data_segment.copy())
        df_clean.dropna(subset=['Latitud', 'Longitud'], how='all', inplace=True)
        #.Convierto a numeros
        df_clean['Latitud']=pd.to_numeric(df_clean['Latitud'],errors='coerce') 
        df_clean['Longitud']=pd.to_numeric(df_clean['Longitud'],errors='coerce') 
        df_clean['Distancia(m)'] = pd.to_numeric(df_clean['Distancia(m)'], errors='coerce')
        df_clean['Trocha(mm)'] = pd.to_numeric(df_clean['Trocha(mm)'], errors='coerce')
        df_clean['Peralte(mm)'] = pd.to_numeric(df_clean['Peralte(mm)'], errors='coerce')
        # Verificar si hay datos de GPS válidos
        if df_clean['Latitud'].isna().all() or df_clean['Longitud'].isna().all() or len(df_clean) == 0:
            print(f"Advertencia: No hay datos GPS válidos para la prueba {test_number}. Pasando a la siguiente.")
            test_number += 1
            continue
        #.Ajustamos el sentido de la medición
        if sentido == -1:  # Si el sentido es negativo, invertir las columnas
            df_clean['Distancia(m)'] = df_clean['Distancia(m)']*(-1)
            sentido_med='Descendente'
        else:
            sentido_med='Ascendente'
        #.Ajusto la distancia acumulada
        if df_clean['Distancia(m)'].isna().all():
            print(f"Advertencia: No hay datos de distancia válidos para la prueba {test_number}. Pasando a la siguiente.")
            test_number += 1
            continue
        #.Corregimos y acumulamos distancia
        df_clean['Distancia(m)']=df_clean['Distancia(m)']+distancia_acumulada+(pk_inicial * 1000)
        distancia_acumulada += df_clean['Distancia(m)'].iloc[-1] - (pk_inicial * 1000)
        #.Offset aceleracion
        if flagoffset:   #.Solo calculo offset de la primer prueba
            offset_lat=lat_ref-df_clean['Latitud'].iloc[0]
            offset_lon=lon_ref-df_clean['Longitud'].iloc[0]
            flagoffset=False
        df_clean['Latitud']=df_clean['Latitud']+offset_lat
        df_clean['Longitud']=df_clean['Longitud']+offset_lon
        
        #.Localizo eventos:
        # Definir las tolerancias
        t = tolerancias_por_clase.get(clase_via)

        if t is None:
            print(f"Advertencia: Clase de vía {clase_via} no reconocida. Se usarán tolerancias por defecto (clase I).")
            t = tolerancias_por_clase['I']
            
        tolerancia_trocha_superior = t['trocha_sup']
        tolerancia_trocha_inferior = t['trocha_inf']
        tolerancia_peralte_superior = t['peralte_sup']
        tolerancia_peralte_inferior = t['peralte_inf']
        tolerancia_alabeo_superior = t['alabeo_sup']

         #.Calculo el alabeo
        progresivas_alabeo=np.arange(df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),3)
        df_clean_agrupado = df_clean.groupby('Distancia(m)')['Peralte(mm)'].max()
        peralte_interpolado = df_clean_agrupado.reindex(progresivas_alabeo, method='bfill')
        alabeo=np.diff(pd.to_numeric(peralte_interpolado),prepend=[0])/3.0
        fuera_alabeo_array = np.abs(alabeo) > tolerancia_alabeo_superior

        # Crear las columnas booleanas para trocha y peralte
        df_clean['fuera_trocha'] = (df_clean['Trocha(mm)'] > tolerancia_trocha_superior) | (df_clean['Trocha(mm)'] < tolerancia_trocha_inferior)
        df_clean['fuera_peralte'] = (df_clean['Peralte(mm)'] > tolerancia_peralte_superior) | (df_clean['Peralte(mm)'] < tolerancia_peralte_inferior)

        # Crear la columna booleana para alabeo, alineando por la distancia
        # Necesitamos crear una Serie de Pandas con el índice adecuado
        if len(progresivas_alabeo) == len(fuera_alabeo_array):
            df_alabeo = pd.DataFrame({'Distancia(m)': progresivas_alabeo[:-1], 'fuera_alabeo': fuera_alabeo_array[1:]}) # Excluimos el primer valor (prepend 0) y la última distancia
            df_clean = pd.merge_asof(df_clean.sort_values('Distancia(m)'), df_alabeo.sort_values('Distancia(m)'), on='Distancia(m)', direction='nearest')
            df_clean['fuera_alabeo'] = df_clean['fuera_alabeo'].fillna(False) # Llenar posibles NaN con False
        else:
            df_clean['fuera_alabeo'] = False # Si no hay suficientes datos para el alabeo, marcar todo como False


        # Graficar la trayectoria     
        mapa=graficar_trayectoria(df_clean,test_number,dia,zona)
        mapa_name=f"mapa_{test_number}.html"
        mapa.save(os.path.join(maps_path,mapa_name))
        
        #.Graficar las series
        fig,ax=plt.subplots(nrows=3,ncols=1,sharex=True,dpi=100,figsize=(12,8))
        ax[0].hlines(1000,df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),color='k',linestyle='--',label='Nominal')
        ax[0].hlines(tolerancia_trocha_superior,df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),color='r',linestyle='--',label='Limites')
        ax[0].hlines(tolerancia_trocha_inferior,df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),color='r',linestyle='--')
        ax[0].plot(df_clean['Distancia(m)'],pd.to_numeric(df_clean['Trocha(mm)']),label='Medición')
        ax[0].set_ylabel('Trocha [mm]',fontfamily='Times New Roman',fontsize=12)
        ax[0].set_ylim(980,1047)
        ax[0].set_xlim(df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max())
        ax[0].grid(True)
        ax[0].legend(fontsize=9)
        
        ax[1].hlines(tolerancia_peralte_superior,df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),color='r',linestyle='--',label='Límites')
        ax[1].hlines(tolerancia_peralte_inferior,df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),color='r',linestyle='--')
        ax[1].plot(df_clean['Distancia(m)'],pd.to_numeric(df_clean['Peralte(mm)']),c='tab:green',label='Medición')
        ax[1].set_ylabel('Peralte [mm]',fontfamily='Times New Roman',fontsize=12)
        ax[1].grid(True)
        ax[1].set_ylim(-120,120)
        ax[1].legend(fontsize=9)

        ax[2].hlines(tolerancia_alabeo_superior,df_clean['Distancia(m)'].min(),df_clean['Distancia(m)'].max(),color='r',linestyle='--',label='Límite')
        ax[2].plot(progresivas_alabeo,np.abs(alabeo),c='tab:orange',label='Medición')
        ax[2].set_ylabel('Variación de desnivel transv. [mm/m]',fontfamily='Times New Roman',fontsize=12)
        ax[2].set_xlabel('Progresiva [m]',fontfamily='Times New Roman',fontsize=16)
        ax[2].grid(True)
        ax[2].set_ylim(0,70)
        ax[2].legend(fontsize=9)

        nombre_imagen =f'plot_{test_number}.png'
        plt.tight_layout()
        plt.savefig(os.path.join(plots_path,nombre_imagen),dpi=200)
        plt.clf()
        # Crear los gráficos de pie
        fig_pie, axes_pie = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))
        plt.style.use('seaborn-v0_8-pastel') # Un estilo visual agradable
        
        # Gráfico de pie para Trocha
        fuera_trocha_porcentaje = np.mean(df_clean['fuera_trocha']) * 100
        dentro_trocha_porcentaje = 100 - fuera_trocha_porcentaje
        labels_trocha = [f'Dentro de tol. ({dentro_trocha_porcentaje:.1f}%)', f'Fuera de tol. ({fuera_trocha_porcentaje:.1f}%)']
        sizes_trocha = [1 - np.mean(df_clean['fuera_trocha']), np.mean(df_clean['fuera_trocha'])]
        colors_trocha = ['lightgreen', 'lightcoral']
        axes_pie[0].pie(sizes_trocha, labels=labels_trocha, autopct='%1.1f%%', startangle=90, colors=colors_trocha)
        axes_pie[0].set_title(f'Trocha - Prueba {test_number}')
        axes_pie[0].axis('equal')  # Equal aspect ratio asegura que el pie sea un círculo.
        
        # Gráfico de pie para Peralte
        fuera_peralte_porcentaje = np.mean(df_clean['fuera_peralte']) * 100
        dentro_peralte_porcentaje = 100 - fuera_peralte_porcentaje
        labels_peralte = [f'Dentro de tol. ({dentro_peralte_porcentaje:.1f}%)', f'Fuera de tol. ({fuera_peralte_porcentaje:.1f}%)']
        sizes_peralte = [1 - np.mean(df_clean['fuera_peralte']), np.mean(df_clean['fuera_peralte'])]
        colors_peralte = ['lightgreen', 'lightcoral']
        axes_pie[1].pie(sizes_peralte, labels=labels_peralte, autopct='%1.1f%%', startangle=90, colors=colors_peralte)
        axes_pie[1].set_title(f'Peralte - Prueba {test_number}')
        axes_pie[1].axis('equal')
        
        # Gráfico de pie para Alabeo
        # Asegurarse de que la columna 'fuera_alabeo' exista
        if 'fuera_alabeo' in df_clean.columns:
            fuera_alabeo_porcentaje = np.mean(df_clean['fuera_alabeo'].fillna(False)) * 100 # Manejar posibles NaN
            dentro_alabeo_porcentaje = 100 - fuera_alabeo_porcentaje
            labels_alabeo = [f'Dentro de tol. ({dentro_alabeo_porcentaje:.1f}%)', f'Fuera dfe tol. ({fuera_alabeo_porcentaje:.1f}%)']
            sizes_alabeo = [1 - np.mean(df_clean['fuera_alabeo'].fillna(False)), np.mean(df_clean['fuera_alabeo'].fillna(False))]
            colors_alabeo = ['lightgreen', 'lightcoral']
            axes_pie[2].pie(sizes_alabeo, labels=labels_alabeo, autopct='%1.1f%%', startangle=90, colors=colors_alabeo)
            axes_pie[2].set_title(f'Variación de desnivel transv.- Prueba {test_number}')
            axes_pie[2].axis('equal')
        else:
            axes_pie[2].axis('off') # Si no hay datos de alabeo, ocultar el subplot
            axes_pie[2].set_title(f'Variación del desnivel transv. - Prueba {test_number} (Sin datos)')
            
        plt.tight_layout()
        nombre_pie = f'pie_tolerancias_{test_number}.png'
        plt.savefig(os.path.join(plots_path, nombre_pie), dpi=200)
        plt.clf() # Limpiar la figura para la siguiente prueba

        #.Guardo excel-
        name_excel=f"medicion_{test_number}.xlsx"
        df_clean.to_excel(os.path.join(sheets_path,name_excel),sheet_name='Datos',index=False)
        #.-----------------------------------Armo un pequeño reporte----------------------------
               
        with open(os.path.join(plots_path,nombre_imagen), "rb") as image_file:
            medicion_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        with open(os.path.join(plots_path,nombre_pie), "rb") as image_file:
            stats_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        with open("tia_logo.jpeg", "rb") as image_file:
            logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <center>
        <head>
            <title>Reporte de medición con IGVR</title>

            <style>
            .imagen-esquina {{
                position: absolute;
                top: 10px; /* Ajusta la distancia desde la parte superior */
                right: 10px; /* Ajusta la distancia desde la derecha */
                width: 200px; /* Ajusta el ancho de la imagen */
                height: auto; /* Mantiene la proporción de la imagen */
            }}
            .mapa-iframe {{
            border: none; /* Elimina el borde del iframe */
            padding: 0; /* Elimina el relleno del iframe */
            margin: 0; /* Elimina el margen del iframe */
            }}
        
            </style>
        </head>
    
        <body>
        <body style="background-color: lightgrey;">
        
            <h1>Reporte de medición</h1>
             <img src="data:image/png;base64,{logo_base64}" alt="TIA S.A" class="imagen-esquina">
            
            <p> <b>Cliente: </b>{cliente} </br> <b>Fecha del relevamiento: </b>{dia} </br> <b>Lugar del relevamiento: </b>{zona} </br>
            <b>Ramal/Línea: </b>{ramal} </br> <b>Número de prueba: </b>{test_number} </br>
            <b>PK inicio: </b>{pk_inicial}  -  <b>Sentido: </b>{sentido_med} </br>  </p>
            
            <h3>Magnitudes geométricas registradas</h3>
            <img src="data:image/png;base64,{medicion_base64}" width="900" alt="Data of sensors">
            
            <h3>Estadística con respecto a las tolerancias</h3>
            <img src="data:image/png;base64,{stats_base64}" width="900" alt="Data of sensors">
            
            <h3>Mapa del trayecto relevado</h3>
            <iframe src="../maps/{mapa_name}" width="900" height="300" class="mapa-iframe"></iframe>
        
            <p> Todos los derechos reservados &#174;</p>
        </body>
        </center>
        </html>
        """
        
        html_name=f"report_{test_number}.html"
        html_path=os.path.join(report_path,html_name)
        with open(html_path, "w", encoding="latin1") as f:
            f.write(html_content)
            
        test_number+=1
