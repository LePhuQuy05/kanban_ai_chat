from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.app.ai_client import OpenRouterError, run_ai_connectivity_check
from backend.app.board_service import (
    InvalidCredentialsError,
    BoardWriteError,
    get_board_for_user,
    update_board_for_user,
)
from backend.app.db import DEFAULT_DB_PATH
from backend.app.schemas import AICheckResponse, BoardPayload


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")
    app.state.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH


    @app.get("/api/hello")
    def read_hello() -> dict[str, str]:
        return {"message": "Hello from FastAPI"}

    def get_credentials(
        x_username: str | None = Header(default=None, alias="X-Username"),
        x_password: str | None = Header(default=None, alias="X-Password"),
    ) -> tuple[str, str]:
        if not x_username or not x_password:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        return x_username, x_password

    @app.get("/api/board", response_model=BoardPayload)
    def read_board(
        request: Request,
        credentials: tuple[str, str] = Depends(get_credentials),
    ) -> BoardPayload:
        username, password = credentials
        try:
            return get_board_for_user(request.app.state.db_path, username, password)
        except InvalidCredentialsError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error

    @app.put("/api/board", response_model=BoardPayload)
    def save_board(
        board: BoardPayload,
        request: Request,
        credentials: tuple[str, str] = Depends(get_credentials),
    ) -> BoardPayload:
        username, password = credentials
        try:
            return update_board_for_user(request.app.state.db_path, username, password, board)
        except InvalidCredentialsError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        except BoardWriteError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/ai/check", response_model=AICheckResponse)
    def ai_connectivity_check() -> AICheckResponse:
        try:
            reply = run_ai_connectivity_check()
            return AICheckResponse(reply=reply)
        except OpenRouterError as error:
            raise HTTPException(
                status_code=502,
                detail="OpenRouter request failed.",
            ) from error

    static_dir = Path(__file__).resolve().parent.parent / "static"

    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    else:

        @app.get("/", response_class=HTMLResponse)
        def read_root_fallback() -> str:
            return (
                "<h1>Frontend build not found</h1>"
                "<p>Run the container build to generate and serve the static frontend.</p>"
            )

    return app


app = create_app()
