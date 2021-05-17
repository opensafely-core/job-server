from environs import Env
from slack_sdk import WebClient


env = Env()

slack_token = env.str("SLACK_BOT_TOKEN", default="")

client = WebClient(token=slack_token)
