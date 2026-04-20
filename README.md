# 🧵 Stitch-Pix — Interactive Cross-Stitch Pattern Generator

Stitch-Pix transforms an image into a symbol-based cross-stitch pattern. It includes a local web interface that lets you **preview**, **merge colors**, and **export** the final pattern bundle for printing or digital use.

---

## 🔧 Requirements
- **Python 3.13+**
- Install dependencies:  
  pip install fastapi uvicorn pillow python-multipart numpy scikit-learn

---

## 🧠 Project Structure
    stitch-pix/
    ├── main.py          # Core image & rendering logic
    ├── server.py        # FastAPI backend exposing /quantize and /render
    ├── index.html       # Web interface for uploading, merging & exporting
    └── README.md        # This file

---

## ▶️ Running the Application
1. Open a terminal inside the *stitch-pix* folder.  
2. Start the backend server:  
       py -m uvicorn server:app --reload  
   This launches the API at **http://127.0.0.1:8000**  
3. In a separate terminal, start a simple local web server:  
       py -m http.server 8080
   Then open **http://127.0.0.1:8080/index.html** in your browser.

---

## 💻 Using the Interface
1. **Upload files**  
   - Symbols image – PNG grid of symbols (for example use the one under /Examples)  
   - Image – picture to convert (tip: use transparent background for empty squares)
2. **Set parameters**  
   - Symbol dimension – pixel size per symbol  
   - Total colors – number of colors to quantize to (but this can be reduced in next stage by merging similar colors)  
   - Font size / Font path – optional font options  
3. Click **Quantize** → generates the initial palette.  
4. **Merge colors** → drag one color square onto another to average them.  
5. Click **Download bundle** → downloads a ZIP containing:  
   - reference.png — recolored reference image  
   - color_reference.png — color/symbol legend  
   - pattern.png — final cross-stitch pattern  

---

## 🧩 Notes
- Click **Quantize** again to rebuild the palette.  
- Color merges only affect the render step.  
- Mapping logic in *apply_color_mapping()* inside server.py.  

---

## ⚙️ Troubleshooting
**CORS blocked request** — ensure *server.py* includes:  
    from fastapi.middleware.cors import CORSMiddleware  
    app.add_middleware(  
        CORSMiddleware,  
        allow_origins=["http://127.0.0.1:8080","http://localhost:8080"],  
        allow_credentials=True,  
        allow_methods=["*"],  
        allow_headers=["*"],  
    )  

**Empty ZIP / no download** — check the terminal running uvicorn for errors.  

---

## 🪄 Example Workflow
    # Terminal 1
    py -3.13 -m uvicorn server:app --reload

    # Terminal 2
    python -m http.server 8080

Then open http://127.0.0.1:8080/index.html and:  
1. Upload symbol sheet + image  
2. Set parameters  
3. Click Quantize  
4. Merge colors  
5. Click Download bundle  
6. Extract pattern_bundle.zip  

---
