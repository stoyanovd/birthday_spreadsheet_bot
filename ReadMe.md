Install
========

### Google service accounts

Here is docs: https://developers.google.com/identity/protocols/OAuth2ServiceAccount

1. Create new project in google cloud: https://console.developers.google.com
1. Create new service account in this project: https://console.developers.google.com/iam-admin/serviceaccounts
3. Create json key, copy account email

### Create and populate .env.yaml

- put every string in quotes
- put dicts and lists in quotes too

### Install postgres on target machine

- install postgres

- Create locale in ubuntu and in psql
``` 
locale-gen ru_RU.UTF-8
dpkg-reconfigure locales
pg_lsclusters
Из предыдущей команды берём версию и название кластера, первые два столбца
sudo pg_dropcluster --stop 12 main
sudo pg_createcluster --locale ru_RU.utf8 --start 12 main
sudo pg_ctlcluster 12 main start
И после создать всю структуру БД
```

- or use interactive `sudo dpkg-reconfigure locales`
  you need ru_RU.UTF-8


- create user, db for user
- create target db, set unicode encoding to db

```
CREATE DATABASE "bday_db"
WITH OWNER "postgres"
ENCODING 'UTF8'
LC_COLLATE = 'ru_RU.utf8'
LC_CTYPE = 'ru_RU.utf8';
```



