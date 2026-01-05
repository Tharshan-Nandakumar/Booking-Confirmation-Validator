# Booking Confirmation Validator

Python3.13 application. Uses [FASTAPI](https://fastapi.tiangolo.com). Local deployments are possible with [Docker Compose](https://docs.docker.com/compose/) and preferred IDE is [VSCode](https://code.visualstudio.com/).

Booking Confirmation Validator consists of two separate executables:

- Backend, lives in `backend\pybooking\app`
- Frontend, lives in `frontend`

## Development and running locally

We use Docker Compose to run all parts of the application - frontend and backend.

Even though the app is running inside a container, it is recommended that you:

- Create a python virtual environment with the correct packages installed for the backend

```
cd backend
python3 -m venv .venv
.venv\Scripts\activate
cd pybooking\app
python -m pip install -r requirements.txt
```

<sup>Hint: Try `source .venv/bin/activate` instead if you are using Linux or masOS</sup>

- Install the correct node modules for the frontend

```
cd frontend
npm install
```

You need to set these environment variables or create the following `.env` files:

In `frontend\.env`:

```
REACT_APP_BACKEND_URL=http://localhost:8000
```

In `backend\pybooking\.env`:

```
GEMINI_API_KEY=
FRONTEND_URL=http://localhost:3000
```

A GEMINI_API_KEY can be obtained in the [official gemini api website](https://ai.google.dev/gemini-api/docs). The deployed version of this application uses a free tier GEMINI_API_KEY, which allows 20 API calls per day. [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) can be upgraded with payment.

To bring up the application:

```
docker compose up
```

The backend application in `backend\pybooking\app` is mounted as a volume. FastAPI will detect any file system changes and reload the backend.

If you have changed `requirements.txt`, you should rebuild the backend by running:

```
docker compose up -d --build backend
```

The frontend application in `frontend` will also detect any file system changes on reload.

After running Docker, in your browser you can access:
| Service | Hostname |
| ------------ | -------------------------- |
| Frontend | http://localhost:3000 |
|Swagger docs |	http://localhost:8000/docs |

To run locally without Docker, two terminals are required:

To run the backend:

```
cd backend
.venv\Scripts\activate
cd pybooking
uvicorn app.main:app --reload --port 8000
```

To run the frontend:

```
cd frontend
npm start
```
