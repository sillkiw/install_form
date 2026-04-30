from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Simple File Upload")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    files = sorted(
        [path.name for path in UPLOADS_DIR.iterdir() if path.is_file()],
        key=str.lower,
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {"files": files},
    )


@app.post("/upload")
async def upload_file(
    files: Annotated[list[UploadFile], File(...)],
) -> RedirectResponse:
    saved_files = 0

    for file in files:
        filename = Path(file.filename or "").name
        if not filename:
            await file.close()
            continue

        destination = UPLOADS_DIR / filename
        content = await file.read()
        destination.write_bytes(content)
        await file.close()
        saved_files += 1

    if saved_files == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    return RedirectResponse(url="/", status_code=303)


@app.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    file_path = UPLOADS_DIR / safe_name
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=safe_name)
