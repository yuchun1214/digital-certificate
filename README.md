# Digital Certificate Authentication Web-app

This is a centralized certificate authentication web-app. The app provides several functions. It could issue certificates and allows user to authenticate their certificates.

## Deployment

`config.yml` should be included in the root directory. The `config.yml` file stores the keys of [Google reCAPTCHA v3](https://developers.google.com/recaptcha/docs/v3) and it should be like
```
SITE_KEY: [site key]
SECRET_KEY: [secret key]
```
The web-app has used [Google reCAPTCHA v3](https://developers.google.com/recaptcha/docs/v3) to protect the website. The hash value and tokens are stored in the database.

**Before starting the server, it is of importance to setup the config file**


### Setup the virtual environment

```shell=
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Initialize Database

```shell=
flask --app digital-certificate init-db
```

### Start production server

There are indeed several ways to start the server in production mode. Here provides one, [gunicorn](https://gunicorn.org/).

```shell=
python3 -m pip install gunicorn
python3 -m gunicorn -w [number of processors] --bind [binding address] 'digital-certificate:create_app()'
```

## API docs

The website is built by employing the [flask](https://flask.palletsprojects.com/en/2.3.x/) framework. The website serves two things, allowing user to verify their certificates and re-download the certificates. 

### Authentication

#### Upload

* Endpoint: `/api/upload`
* Method: **POST**
* Response: JSON type data like.
```json!
{
    'message' : 'successful' | 'failed'
}
```
reponse the authentication result

The API only accepts file which could be submited by [formData](https://developer.mozilla.org/en-US/docs/Web/API/FormData).

### Download

#### Search File

* Endpoint: `/api/search`
* Method: **POST**
* Response: JSON type data like
```json!
{
    'message' : 'recaptcha failed' | 'id or date note found' | 'file not found' | 'ok',
    'token' : 'sha256 token(if avaliable)'
}
```
The search file api only accepts form data which contains the following fields
`id`, `date`, `recaptcha response`. The `date` should be the following format: **yyyy-mm-dd**. The recaptcha response should come from **Google reCAPTCHA** The API will verify the users are genuine or not and the data they provide is faulty.

If all the checkpoints are passed, the response will contain a token for user to download their file. For further explaination, please refer the next API's description.

#### Download file

* Endpoint: `/api/download`
* Method: **GET**
* Response: pdf file

The token gotten from the API `/api/search` would be used here to download the file only once. If user want to download a file several times, they have to use the search file to re-obtain the token. The relevant information used to download the file would be embeded in the query string. The qury string would have `id`, `date`, and `token`.
