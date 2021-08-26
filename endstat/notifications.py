from flask import current_app
from discord_webhook import DiscordWebhook, DiscordEmbed
from endstat.db import get_db
import requests

# Specific email agent
def sendEmail(email, message):
	return requests.post(
			"https://api.mailgun.net/v3/endstat.com/messages",
			auth=("api", current_app.config['MAILGUN_API']),
			data={"from": "End Stat <info@endstat.com>",
				"to": email,
				"subject": "End Stat Alert",
				"text": message})

# General wrapper to send notifications to enabled agents for the user
def sendNotification(userID, message):
	db = get_db()
	notifications = db.execute('SELECT email, discord, email_enabled, discord_enabled FROM notification_settings WHERE user_id = ?', 
		(userID,)).fetchone()
	
	if (notifications['email_enabled']):
		sendEmail(notifications['email'], message)
		
	if (notifications['discord_enabled']):
		discordWebhook = DiscordWebhook(url=notifications['discord'])
		embed = DiscordEmbed(title="End Stat Alert", description=message, color=242424)
		discordWebhook.add_embed(embed).execute()
		response = discordWebhook.execute()