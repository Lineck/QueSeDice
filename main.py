from flask import Flask, render_template, redirect, url_for, request, Response
from sentiment import roberta, preprocess
from youtube import buscar_videos, obtener_comentarios
from twitter import twitters
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import datetime
from twitter_API import buscar_tweets
import io
import asyncio
import pandas as pd 
from pymongo import MongoClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
import matplotlib

matplotlib.use('Agg')  # Configurar backend sin GUI

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'

# Crear un bucle de eventos global
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Conectar a MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Conexión local
db = client["ProyectoF"]  # Nombre de la base de datos
# collection = db["pruebaX"]  # Nombre de la colección
collection = db["TablaResultado"]  # Nombre de la colección

# Formulario
class TermForm(FlaskForm):
    term = StringField("Término a buscar", validators=[DataRequired(), Length(min=3, max=20)])
    submit = SubmitField("Buscar")
    youtube = BooleanField("YouTube")
    twitter = BooleanField("Twitter")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        if not any([self.youtube.data, self.twitter.data]):
            self.youtube.errors.append("Debes seleccionar al menos una opción (YouTube o Twitter).")
            return False
        
        return True




    
    
def paginate_dataframe(df, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return df.iloc[start:end]

def style_sentimientos(row):
    if row["SENTIMIENTO"] == "positive":
        row["SENTIMIENTO"] = "Positivo"
        return f'<strong class="text-success">{row["SENTIMIENTO"]}</strong>'
    elif row["SENTIMIENTO"] == "negative":
        row["SENTIMIENTO"] = "Negativo"
        return f'<strong class="text-danger">{row["SENTIMIENTO"]}</strong>'
    elif row["SENTIMIENTO"] == "neutral":
        row["SENTIMIENTO"] = "Neutral"
        return f'<strong class="text-warning">{row["SENTIMIENTO"]}</strong>'
    
    return row["SENTIMIENTO"]

def style_plataformas(row):
    if row["PLATAFORMA"] == "YouTube":
        return f'<strong class="text-danger">{row["PLATAFORMA"]}</strong>'
    elif row["PLATAFORMA"] == "Twitter":
        return f'<strong class="text-primary">{row["PLATAFORMA"]}</strong>'
    return row["PLATAFORMA"]


@app.route('/results')

@app.route('/results/<term>/<youtube>/<twitter>')
def results(term=None, youtube=None, twitter=None):
    lista_datos = []

    # Parámetros de paginación
    page = int(request.args.get("page", 1))  # Página actual (por defecto 1)
    per_page = 25  # Número de filas por página
    
    # Convertir parámetros a booleanos
    youtube = youtube.lower() == "true" if youtube else False
    twitter = twitter.lower() == "true" if twitter else False

    
    if youtube:
        videos = buscar_videos(term)
        
        for video in videos:
            video_id = video['videoId']
            comentarios = obtener_comentarios(video_id)
            
            for comentario in comentarios:
                texto = comentario['comentario'] 
                           
                textos = preprocess(texto)
                
                sentimiento = roberta(textos)
                lista_datos.append({                
                "PLATAFORMA": "YouTube",
                "TEXTO": texto,
                "TERMINO": term,
                "SENTIMIENTO": sentimiento
                })
                
    if twitter:        
        tweets = loop.run_until_complete(twitters(term))
        # tweets = buscar_tweets(term)
        for tweet in tweets:            
            texto = preprocess(tweet)
            sentimiento = roberta(texto)
            lista_datos.append({                
                "PLATAFORMA": "Twitter",
                "TEXTO": texto,
                "TERMINO": term,
                "SENTIMIENTO": sentimiento
            })

    # Guardar resultados en MongoDB
    if lista_datos:
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        busqueda_id = f"{term}_{fecha_actual}"  # Identificador único para esta búsqueda
        
        for dato in lista_datos:
            dato["FECHA"] = fecha_actual
            dato["BUSQUEDA_ID"] = busqueda_id  # Asociar los datos a esta búsqueda
        collection.insert_many(lista_datos)
            
   
    return redirect(url_for('view_results', busqueda_id=busqueda_id))

@app.route('/previous_results', methods=['GET'])
def previous_results():
    # Obtener identificadores únicos de búsqueda
    historial = collection.distinct("BUSQUEDA_ID")
    historial_info = [{"busqueda_id": id, "term": id.split('_')[0], "fecha": id.split('_')[1]} for id in historial]

    return render_template("previous_results.html", historial=historial_info)

@app.route('/view_results/<busqueda_id>', methods=['GET'])
def view_results(busqueda_id):

    # Parámetros de paginación
    page = int(request.args.get("page", 1))  # Página actual (por defecto 1)
    per_page = 20  # Número de filas por página
      
    # Consultar los resultados de MongoDB para el término seleccionado
    resultados = collection.find({"BUSQUEDA_ID": busqueda_id})
    lista_datos = list(resultados)
    
    
    if lista_datos:
        # Eliminar el campo '_id'
        for dato in lista_datos:
            dato.pop('_id', None)
        df = pd.DataFrame(lista_datos,columns=["PLATAFORMA", "TEXTO", "SENTIMIENTO"])
        df["SENTIMIENTO"] = df.apply(style_sentimientos, axis=1) 
        df["PLATAFORMA"] = df.apply(style_plataformas, axis=1)

        
        # Dividir el DataFrame
        paginated_df = paginate_dataframe(df, page, per_page)
        total_pages = (len(df) + per_page - 1) // per_page  # Número total de páginas
        # Convertir el DataFrame a HTML para mostrarlo en la tabla
        tabla_html = paginated_df.to_html(classes='table table-bordered table-light ', index=False, justify='center', escape=False)
    
        return render_template('view_results.html', tabla=tabla_html, page=page, total_pages=total_pages, busqueda_id=busqueda_id,term=lista_datos[0]['TERMINO'],fecha=lista_datos[0]['FECHA'])

    return f"No se encontraron resultados para el término:{busqueda_id} "

@app.route('/stats/<busqueda_id>', methods=['GET'])
def stats(busqueda_id):
    # Consultar resultados en MongoDB para el término
    resultados = collection.find({"BUSQUEDA_ID": busqueda_id})
    lista_datos = list(resultados)

    if not lista_datos:
        return f"No se encontraron resultados para el término: {lista_datos[0]['TERMINO']}"

    # Crear DataFrame
    df = pd.DataFrame(lista_datos)
    
    # Separar por plataforma
    stats_por_plataforma = {}
    for plataforma in df['PLATAFORMA'].unique():
        df_plataforma = df[df['PLATAFORMA'] == plataforma]

        total = len(df_plataforma)
        positivos = len(df_plataforma[df_plataforma['SENTIMIENTO'] == 'positive'])
        negativos = len(df_plataforma[df_plataforma['SENTIMIENTO'] == 'negative'])
        neutrales = len(df_plataforma[df_plataforma['SENTIMIENTO'] == 'neutral'])

        stats_por_plataforma[plataforma] = {
            "Total de comentarios": total,
            "Positivos": positivos,
            "Negativos": negativos,
            "Neutrales": neutrales,
            "Porcentaje Positivo": round((positivos / total) * 100, 2) if total > 0 else 0,
            "Porcentaje Negativo": round((negativos / total) * 100, 2) if total > 0 else 0,
            "Porcentaje Neutral": round((neutrales / total) * 100, 2) if total > 0 else 0,
        }

    # Renderizar las estadísticas en una plantilla HTML
    return render_template("stats.html", busqueda_id=busqueda_id, stats_por_plataforma=stats_por_plataforma, term=lista_datos[0]['TERMINO'], fecha=lista_datos[0]['FECHA'])

@app.route('/download_pdf/<busqueda_id>', methods=['GET'])
def download_pdf(busqueda_id):
    # Consultar resultados en MongoDB para el término
    resultados = collection.find({"BUSQUEDA_ID": busqueda_id})
    lista_datos = list(resultados)

    if not lista_datos:
        return "No se encontraron resultados para este término.", 404
    
    # Obtener la fecha de la búsqueda (usando el primer resultado como referencia)
    fecha_busqueda = lista_datos[0].get("FECHA", "Fecha no disponible")

    # Crear DataFrame
    df = pd.DataFrame(lista_datos)

    # Calcular estadísticas por plataforma
    stats_por_plataforma = {}
    for plataforma in df['PLATAFORMA'].unique():
        df_plataforma = df[df['PLATAFORMA'] == plataforma]
        total = len(df_plataforma)
        positivos = len(df_plataforma[df_plataforma['SENTIMIENTO'] == 'positive'])
        negativos = len(df_plataforma[df_plataforma['SENTIMIENTO'] == 'negative'])
        neutrales = len(df_plataforma[df_plataforma['SENTIMIENTO'] == 'neutral'])

        stats_por_plataforma[plataforma] = {
            "Total de comentarios": total,
            "Positivos": positivos,
            "Negativos": negativos,
            "Neutrales": neutrales,
        }

    # Generar el PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    y = 750
    pdf.drawString(200, y, f"Estadísticas para el término: {lista_datos[0]['TERMINO']}")
    y -= 20
    pdf.drawString(200, y, f"Fecha de búsqueda: {fecha_busqueda}")
    y -= 60

    for plataforma, stats in stats_por_plataforma.items():
        pdf.drawString(50, y, f"Plataforma: {plataforma}")
        y -= 20
        for key, value in stats.items():
            pdf.drawString(70, y, f"{key}: {value}")
            y -= 15

        # Generar gráfico con Matplotlib
        labels = ["Positivos", "Negativos", "Neutrales"]
        values = [stats["Positivos"], stats["Negativos"], stats["Neutrales"]]
        plt.figure(figsize=(4, 4))
        plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=["green", "red", "gray"])
        plt.title(f"Distribución de Sentimientos - {plataforma}")

        # Guardar gráfico como imagen en memoria
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png")
        img_buffer.seek(0)  # Reiniciar el puntero al inicio del búfer
        plt.close()

        # Convertir el búfer en un objeto compatible con ReportLab
        image = ImageReader(img_buffer)

        # Insertar la imagen en el PDF
        pdf.drawImage(image, 300, y -90 , width=200, height=200)
        y -= 200  # Ajustar la posición para el siguiente contenido


        if y < 100:  # Salto de página si queda poco espacio
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 750

    pdf.save()
    buffer.seek(0)

    # Devolver el archivo PDF
    return Response(
        buffer,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename={lista_datos[0]['TERMINO']}_{fecha_busqueda}_stats.pdf"}
    )



@app.route('/download_csv/<busqueda_id>', methods=['GET'])
def download_csv(busqueda_id):
    # Consultar datos de MongoDB
    resultados = collection.find({"BUSQUEDA_ID": busqueda_id})
    lista_datos = list(resultados)

    if lista_datos:
        # Eliminar el campo '_id'
        for dato in lista_datos:
            dato.pop('_id', None)
        df = pd.DataFrame(lista_datos)

        # Convertir a CSV
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)

        return Response(
            buffer,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={lista_datos[0]['TERMINO']}_resultados.csv"}
        )
    return "No se encontraron resultados en MongoDB para este término."

   

@app.route('/', methods=['GET', 'POST'])
def index():
    form = TermForm()
    if form.validate_on_submit():
        term = form.term.data
        print("Formulario válido")
       

        print(f"youtube: {form.youtube.data}, twitter: {form.twitter.data}")
        return redirect(url_for('results', term=term, youtube=form.youtube.data, twitter=form.twitter.data))
    else:
        print("Formulario inválido", form.errors)
    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)