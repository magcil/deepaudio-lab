import uvicorn
from fastapi import FastAPI

from routers import training

# Instantiate api
app = FastAPI()

# Add routers
app.include_router(training.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)