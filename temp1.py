from datetime import timedelta, date, datetime

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield end_date - timedelta(n)

start_date = datetime.utcnow()
end_date = date(2015, 6, 2)
for single_date in daterange(start_date, end_date):
    print(datetime.utcnow().strftime("%Y-%m-%d"))