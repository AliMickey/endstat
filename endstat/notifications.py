from flask import current_app
import smtplib
from discord_webhook import DiscordWebhook, DiscordEmbed
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# App imports
from endstat.db import get_db

# Specific email agent
def sendEmail(recipient, message):
	msg = MIMEText(message, 'plain', 'utf-8')
	msg['Subject'] =  Header("End Stat Alert", 'utf-8')
	msg['From'] = formataddr((str(Header("End Stat", 'utf-8')), "endstat@mickit.net"))
	msg['To'] = recipient

	server = smtplib.SMTP_SSL('smtp.zoho.com.au', 465)
	server.login('endstat@mickit.net', current_app.config['ZOHO_API'])
	server.sendmail("endstat@mickit.net", [recipient], msg.as_string())
	server.quit()


# General wrapper to send notifications to enabled agents for the user
def sendNotification(userID, message):
	db = get_db()
	notifications = db.execute('SELECT email, discord, email_enabled, discord_enabled FROM notification_settings WHERE user_id = ?', 
		(userID,)).fetchone()
	
	if (notifications['email_enabled']):
		sendEmail(notifications['email'], message)
		
	if (notifications['discord_enabled'] and notifications['discord']):
		discordWebhook = DiscordWebhook(url=notifications['discord'], content=message)
		response = discordWebhook.execute()