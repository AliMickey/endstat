import requests
from flask import current_app

def send_email(recipient, subject, message):
	return requests.post(
		"https://api.mailgun.net/v3/endstat.com/messages",
		auth=("api", current_app.config['MAILGUN_API']),
		data={"from": "End Stat <info@endstat.com>",
			"to": recipient,
			"subject": subject,
			"text": message})