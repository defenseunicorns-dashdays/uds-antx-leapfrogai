## Backend structure
* Zarf package: `zarf.yaml` and `test/zarf-config-dev.yaml` are provided to set up valkey and (eventually) the API deployment and custom listener (not implemented yet).  `Dockerfile` will eventually build the image that will be used for this zarf package. `values/valkey.py` contains the values file for the valkey deployment.
* Code: `api.py` for the skeleton API, `ingest.py` for the skeleton ingestion engine, and `listener.py` for the skeleton listener.  `comms/` contains the s3, and valkey comms.  Leapfrog comms are not implemented yet.  `util/objects.py` contains data definitions for the api.
* Testing: `tasks.yaml` contains uds tasks to create k3d-slim-dev with the correct minio setup for development.  It also contains code to build and deploy the zarf package (right now this just contains valkey)

## Swagger
To access the backend API swagger docs, do the following steps:
1. Make sure you are in the `src/backend/` directory
2. `pip install -r requirements.txt`
3. `fastapi dev api.py`
4. open `localhost:8000/docs` in a browser

## Dummy API
There is a testing branch called `testing/dummy-api` that will very simply create fake updates to test the API.  It can be built from the zarf package for integration testing with the frontend.
* `/start/` endpoint will init a new dataframe.
* `/update/` will create a new row of data and return the most recent data.
* `/end/` will return the most recent data.

To use the `date` query parameter to initiate ingestion for a different date than the current date, use the follwoing command:
```bash
curl localhost:8000/start/?date=MMDDYYYY
```
example:
```bash
curl localhost:8000/start/?date=07292024
```

This will kick off ingestion looking only for S3 keys that start with the supplied date.

## Testing environment
Use the following targets and intstructions for `uds run` to bring up a dev deployment from `/src/backend`.
* `uds-up`: uses `test/uds-config.yaml` to create the proper minio buckets and credentials
* `registry-up`: crates a local docker registry for local image pushing
* `push-image`: pushes the api / listener image to the local registry
* `build-package-valkey`: Builds the valkey package
* `deploy-package-valkey`: Deploys the valkey package
* `build-package`: Builds the zarf package with valkey
* If you are only deploying for a testing environment, set `IS_TEST_DEPLOYMENT: 1` in `src/backend/zarf-config.yaml`
* `deploy-package`: Uses the `zarf-config.yaml` to deploy the package
* Port-forward the valkey service `valkey-master` on port 6379
* Port-forward the API on port 8000
* Port-forward minio in namespace `uds-dev-stack` on port 9000

## Testing loop DO NOT USE THIS IN PRODUCTION
* run the target `uds run e2e-test`, which will clear the data in valkey for the day and all objects in the `READ_BUCKET`
* Check the logs on the ingestion pod
* You can curl `localhost:8000/update/` to get the latest data.

The easiset way to test the API is to follow the steps for the swagger above and simply hit the `/start/` endpoint followed by multiple `/update/` endpoints and `/end/` endpoint to wipe the data.  The data is dummy data, but it is using the actual storage / query system in valkey found mostly in `util/loaders.py` and `comms/valkey.py`.