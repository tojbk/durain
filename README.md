# sms
git clone 到本地

创建Heroku应用

heroku create -a durain

初始化 git

git add .

git commit -m "My first commit"

heroku git:remote -a durain

推送

heroku  git push heroku main

添加变量值

heroku config:set APIKEY=You durain API AUTHORIZED_USERS=You TG id BOT_TOKEN=You TG bot Token
