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


async def twitters(term):
    lista_tweets=[]

    await client.login(auth_info_1=username, auth_info_2=email, password=password)

    if term != None:    
        tweets = await client.search_tweet(term, 'top')  
                                    
        for tweet in tweets:                       
            lista_tweets.append(tweet.text)    
                
        more_tweets = await tweets.next()

        for tweet in more_tweets:                       
            lista_tweets.append(tweet.text)    
                
        more_tweets = await more_tweets.next()
        for tweet in more_tweets:                       
            lista_tweets.append(tweet.text)    
                
        more_tweets = await more_tweets.next()
        for tweet in more_tweets:                       
            lista_tweets.append(tweet.text)    
                
        more_tweets = await more_tweets.next()
        for tweet in more_tweets:                       
            lista_tweets.append(tweet.text)    
                
       

        return(lista_tweets)                
    