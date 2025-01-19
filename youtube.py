from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Tu clave API de YouTube
API_KEY = "AIzaSyCiFWYUHFjIUdJPoSanJwLYS18RfBAyecg"

# Configura el cliente de la API
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Paso 1: Buscar videos relacionados con una consulta
def buscar_videos(query, max_results=10):
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    ).execute()
    
    videos = []
    for item in response['items']:
        videos.append({
            "videoId": item['id']['videoId'],
            "title": item['snippet']['title']
        })
    return videos

# Paso 2: Obtener comentarios de un video
def obtener_comentarios(video_id):
    comentarios = []
    try:
        # Realiza la solicitud para obtener comentarios
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=10
        ).execute()

        # Procesa los comentarios
        for item in response.get("items"):
            comentario = item['snippet']['topLevelComment']['snippet']['textDisplay']
            autor = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
            comentarios.append({"autor": autor, "comentario": comentario})

    except HttpError as e:
        error_content = e.content.decode()
        if "commentsDisabled" in error_content:
            print(f"El video con ID {video_id} tiene los comentarios deshabilitados. Omitiendo...")
        else:
            raise  # Si es otro error, propágalo

    return comentarios

