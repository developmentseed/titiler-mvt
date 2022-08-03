"""app."""

import logging
from enum import Enum
from typing import Any, Dict

from mangum import Mangum
from rio_tiler.io import COGReader
from rio_tiler.models import BandStatistics, Info
from rio_tiler_mvt import pixels_encoder, shapes_encoder

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.responses import JSONResponse
from titiler.core.utils import Timer

from fastapi import FastAPI, Query

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette_cramjam.middleware import CompressionMiddleware

# turn off or quiet logs
logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)
logging.getLogger("shapely").setLevel(logging.ERROR)


class VectorTileType(str, Enum):
    """Available Output Vector Tile type."""

    pixels = "pixels"
    shapes = "shapes"


app = FastAPI(title="titiler-mvt", version="0.1.0")

add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_middleware(
    CompressionMiddleware,
    minimum_size=0,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
)
app.add_middleware(
    CacheControlMiddleware,
    cachecontrol="public, max-age=3600",
    exclude_path={r"/healthz"},
)


@app.get(
    "/info",
    response_model=Info,
    response_model_exclude_none=True,
    response_class=JSONResponse,
    responses={200: {"description": "Return dataset's basic info."}},
)
def info(url: str = Query(..., description="COG url")):
    """Return dataset's basic info."""
    with COGReader(url) as src_dst:
        return src_dst.info()


@app.get(
    "/statistics",
    response_model=Info,
    response_model_exclude_none=True,
    response_class=JSONResponse,
    responses={200: {"description": "Return dataset's basic info."}},
)
@app.get(
    "/statistics",
    response_model=Dict[str, BandStatistics],
    response_model_exclude_none=True,
    response_class=JSONResponse,
    responses={200: {"description": "Return the statistics of the COG."}},
)
def statistics(url: str = Query(..., description="COG url")):
    """Return dataset's statistics."""
    with COGReader(url) as src_dst:
        return src_dst.statistics()


@app.get(
    r"/tiles/pixels/{z}/{x}/{y}",
    responses={
        200: {
            "content": {"application/x-protobuf": {}},
            "description": "Return an a vector tile.",
        }
    },
    response_class=Response,
    description="Read COG and return a mvt tile",
)
def mvt_pixels(
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
            tile_data = src_dst.tile(x, y, z, tilesize=tilesize)

    timings.append(("cogread", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        content = pixels_encoder(
            tile_data.data,
            tile_data.mask,
            layer_name="cogeo",
            feature_type="polygon",
        )
    timings.append(("mvtencoding", round(t.elapsed * 1000, 2)))

    headers["Server-Timing"] = ", ".join(
        [f"{name};dur={time}" for (name, time) in timings]
    )

    return Response(content, media_type="application/x-protobuf", headers=headers)


@app.get(
    r"/tiles/shapes/{z}/{x}/{y}",
    responses={
        200: {
            "content": {"application/x-protobuf": {}},
            "description": "Return an a vector tile.",
        }
    },
    response_class=Response,
    description="Read COG and return a mvt tile",
)
def mvt_shapes(
    z: int,
    x: int,
    y: int,
    url: str = Query(..., description="COG url"),
    tilesize: int = Query(256, description="TileSize"),
    bidx: int = Query(description="Band index to render."),
):
    """Handle /mvt requests."""
    timings = []
    headers: Dict[str, str] = {}

    with Timer() as t:
        with COGReader(url) as src_dst:
            tile_data = src_dst.tile(x, y, z, tilesize=tilesize, indexes=bidx)
            cmap = src_dst.colormap or {}

    timings.append(("cogread", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        content = shapes_encoder(
            tile_data.data[0],
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
    request: Request,
    url: str = Query(..., description="COG url"),
    mvt_type: VectorTileType = Query(
        VectorTileType.pixels, description="MVT encoding type."
    ),
):
    """Handle /tilejson.json requests."""
    kwargs: Dict[str, Any] = {"z": "{z}", "x": "{x}", "y": "{y}"}
    tile_url = request.url_for(f"mvt_{mvt_type.name}", **kwargs)
    tile_url += f"?url={url}"

    with COGReader(url) as src_dst:
        bounds = src_dst.geographic_bounds
        minzoom = src_dst.minzoom
        maxzoom = src_dst.maxzoom

    return dict(
        bounds=bounds,
        minzoom=minzoom,
        maxzoom=maxzoom,
        name="cogeo",
        tilejson="2.1.0",
        tiles=[tile_url],
    )


@app.get("/healtz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


handler = Mangum(app)
