# option 1 
# have scheduler run every 12 hours
# check db for all websites for specific options
# run checks on all websites at same time
# if website is deleted, db entry removed
#https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask
#EASY - Server gets over loaded 


# option 2
# store start time for each website in db
# each time app is run, initiliase a scheduler for each website
# scheduler will add 12 hours to start time for each website
# if website is deleted, db entry removed and scheduler task removed from job list
#HARDER - Load is distributed