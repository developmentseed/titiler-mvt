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


## Demo

[`pixels`](demo/demo_pixels.html)

Elevation data `https://data.geo.admin.ch/ch.swisstopo.swissalti3d/swissalti3d_2019_2573-1085/swissalti3d_2019_2573-1085_0.5_2056_5728.tif`

![](https://user-images.githubusercontent.com/10407788/183614973-54518ded-a48b-4556-bcd7-ceb547129b95.jpg)


[`shapes`](demo/demo_shapes.html)

Land Cover classification `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_N39W111_Map.tif`

![](https://user-images.githubusercontent.com/10407788/183614967-7403ed4b-d86a-4e13-95cd-af9bdd667d67.jpg)
