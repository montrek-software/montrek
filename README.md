# montrek
A program that tracks financial transactions of a number of bank accounts and depots, analyzes the data and gives valuable output? 

## Installation Notes

### Checkout Repository

Do
```
git clone git@github.com:chrishombach/montrek.git <your-folder>
```

You have to eventually sort out ssh keys.

### DB Setup

1) Install MariaDB 

(Largely taken from [Django-Maria-DB Setup](https://www.digitalocean.com/community/tutorials/how-to-use-mysql-or-mariadb-with-your-django-application-on-ubuntu-14-04))

If your system has already MariaDB installed, you can skip this step

Install the packages from the repositories by typing:

```
sudo apt-get update
sudo apt-get install python-pip python-dev mariadb-server libmariadbclient-dev libssl-dev
```


   You will be asked to select and confirm a password for the administrative MariaDB account.

   You can then run through a simple security script by running:

```
sudo mysql_secure_installation
```

   You’ll be asked for the administrative password you set for MariaDB during installation. Afterwards, you’ll be asked a series of questions. Besides the first question, asking you to choose another administrative password, select yes for each question.

   With the installation and initial database configuration out of the way, we can move on to create our database and database user.

2) Create a database and user

We can start by logging into an interactive session with our database software by typing the following:

```
mysql -u root -p
```

You will be prompted for the administrative password you selected during installation. Afterwards, you will be given a prompt.

First, we will create a database for our Montrek project. Each project should have its own isolated database for security reasons. We will call our database montrek_db in this guide, but it’s always better to select something more descriptive. We’ll set the default type for the database to UTF-8, which is what Django expects:

```sql
CREATE DATABASE montrek_db CHARACTER SET UTF8;
```

Remember to end all commands at an SQL prompt with a semicolon.

Next, we will create a database user which we will use to connect to and interact with the database. Set the password to something strong and secure:

```sql
CREATE USER montrekuser@localhost IDENTIFIED BY 'password';
```
Now, all we need to do is give our database user access rights to the database we created:

```sql
GRANT ALL PRIVILEGES ON montrek_db.* TO montrekuser@localhost;
GRANT ALL PRIVILEGES ON test_montrek_db.* TO 'montrekuser'@'localhost';
```
The second privileged command is needed for the test suite.
Then, we need to flush the privileges so that the current instance of the database knows about the recent changes we’ve made:

```sql
FLUSH PRIVILEGES;
```
Exit the SQL prompt to get back to your regular shell session:
```
exit
```

### Locally (For development)

Copy the following to `.env` file in the root directory of the project and adjust where needed:
```
#montrek Config
NAVBAR_APPS= montrek_example_a_list montrek_example_b_list
LINKS=https://example.com,Example
INSTALLED_APPS= credit_institution currency country company

#Django
SECRET_KEY="my_secret_key"
DEBUG=1
ALLOWED_HOSTS=localhost 127.0.0.1

# database access credentials
DB_NAME=montrek_db
DB_USER=montrekuser
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
DB_VOLUME=/var/lib/mysql
APP_PORT=8000

```
Enter in your bash terminal

```
python -m venv venv_montrek
. venv_montrek/bin/activate
python -m pip install -r requirements.txt
cd montrek
python manage.py makemigrations
```

Run the migrations and start the server:
```
python manage.py migrate
python manage.py runserver
```
Now you should be able to open montrek in your webbrowser:
```
http://127.0.0.1:8000/
```

If you want to make sure that everything runs, you can run the test suite:

```
python manage.py test
```

### In Docker container ###

If you want to run montrek without developing it as the bases of your application or want to deploy it in you local network, you are encouraged to let it run in a docker container.

Install docker (e.g. like here: [Django installation Linux](https://www.simplilearn.com/tutorials/docker-tutorial/how-to-install-docker-on-ubuntu))

Install docker-compose.

Change in the .env file:

```
DB_HOST=db
DEBUG=0
```

And add the following line to the .env file:

```
DEPLOY_PORT=1339
DEPLOY_HOST=<your-ip-address>
```

Run
```
docker-compose up --build
```

You can now access montrek in your webbrowser:
```
127.0.0.1:1339
```

Or from any browser in you network:
```
<your-ip-address>:1339
```

*Note for installation on windows*:

Montrek can be installed on Windows via wsl. For this open a Powershell as administrator and determine the IP address of the wsl connection:
```
wsl hostname -I
```

(The first IP shown here should work.)

Now you can access wsl and install montrek as described above with the wsl IP as DEPLOY_HOST. You can access montrek locally via the wsl IP and the port you defined in the .env file. If you want to make montrek public to your localhost, you can do this from the powershell with:

```
netsh interfact portproxy add v4t<F2><F2><F2>o4 listenaddress=0.0.0.0 listenport=1339 connectaddress=<your-wsl-ip> connectport=1339
```
