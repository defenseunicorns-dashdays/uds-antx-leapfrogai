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

## Testing environment
Use the following targets for `uds run` to bring up a dev deployment from `/src/backend`:
* `uds-up`: uses `test/uds-config.yaml` to create the proper minio buckets and credentials
* `registry-up`: crates a local docker registry for local image pushing
* `push-image`: pushes the api / listener image to the local registry
* `build-package`: Builds the zarf package with valkey
* `deploy-package`: Uses the `zarf-config-dev.yaml` to deploy the package