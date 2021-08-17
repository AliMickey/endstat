import os, requests
from dotenv import load_dotenv
load_dotenv('../env')

mailgunAPIkey = os.environ.get('mailgunAPIkey')

def send_email(recipient, subject, message):
	return requests.post(
		"https://api.mailgun.net/v3/endstat.com/messages",
		auth=("api", mailgunAPIkey),
		data={"from": "End Stat <info@endstat.com>",
			"to": [recipient],
			"subject": subject,
			"text": message})