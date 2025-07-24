import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from orchestrator import Orchestrator
from websocket_manager import manager
import uvicorn

# Initialize the FastAPI app
app = FastAPI()

# Create a single orchestrator instance
orchestrator = Orchestrator()

@app.on_event("startup")
async def startup_event():
    """On startup, run the orchestrator in the background."""
    print("--- Server starting up, initializing orchestrator ---")
    # Add an initial token to simulate a signal
    orchestrator.add_token_to_queue("DEBTCOIN") 
    await manager.broadcast({
        "type": "queue_update",
        "data": ["DEBTCOIN"] # Get this from the queue
    })
    # Run the orchestrator's main loop as a background task
    asyncio.create_task(orchestrator.run())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The WebSocket endpoint for the UI to connect to."""
    await manager.connect(websocket)
    print("UI Connected.")
    try:
        while True:
            # We just keep the connection open to send data from the server
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("UI Disconnected.")

# This is a simple way to serve the React app's build files
# You'll need to create a 'static' folder and place the React build there
app.mount("/", StaticFiles(directory="auto-trader-ui/dist", html=True), name="static")


if __name__ == "__main__":
    # Use uvicorn to run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)