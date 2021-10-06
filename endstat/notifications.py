from flask import current_app
import smtplib, sqlite3
from discord_webhook import DiscordWebhook
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# Specific email agent
def sendEmail(recipient, message, api):
	msg = MIMEText(message, 'plain', 'utf-8')
	msg['Subject'] =  Header("End Stat Alert", 'utf-8')
	msg['From'] = formataddr((str(Header("End Stat", 'utf-8')), "endstat@mickit.net"))
	msg['To'] = recipient

	try:
		server = smtplib.SMTP_SSL('smtp.zoho.com.au', 465)
		server.login('endstat@mickit.net', api)
		server.sendmail("endstat@mickit.net", [recipient], msg.as_string())
		server.quit()
	except smtplib.SMTPServerDisconnected:
		print("SMTP error.")
		pass
	except:
		print("Socket timeout error.")
		pass

# General wrapper to send notifications to enabled agents for the user
def sendNotification(userID, message, api=None):
	db = sqlite3.connect('instance/endstat.sqlite')
	# Check if api is passed to thread, otherwise use app config
	if api is None:
		api = current_app.config['ZOHO_API']
	notifications = db.execute('SELECT email, discord, email_enabled, discord_enabled FROM notification_settings WHERE user_id = ?', 
		(userID,)).fetchone()
	db.close()
	# Checks to see which notification agents are enabled
	if (notifications[2]): #Email
		sendEmail(notifications[0], message, api)
		
	if (notifications[3] and notifications[1]): #Discord
		discordWebhook = DiscordWebhook(url=notifications[1], content=message)
		response = discordWebhook.execute()