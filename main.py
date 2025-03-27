from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import socketio
import asyncio
import os

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
origins = [
    "*",  # Replace with your frontend's Render URL in production for better security
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'frontend' directory (one level up)
app.mount("/static", StaticFiles(directory="./frontend"), name="static")

# Initialize SocketIO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*') # Adjust origins as needed for SocketIO
socketio_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def get():
    return HTMLResponse(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "index.html")).read())

@sio.on('connect')
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('message', 'Bot: Hello! How can I help you today?', room=sid)

@sio.on('disconnect')
def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.on('user_message')
async def handle_user_message(sid, message):
    print(f"Received message from {sid}: {message}")
    ai_response = await get_ai_response(message)
    await sio.emit('message', f'Bot: {ai_response}', room=sid)

import openai
import os
import asyncio

# Initialize OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

async def get_ai_response(user_message: str):
    if not openai.api_key:
        return "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    try:
        # OpenAI API call (no need for 'await' here)
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        # Extract response
        ai_response = completion.choices[0].message.content
        return ai_response
    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return "Sorry, I encountered an error while trying to respond."