# montrek
A program that tracks financial transactions of a number of bank accounts and depots, analyzes the data and gives valuable output? 

## Installation Notes

Checkout repository:
```
git clone git@github.com:chrishombach/montrek.git
```

You have to eventually sort out ssh keys.

### Locally (For development)

**Setup environment**

Enter in your bash terminal

```
python -m venv venv_montrek
. venv_montrek/bin/activate
python -m pip install -r requirements.txt
cd montrek
python manage.py runserver
```
**DB Setup**

Follow instructions for MariaDb here: [Django-Maria-DB Setup](https://www.digitalocean.com/community/tutorials/how-to-use-mysql-or-mariadb-with-your-django-application-on-ubuntu-14-04)

### In Docker container ###

Install docker-compose.

Run
```
docker-compose up --build
```

Open in webbrowser:
```
http://localhost:1339/account/list
```
