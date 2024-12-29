import tweepy
import time


bearer_token = "AAAAAAAAAAAAAAAAAAAAAN8JxgEAAAAAhwSsyQwufwx9i%2F9jXJyAmFRP%2FY4%3De4wdKX7dqZ4uQdBCCkdzZorudOK7GHODqzupvMFGD3J676Rk2y"


# Crear un cliente de Twitter

client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

def buscar_tweets( term):
    query = term+" -is:retweet lang:es"

    count = 0
    tweets = []
    response = client.search_recent_tweets(query, max_results=10)
    for tweet in response.data:
        tweets.append(tweet.text)
        count += 1
        time.sleep(1)

    print(f"Se encontraron {count} tweets")
    return tweets

# Realizar solicitudes sin preocuparte por los límites

# tweets = buscar_tweets("Python")

# for tweet in tweets:
#     print(tweet)
#     print("----")
