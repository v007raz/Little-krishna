Here is a clean, developer-style `README.md` without emojis, buzzwords, or typical template filler.

```markdown
# Neon Sketch Reveal

A Python script that generates a dynamic neon particle and edge-sketch reveal animation from an image using OpenCV and NumPy.

## How it Works

1. Computes an edge mask from the input image and applies a multi-pass Gaussian blur glow filter.
2. Downsamples the glow layer into a mosaic grid and reveals circular blocks in random order.
3. Iteratively shrinks the block size to refine the mosaic into sharp neon sketch lines.
4. Smoothly crossfades from the neon edge sketch into the original image.
5. Adds a bottom vertical mirror gradient for a floor reflection effect.

## Requirements

- Python 3.8+
- OpenCV
- NumPy

Install the dependencies:

```bash
pip install opencv-python numpy

```

## Setup & Usage

1. Place your target image in the same directory as `particle_animation.py` and name it `krishna.png` (or update `INPUT_IMAGE` in the script).
2. Run the script:

```bash
python particle_animation.py

```

Press `q` or `Esc` at any time to exit the window.

## Configuration

You can adjust timing and visual parameters at the top of the script:

```python
# Window resolution
CANVAS_W, CANVAS_H = 1920, 1080
FULLSCREEN = True

# Animation duration (seconds)
DOT_REVEAL_SECONDS = 3.5      # Time for initial dot placement
REFINE_SECONDS     = 3.0      # Time taken to sharpen into neon lines
HOLD_SECONDS       = 3.0      # Pause on neon sketch
CROSSFADE_SECONDS  = 1.5      # Transition time to original image
FINAL_HOLD_SECONDS = 3.0      # Pause on final image

# Visual settings
MOSAIC_BLOCK_SIZE  = 10       # Initial dot size
LINE_THICKNESS     = 2        # Edge line dilation
GLOW_STRENGTH      = 1.6      # Bloom intensity
REFLECTION_HEIGHT_RATIO = 0.28 # Bottom reflection height (0.0 to disable)

```
