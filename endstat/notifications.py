import os, requests
from dotenv import load_dotenv
load_dotenv(os.getenv('ENVFILE'))

MAILGUN_API = os.environ.get('MAILGUN_API')

def send_email(recipient, subject, message):
	return requests.post(
		"https://api.mailgun.net/v3/endstat.com/messages",
		auth=("api", MAILGUN_API),
		data={"from": "End Stat <info@endstat.com>",
			"to": recipient,
			"subject": subject,
			"text": message})