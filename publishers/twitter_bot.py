import tweepy

def publicar_en_x(api_key, api_secret, access_token, access_secret, texto):
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )
    
    # X/Twitter limita los mensajes a 280 caracteres
    texto_corto = texto[:275] + "..." if len(texto) > 280 else texto
    response = client.create_tweet(text=texto_corto)
    return response