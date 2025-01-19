from twikit import Client
from configparser import ConfigParser

# credenciales de login
config = ConfigParser()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

# autentificacion
client = Client('es')

# funcion asincrona para obtener tweets
async def twitters(term):
    lista_tweets=[]
   
# se inicia sesion
    await client.login(auth_info_1=username, auth_info_2=email, password=password)

    if term != None:    
        tweets = await client.search_tweet(term, 'top')  
        #se obtienen los tweets 
        for tweet in tweets:                       
            lista_tweets.append({
                "tweets":tweet.text,
                "user":tweet.user.name})
           
        # se repite el proceso para obtener mas tweets   
        more_tweets = await tweets.next()

        for tweet in more_tweets:                       
            lista_tweets.append({
                "tweets":tweet.text,
                "user":tweet.user.name})
               
      
        return(lista_tweets)                
    