# EndStat
## Description
An Open-Source Platform to Facilitate Endpoint Status Monitoring.
Developed for final year university project.

[Live Version](https://endstat.app.mickit.net)

## Motivation
Pre-existing solutions were either not open-source, behind a paywall of some sort or was not simple enough to use.

## Technologies Used
[Flask](https://flask.palletsprojects.com),
[Bootstrap](https://getbootstrap.com),
[Docker](https://www.docker.com),
[URLScan.io](https://urlscan.io/docs/api/)

## Build from source
1. Clone the repository
2. Move into the directory `cd endstat`
3. Initialise a virtual environment `python -m venv venv`
4. Activate the virtual environment, Linux: `source venv/bin/activate`
5. Install requirements `pip install -r requirements.txt`
6. Edit the config file with your keys `endstat/instance/config.py`
7. Set Flask environment `export FLASK_APP=endstat`
8. Initialise a new database `flask init-db`
9. Run the app `flask run`

## Notes
In order for website scanning to work, you need an api key from [URLScan.io](https://urlscan.io/docs/api)
Furthermore, for emails to work, you will need to get a [Zoho](https://www.zoho.com) app password and change all domain references to your own.

## Features
### Certificates
Websites will have their certificates checked for validity.

### Ports
Websites will be checked for open ports on their web servers, "safe" ports such as (80, 443) will only be shown to the user. More dangerous ports such as (22) will be highlighted and the user will be alerted.

### Safety Analysis
Websites will be run against Google's [Safe Browsing API](https://developers.google.com/safe-browsing) to check for any threats.

### Monitoring
Websites will be scanned on initial addition, then every 24 hours thereafter.

### Alerting
Users will be sent notifications via enabled agents (Email & Discord for now) for dangerous website status changes. This can include a dangerous port being opened or a certificate nearing expiry.
