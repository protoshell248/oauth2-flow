import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import requests
import json

load_dotenv()

SERVER_PORT = int(os.getenv("SERVER_PORT"))

CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

AUTHORIZATION_URL = os.getenv("AUTHORIZATION_URL")
TOKEN_URL = os.getenv("TOKEN_URL")

REDIRECT_URL = os.getenv("REDIRECT_URL").format(SERVER_PORT=SERVER_PORT)

app = FastAPI()

ACCESS_TOKEN_FILE = "access_token.json"

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serves the index.html page."""
    context = {"request": request, "access_token": None, "redirect_url": REDIRECT_URL}
    return templates.TemplateResponse("index.html", context)


@app.get("/login")
async def login(request: Request):
    """Redirects the user to the authorization URL."""

    auth_url = (
        f"{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
    )
    print(f"auth_url: {auth_url}")
    return RedirectResponse(auth_url)


@app.get("/callback", response_class=HTMLResponse)
async def callback(request: Request):
    """Handles the callback after authorization."""

    error = None
    access_token = None

    code = request.query_params.get("code")

    print(f"code: {code}")

    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_ID,
        "redirect_uri": REDIRECT_URL,
        "grant_type": "authorization_code",
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        if response.status_code != 200:
            error = f"Failed to retrieve access token. Server returned: {response.status_code}"
        else:
            access_token_data = response.json()
            print(f"access_token_data: {access_token_data}")

            access_token = access_token_data.get("access_token")

            if not access_token:
                error = f"Access token not found in response"
    except Exception as e:
        error = f"Unknown error occurred: {str(e)}"

    context = {"request": request, "access_token": access_token, "error": error, "redirect_url": REDIRECT_URL}
    return templates.TemplateResponse("index.html", context)


if __name__ == "__main__":
    if CERT_PATH and KEY_PATH:
        uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT, ssl_certfile=CERT_PATH, ssl_keyfile=KEY_PATH)
    else:
        uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT)
