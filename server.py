from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
import importlib.util, os
import json
from typing import Dict, Tuple
from collections import Counter

# load your existing main.py as a module
SPEC = importlib.util.spec_from_file_location("core", os.path.join(os.path.dirname(__file__), "main.py"))
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)

app = FastAPI(title="Cross-stitch API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RenderRequest(BaseModel):
    symbols_dimension: int
    total_colors: int
    font_size: int
    font_path: str | None = None
    # phase 2: add mapping: dict[hex_color]->symbol_index

def hex_to_rgba_tuple(hex_str: str) -> Tuple[int,int,int,int]:
    h = hex_str.strip().lstrip("#")
    r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
    a = int(h[6:8], 16) if len(h) >= 8 else 255
    return (r, g, b, a)

def apply_color_mapping(img: Image.Image, mapping_hex: Dict[str, str]) -> Image.Image:
    """Replace exact RGBA matches according to mapping_hex."""
    if not mapping_hex:
        return img
    mapping = {hex_to_rgba_tuple(k): hex_to_rgba_tuple(v) for k, v in mapping_hex.items()}
    src = img.convert("RGBA")
    px = src.load()
    w, h = src.size
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            # p is a 4-tuple already
            if p in mapping:
                px[x, y] = mapping[p]
    return src


def pil_to_png_response(img: Image.Image):
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.post("/quantize")
async def quantize(
    symbols: UploadFile = File(...),
    image: UploadFile = File(...),
    symbols_dimension: int = Form(...),
    total_colors: int = Form(...),
    font_size: int = Form(16),
    font_path: str = Form("")
):
    # load images
    sym_img = Image.open(BytesIO(await symbols.read())).convert("RGBA")
    in_img = Image.open(BytesIO(await image.read())).convert("RGBA")

    # replicate your pipeline (names match your functions)
    config = {"symbols_dimension": str(symbols_dimension), "font_size": str(font_size), "font_path": font_path}

    symbols_array = core.make_symbol_array(sym_img, int(symbols_dimension))
    pixel_array_consolidated = core.kmeans_color_quantization(in_img, int(total_colors))
    reference_image_consolidated = core.fill_reference_image(pixel_array_consolidated)
    unique_pixels_array = core.get_unique_pixels(reference_image_consolidated)

    if len(symbols_array) < len(unique_pixels_array):
        return JSONResponse(
            status_code=400,
            content={"error": f"Not enough symbols: {len(symbols_array)} for {len(unique_pixels_array)} colors."}
        )

    pixel_count = core.make_color_count(pixel_array_consolidated)
    pixel_dictionary = core.make_pixel_dictionary(unique_pixels_array)

    color_reference = core.create_symbol_color_reference(
        unique_pixels_array, pixel_dictionary, symbols_array, pixel_count, config
    )

    empty_image = core.create_empty_image_to_size(reference_image_consolidated, int(symbols_dimension))
    pattern_image = core.fill_pattern(
        reference_image_consolidated, symbols_array, empty_image, pixel_dictionary, int(symbols_dimension)
    )
    final_pattern = core.fill_with_squares(pattern_image, config)

    # JSON-safe payload (cast numpy types → Python ints/str)
    palette_hex = [f"#{r:02x}{g:02x}{b:02x}{a:02x}" for (r, g, b, a) in unique_pixels_array]

    # pixel_count might be a numpy array/list; coerce to plain ints
    try:
        counts_list = [int(x) for x in pixel_count]
    except TypeError:
        # fallback if it's a dict-like; stringify keys, int() values
        counts_list = [int(pixel_count[k]) for k in pixel_count]

    return {
        "palette": palette_hex,
        "counts": counts_list,
        "meta": {"symbols": int(len(symbols_array))}
    }


@app.post("/render")
async def render(
    symbols: UploadFile = File(...),
    image: UploadFile = File(...),
    symbols_dimension: int = Form(...),
    total_colors: int = Form(...),
    font_size: int = Form(16),
    font_path: str = Form(""),
    mapping: str = Form(default="")  # JSON string: { "#rrggbbaa": "#rrggbbaa", ... }
):
    try:
        # --- Load inputs ---
        sym_img = Image.open(BytesIO(await symbols.read())).convert("RGBA")
        in_img = Image.open(BytesIO(await image.read())).convert("RGBA")

        # --- Config / symbols ---
        sd = int(symbols_dimension)
        tc = int(total_colors)
        config = {"symbols_dimension": str(sd), "font_size": str(font_size), "font_path": font_path}
        symbols_array = core.make_symbol_array(sym_img, sd)

        # --- Baseline pipeline to consolidated reference ---
        pixel_array_consolidated = core.kmeans_color_quantization(in_img, tc)
        reference_image_consolidated = core.fill_reference_image(pixel_array_consolidated)

        # --- Optional: apply client merges (exact RGBA remap) ---
        mapping_hex = {}
        if mapping and mapping.strip():
            try:
                mapping_hex = json.loads(mapping)
                if not isinstance(mapping_hex, dict):
                    mapping_hex = {}
            except Exception:
                mapping_hex = {}
        if mapping_hex:
            reference_image_consolidated = apply_color_mapping(reference_image_consolidated, mapping_hex)

        # --- Unique colors after merges ---
        unique_pixels_array = core.get_unique_pixels(reference_image_consolidated)

        # Guard: enough symbols?
        if len(symbols_array) < len(unique_pixels_array):
            return JSONResponse(
                status_code=400,
                content={"error": f"Not enough symbols: {len(symbols_array)} for {len(unique_pixels_array)} colors after merging."}
            )

        # --- Recompute counts from the recolored reference (fixes KeyError) ---
        counts = Counter(reference_image_consolidated.getdata())  # keys are RGBA tuples
        pixel_count = {tuple(px): int(counts[tuple(px)]) for px in unique_pixels_array}

        # --- Symbol mapping + renders ---
        pixel_dictionary = core.make_pixel_dictionary(unique_pixels_array)

        color_reference = core.create_symbol_color_reference(
            unique_pixels_array, pixel_dictionary, symbols_array, pixel_count, config
        )

        empty_image = core.create_empty_image_to_size(reference_image_consolidated, sd)
        pattern_image = core.fill_pattern(
            reference_image_consolidated, symbols_array, empty_image, pixel_dictionary, sd
        )
        final_pattern = core.fill_with_squares(pattern_image, config)

        # --- Package as ZIP ---
        import zipfile
        zbuf = BytesIO()
        with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
            b1 = BytesIO(); reference_image_consolidated.save(b1, "PNG"); zf.writestr("reference.png", b1.getvalue())
            b2 = BytesIO(); color_reference.save(b2, "PNG"); zf.writestr("color_reference.png", b2.getvalue())
            b3 = BytesIO(); final_pattern.save(b3, "PNG"); zf.writestr("pattern.png", b3.getvalue())
        zbuf.seek(0)
        return StreamingResponse(
            zbuf,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=pattern_bundle.zip"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})