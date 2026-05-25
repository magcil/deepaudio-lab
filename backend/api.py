import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.session import Base, engine
from exceptions.handlers import register_exception_handlers
from routers import datasets, evaluation, run, tasks, training

# Instantiate api
app = FastAPI()
register_exception_handlers(app)

# Init database
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(training.router)
app.include_router(evaluation.router)
app.include_router(run.router)
app.include_router(tasks.router)
app.include_router(datasets.router)


# Check status point
@app.get("/")
async def root():
    return {"message": "FastAPI backend is running!"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
