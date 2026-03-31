import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import training, evaluation

# Instantiate api
app = FastAPI()


# Handle RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print("[422] Raw request body:", body.decode())
    print("[422] Validation errors:", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


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


# Check status point
@app.get("/")
async def root():
    return {"message": "FastAPI backend is running!"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
