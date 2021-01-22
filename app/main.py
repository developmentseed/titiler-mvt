"""titiler-pds app."""

import logging
import pathlib
from typing import Any, Dict

from brotli_asgi import BrotliMiddleware
from mangum import Mangum
from rio_tiler.io import COGReader
from rio_tiler.models import Info
from rio_tiler_mvt import shapes_encoder

from titiler.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.middleware import CacheControlMiddleware, TotalTimeMiddleware
from titiler.models.mapbox import TileJSON
from titiler.utils import Timer

from fastapi import FastAPI, Query

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates

# turn off or quiet logs
logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)
logging.getLogger("shapely").setLevel(logging.ERROR)

template_dir = str(pathlib.Path(__file__).parent.joinpath("templates"))
templates = Jinja2Templates(directory=template_dir)

app = FastAPI(title="titiler-mvt", version="0.1.0")


@app.get(
    "/info",
    response_model=Info,
    response_model_exclude={"minzoom", "maxzoom", "center"},
    response_model_exclude_none=True,
    responses={200: {"description": "Return dataset's basic info."}},
)
def info(url: str = Query(..., description="COG url")):
    """Return dataset's basic info."""
    with COGReader(url) as src_dst:
        return src_dst.info()


@app.get(
    r"/{z}/{x}/{y}",
    responses={
        200: {
            "content": {"application/x-protobuf": {}},
            "description": "Return an a vector tile.",
        }
    },
    response_class=Response,
    description="Read COG and return a mvt tile",
)
def mvt(
    z: int,
    x: int,
    y: int,
    url: str = Query(..., description="COG url"),
    tilesize: int = Query(256, description="TileSize"),
):
    """Handle /mvt requests."""
    timings = []
    headers: Dict[str, str] = {}

    with Timer() as t:
        with COGReader(url) as src_dst:
            tile_data = src_dst.tile(x, y, z, tilesize=tilesize, indexes=1)
            cmap = src_dst.colormap

    timings.append(("cogread", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        content = shapes_encoder(
            tile_data.data[0].astype("uint8"),
            tile_data.mask,
            layer_name="cogeo",
            colormap=cmap,
        )
    timings.append(("mvtencoding", round(t.elapsed * 1000, 2)))

    headers["Server-Timing"] = ", ".join(
        [f"{name};dur={time}" for (name, time) in timings]
    )
    return Response(content, media_type="application/x-protobuf", headers=headers)


@app.get(
    "/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
)
def tilejson(
    request: Request, url: str = Query(..., description="COG url"),
):
    """Handle /tilejson.json requests."""
    kwargs: Dict[str, Any] = {"z": "{z}", "x": "{x}", "y": "{y}"}
    tile_url = request.url_for("mvt", **kwargs)
    tile_url += f"?url={url}"

    with COGReader(url) as src_dst:
        bounds = src_dst.bounds
        center = src_dst.center
        minzoom = src_dst.minzoom
        maxzoom = src_dst.maxzoom

    return dict(
        bounds=bounds,
        center=center,
        minzoom=minzoom,
        maxzoom=maxzoom,
        name="cogeo",
        tilejson="2.1.0",
        tiles=[tile_url],
    )


@app.get(
    "/",
    responses={200: {"description": "Simple viewer."}},
    response_class=HTMLResponse,
)
async def viewer(request: Request):
    """Handle /index.html."""
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request, "tilejson": request.url_for("tilejson")},
        media_type="text/html",
    )


add_exception_handlers(app, DEFAULT_STATUS_CODES)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(BrotliMiddleware, minimum_size=0, gzip_fallback=True)
app.add_middleware(CacheControlMiddleware, cachecontrol="public, max-age=3600")
app.add_middleware(TotalTimeMiddleware)


@app.get("/healtz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


handler = Mangum(app)
