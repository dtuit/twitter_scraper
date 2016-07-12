#Twitter_Scraper

Scrapes tweets from twitter.com and inserts into a SQL server database
Uses the [Celery](http://www.celeryproject.org/) asynchronous task queue/job queue as a framework.
Tested on Ubuntu 14.04 with pyhton 3.4
###Install requirements

* Python
 * [Celery](http://www.celeryproject.org/) 
	 * `pip install Celery`
 * [pymssql](https://msdn.microsoft.com/library/mt694094.aspx#Anchor_1) 
	 * `sudo apt-get install freetds-dev freetds-bin ` 
	 * `pip install pymssql`
 * [requests](http://docs.python-requests.org/en/master/)
 * [lxml](http://lxml.de/)
	 * `sudo apt-get install python3-lxml`
 * [cssselect](https://pythonhosted.org/cssselect/)
	 * `pip install cssselect`
* [RabbitMQ](https://www.rabbitmq.com/download.html)
	* `sudo apt-get install rabbitmq-server`

create a file keys.json file
which contains the SQL server connection parameters
```
{
    "server":  "SERVER.database.windows.net",
    "user": "USER@SERVER",
    "password": "password",
    "database": "databasename"
}
```