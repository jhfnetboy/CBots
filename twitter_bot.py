import tweepy
import logging
from datetime import datetime
import asyncio
from config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterBot:
    def __init__(self):
        logger.info("Initializing Twitter bot")
        # Initialize Twitter API client
        self.client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        self.setup_stream()

    def setup_stream(self):
        """Setup Twitter stream for mentions"""
        class MentionStream(tweepy.StreamingClient):
            def __init__(self, bearer_token, bot):
                super().__init__(bearer_token)
                self.bot = bot

            def on_tweet(self, tweet):
                """Handle new tweets"""
                try:
                    logger.info(f"Received tweet: {tweet.text}")
                    # Reply to the tweet
                    self.bot.reply_to_tweet(tweet.id, tweet.text)
                except Exception as e:
                    logger.error(f"Error handling tweet: {e}")

        self.stream = MentionStream(TWITTER_BEARER_TOKEN, self)

    def start_stream(self):
        """Start listening for mentions"""
        try:
            # Get user ID
            user = self.client.get_me()
            user_id = user.data.id
            
            # Add rules to track mentions
            rules = self.stream.get_rules()
            if rules.data:
                for rule in rules.data:
                    self.stream.delete_rules(rule.id)
            
            self.stream.add_rules(tweepy.StreamRule(f"@{user.data.username}"))
            self.stream.filter()
        except Exception as e:
            logger.error(f"Error starting stream: {e}")

    def send_tweet(self, message):
        """Send a tweet"""
        try:
            tweet = self.client.create_tweet(text=message)
            logger.info(f"Tweet sent successfully: {tweet.data['id']}")
            return tweet.data['id']
        except Exception as e:
            logger.error(f"Error sending tweet: {e}")
            raise

    def reply_to_tweet(self, tweet_id, original_text):
        """Reply to a tweet"""
        try:
            reply_text = f"Get, have a nice day! https://twitter.com/user/status/{tweet_id}"
            self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id
            )
            logger.info(f"Reply sent successfully to tweet {tweet_id}")
        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            raise

    def schedule_tweet(self, message, schedule_time):
        """Schedule a tweet"""
        try:
            # Convert schedule_time to datetime
            schedule_datetime = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')
            if schedule_datetime < datetime.now():
                raise ValueError("Schedule time must be in the future")

            # Schedule the tweet
            delay = (schedule_datetime - datetime.now()).total_seconds()
            asyncio.create_task(self._delayed_tweet(message, delay))
            logger.info(f"Tweet scheduled for {schedule_datetime}")
            return True
        except Exception as e:
            logger.error(f"Error scheduling tweet: {e}")
            raise

    async def _delayed_tweet(self, message, delay):
        """Send tweet after delay"""
        try:
            await asyncio.sleep(delay)
            self.send_tweet(message)
        except Exception as e:
            logger.error(f"Error in delayed tweet: {e}") 