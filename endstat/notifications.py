import requests
from flask import current_app
from discord_webhook import DiscordWebhook, DiscordEmbed

def send_email(recipient, subject, message):
	return requests.post(
		"https://api.mailgun.net/v3/endstat.com/messages",
		auth=("api", current_app.config['MAILGUN_API']),
		data={"from": "End Stat <info@endstat.com>",
			"to": recipient,
			"subject": subject,
			"text": message})

def send_discord(title, message):
	# Replace webhook with user provided hook to be stored in db
	discordWebhook = DiscordWebhook(url=current_app.config['DISCORD_WEBHOOK'])
	embed = DiscordEmbed(title=title, description=message, color=242424)
	discordWebhook.add_embed(embed).execute()
	response = discordWebhook.execute()