import os
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twitter():
    """Test Twitter API functionality using v2"""
    try:
        # Get Twitter credentials
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        if not all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
            print("Error: Missing Twitter credentials in .env file")
            return
            
        # Initialize Twitter client v2
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Test tweet using v2
        test_message = "This is a test tweet from the Twitter bot test script using API v2."
        response = client.create_tweet(text=test_message)
        print(f"Test tweet sent successfully! Tweet ID: {response.data['id']}")
        
    except Exception as e:
        print(f"Error testing Twitter API: {str(e)}")

if __name__ == '__main__':
    test_twitter() 