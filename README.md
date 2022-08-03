## titiler-mvt

![](https://user-images.githubusercontent.com/10407788/105131584-359e1680-5ab7-11eb-9c62-3eea96ea2091.png)

This is a DEMO based on work happening over [rio-tiler-mvt](https://github.com/cogeotiff/rio-tiler-mvt/issues/1)

## Deploy

```bash
# Install AWS CDK requirements
$ pip install -r requirements-cdk.txt
$ npm install

# Create AWS env
$ npm run cdk bootstrap

# Deploy app
$ npm run cdk deploy titiler-mvt-production
```

## Local testing

```
$ pip install -r requirements.txt uvicorn
$ uvicorn handler:app --reload --port 8080

open http://127.0.0.1:8080/docs
```
![](https://user-images.githubusercontent.com/10407788/182575689-08eb7ac5-d9df-467d-8dad-0ca34cded46a.png)
