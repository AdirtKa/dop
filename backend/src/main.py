import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.routes import root_router, employee_router, auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employee_router, prefix="/employee", tags=["employee"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(root_router, prefix="")


def main() -> None:
    """Entry point."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == '__main__':
    main()
