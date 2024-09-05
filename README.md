# sms
=======
git clone local

Create Heroku

heroku create -a durain

initialize git

git add .

git commit -m "My first commit"

heroku git:remote -a durain

push

heroku git push heroku main

Adding Variable Values

heroku config:set APIKEY=You durain API AUTHORIZED_USERS=You TG id BOT_TOKEN=You TG bot Token

start

heroku ps:scale worker=1
