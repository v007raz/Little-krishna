import os
import random
import cv2
import numpy as np

# --- CONFIGURATION ---
script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE = os.path.join(script_dir, 'krishna.png')

# Widescreen canvas centered for monitor display
CANVAS_W, CANVAS_H = 1920, 1080  
FPS = 60
WINDOW_NAME = "Cute Krishna Reveal"
FULLSCREEN = True

DOT_REVEAL_SECONDS = 3.5
REFINE_SECONDS = 3.0
HOLD_SECONDS = 3.0
CROSSFADE_SECONDS = 1.5
FINAL_HOLD_SECONDS = 3.0

MOSAIC_BLOCK_SIZE = 10
DOT_SHAPE = "circle"
DARK_PIXEL_SKIP = 18
RANDOM_SEED = 42

GLOW_COLOR_MODE = "original"
EDGE_LOW, EDGE_HIGH = 60, 150
LINE_THICKNESS = 2
GLOW_STRENGTH = 1.6
REFLECTION_HEIGHT_RATIO = 0.28

DISPLAY_BRIGHTNESS = 30
DISPLAY_CONTRAST = 1.0  
AUTO_CONTRAST = True

# --- FUNCTIONS ---
def load_and_fit(path, w, h):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    ih, iw = img.shape[:2]
    scale = min(w / iw, h / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    x_off = (w - new_w) // 2
    y_off = (h - new_h) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return canvas

def make_neon_edge_layer(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    edges = cv2.Canny(gray, EDGE_LOW, EDGE_HIGH)
    
    if LINE_THICKNESS > 0:
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=LINE_THICKNESS)

    mask = edges.astype(bool)
    color_layer = np.zeros_like(img)
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.7, 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * 1.5 + 60, 0, 255)
    boosted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    color_layer[mask] = boosted[mask]

    inner_glow = cv2.GaussianBlur(color_layer, (0, 0), sigmaX=4, sigmaY=4)
    outer_glow = cv2.GaussianBlur(color_layer, (0, 0), sigmaX=14, sigmaY=14)

    combined = (color_layer.astype(np.float32) * 1.4 + 
                inner_glow.astype(np.float32) * 1.1 + 
                outer_glow.astype(np.float32) * 0.7) * GLOW_STRENGTH

    combined = np.clip(combined, 0, 255)

    if AUTO_CONTRAST:
        lit_pixels = combined[combined > 5]
        if lit_pixels.size > 0:
            ref = np.percentile(lit_pixels, 99)
            if ref > 1:
                combined = np.clip(combined * (255.0 / ref), 0, 255)

    return combined.astype(np.uint8)

def block_mosaic(img, block_size):
    if block_size <= 1:
        return img.copy()

    h, w = img.shape[:2]
    ph = (block_size - h % block_size) % block_size
    pw = (block_size - w % block_size) % block_size
    padded = np.pad(img, ((0, ph), (0, pw), (0, 0)), mode="constant")
    
    H, W = padded.shape[:2]
    gh, gw = H // block_size, W // block_size

    reshaped = padded.reshape(gh, block_size, gw, block_size, 3)
    reshaped = reshaped.transpose(0, 2, 1, 3, 4).reshape(gh, gw, block_size * block_size, 3)

    intensity = reshaped.sum(axis=-1)                     
    idx = np.argmax(intensity, axis=-1)                   
    block_colors = np.take_along_axis(reshaped, idx[..., None, None], axis=2).squeeze(2)                                       

    upsampled = np.repeat(np.repeat(block_colors, block_size, axis=0), block_size, axis=1)
    return upsampled[:h, :w].astype(np.uint8)

def get_block_grid(mosaic_img, block_size):
    h, w = mosaic_img.shape[:2]
    blocks = []
    for by in range(0, h, block_size):
        for bx in range(0, w, block_size):
            color = mosaic_img[by, bx]
            if int(color.max()) <= DARK_PIXEL_SKIP:
                continue  
            bw = min(block_size, w - bx)
            bh = min(block_size, h - by)
            blocks.append((bx, by, bw, bh, tuple(int(c) for c in color)))
    return blocks

def draw_block(canvas, block):
    bx, by, bw, bh, color = block
    center = (bx + bw // 2, by + bh // 2)
    radius = max(1, min(bw, bh) // 2)
    cv2.circle(canvas, center, radius, color, -1, lineType=cv2.LINE_AA)

def add_reflection(frame, ratio):
    h, w = frame.shape[:2]
    refl_h = int(h * ratio)
    reflection = cv2.flip(frame[h - refl_h:h, :], 0)
    fade = np.linspace(0.35, 0.0, refl_h).reshape(refl_h, 1, 1)
    reflection = (reflection.astype(np.float32) * fade).astype(np.uint8)
    
    out = frame.copy()
    start_y = h - refl_h
    blended = cv2.addWeighted(out[start_y:h], 0.4, reflection, 0.9, 0)
    out[start_y:h] = np.maximum(out[start_y:h], blended)
    return out

def prepare_for_screen(frame):
    display = cv2.convertScaleAbs(frame, alpha=DISPLAY_CONTRAST, beta=DISPLAY_BRIGHTNESS)
    return display

def show_frame(frame, delay_ms):
    display_frame = prepare_for_screen(frame)
    cv2.imshow(WINDOW_NAME, display_frame)
    key = cv2.waitKey(delay_ms) & 0xFF
    return key != ord("q") and key != 27

def crossfade(frame_a, frame_b, t):
    return cv2.addWeighted(frame_a, 1 - t, frame_b, t, 0)

# --- MAIN ---
def main():
    try:
        base = load_and_fit(INPUT_IMAGE, CANVAS_W, CANVAS_H)
    except FileNotFoundError as e:
        print(e)
        return

    neon = make_neon_edge_layer(base)
    delay_ms = max(1, int(1000 / FPS))
    sharp_frame = add_reflection(neon, REFLECTION_HEIGHT_RATIO)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    if FULLSCREEN:
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    full_mosaic = block_mosaic(neon, MOSAIC_BLOCK_SIZE)
    blocks = get_block_grid(full_mosaic, MOSAIC_BLOCK_SIZE)

    rng = random.Random(RANDOM_SEED)
    order = blocks[:]
    rng.shuffle(order)

    # 1. Dot Reveal
    dot_frames = max(1, int(DOT_REVEAL_SECONDS * FPS))
    canvas = np.zeros_like(neon)
    revealed = 0

    for i in range(dot_frames):
        target = int(len(order) * (i + 1) / dot_frames)
        for block in order[revealed:target]:
            draw_block(canvas, block)
        revealed = target

        frame = add_reflection(canvas, REFLECTION_HEIGHT_RATIO)
        if not show_frame(frame, delay_ms): return

    # 2. Refine Edge Sketch
    refine_frames = max(1, int(REFINE_SECONDS * FPS))
    for i in range(refine_frames):
        t = (i + 1) / refine_frames
        block_size = max(1, int(MOSAIC_BLOCK_SIZE * (1 - t) ** 2))
        frame = block_mosaic(neon, block_size)
        frame = add_reflection(frame, REFLECTION_HEIGHT_RATIO)
        if not show_frame(frame, delay_ms): return

    # 3. Hold Sketch
    hold_frames = max(1, int(HOLD_SECONDS * FPS))
    for _ in range(hold_frames):
        if not show_frame(sharp_frame, delay_ms): return

    # 4. Crossfade
    crossfade_frames = max(1, int(CROSSFADE_SECONDS * FPS))
    for i in range(crossfade_frames):
        t = (i + 1) / crossfade_frames
        frame = crossfade(sharp_frame, base, t)
        if not show_frame(frame, delay_ms): return

    # 5. Final Hold
    final_hold_frames = max(1, int(FINAL_HOLD_SECONDS * FPS))
    for _ in range(final_hold_frames):
        if not show_frame(base, delay_ms): return

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
