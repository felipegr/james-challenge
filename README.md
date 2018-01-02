# James Challenge
The challenge was to implement an application through which a big bank can easily issue new loans and find out what the value and volume of outstanding debt are.

## Instalation instructions
* Install SQLite (for example in Ubuntu run `sudo apt-get update` and then `sudo apt-get install sqlite3 libsqlite3-dev`)
* Clone this repo
* Create a virtual environment and activate it
* Change directory to the project, `cd james-challenge/james`
* Upgrade packaging tools running `pip install --upgrade pip setuptools`
* Install the project in editable mode with its testing requirements running `pip install -e ".[testing]"`

## Running the application

To run the project in Development mode:
* Change directory to the project, `cd james-challenge/james`
* Create the database running `initialize_james_db development.ini`
* Run the application with `pserve development.ini`

The application is set to run at `http://0.0.0.0:8080`.
To access the API's endpoints the user must add an `authorization` key to the header of his request, with its value being a hexidecimal representation of the SHA256 encoding of the API key.
In Development the API key is `seekrit` and its encoded value is `c3d09a8c8b5d4ee86daa9d7926cccff543b55cb71bd0dfdc8ef5b2eff096f449`.

To run the project in Production mode:
* Set the following environment variables:
    * `SQLALCHEMY_URL` with the database connection string
    * `AUTH_SECRET` with a string representing the authentication secret of the application
    * `API_KEY` with a string representing the API key
* Create the database running `initialize_james_db production.ini`
* Run the application with `pserve production.ini`

Also in Production it would be advisable to run the application using `HTTPS`, which can be done by replacing the default `waitress` server by, for example, `gunicorn` (with the right configuration, of course),
or by using `nginx` as a reverse proxy that would handle HTTPS and pass HTTP to the application.

## API Enpoints
Please refer to https://gist.github.com/sergio2540/59d668fe820a06b1eebc42419cef3ef2.

In Development the URLs are `http://0.0.0.0:8080/loans`, `http://0.0.0.0:8080/loans/<:id>/payments` and `http://0.0.0.0:8080/loans/<:id>/balance`.

**Comments**:
* Payment's amount must be equal to the Loan's installment
* There can be only one payment per month
