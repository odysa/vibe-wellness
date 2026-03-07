"""
Generate drink_water.gif — stick figure raises a cup to mouth, drinks, lowers cup.

Style matches squats.gif / neck_rolls.gif:
  - 320x320, dark navy background #1a1b2e
  - Lavender stick figure #b8b8d0, line width 3
  - Ground line near bottom in slightly lighter shade
  - Joint circles at elbows/knees radius 4
  - Head circle radius 20
  - Blue cup #4a6aff held in right hand
  - 24 frames, 140 ms/frame, loop=0
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 320, 320
BG_COLOR = (26, 27, 46)          # #1a1b2e
FIG_COLOR = (184, 184, 208)       # #b8b8d0
GROUND_COLOR = (50, 52, 80)       # slightly lighter than bg
CUP_COLOR = (74, 106, 255)        # #4a6aff
CUP_HIGHLIGHT = (120, 150, 255)   # lighter rim highlight

LINE_WIDTH = 3
JOINT_RADIUS = 4
HEAD_RADIUS = 20

NUM_FRAMES = 24
FRAME_DURATION = 140  # ms

OUTPUT_PATH = Path(__file__).parent.parent / "vibe_wellness" / "gifs" / "drink_water.gif"

# ---------------------------------------------------------------------------
# Skeleton anchor points (neutral standing pose, centred)
# The figure stands with feet on the ground line at y=258.
# ---------------------------------------------------------------------------

# Centre X
CX = 160

# Vertical layout (top-down):
#   head centre  y=105
#   neck base    y=130
#   torso base   y=185
#   hip          y=185  (same as torso base, pelvis)
#   knee         y=222
#   ankle/foot   y=258  <- ground level

HEAD_Y = 105
NECK_Y = HEAD_Y + HEAD_RADIUS + 5       # 130
SHOULDER_Y = NECK_Y + 5                 # 135  (shoulder line == neck base approx)
TORSO_Y = 185                           # hip / pelvis
KNEE_Y = 222
FOOT_Y = 258

# Shoulder positions
SHOULDER_L = (CX - 22, SHOULDER_Y)
SHOULDER_R = (CX + 22, SHOULDER_Y)

# Hip positions
HIP_L = (CX - 14, TORSO_Y)
HIP_R = (CX + 14, TORSO_Y)

# Knee positions (standing, feet slightly apart)
KNEE_L = (CX - 16, KNEE_Y)
KNEE_R = (CX + 16, KNEE_Y)

# Ankle/foot positions
FOOT_L = (CX - 18, FOOT_Y)
FOOT_R = (CX + 20, FOOT_Y)


class Pose(NamedTuple):
    """Describes the right arm pose and head tilt for one frame."""
    # Right elbow position
    elbow_r: tuple[float, float]
    # Right wrist / hand position
    wrist_r: tuple[float, float]
    # Head centre offset (dy for tilt-back; head always stays at CX, HEAD_Y + dy)
    head_dy: float
    # Left arm — hangs naturally; only elbow_l / wrist_l need tweaking if desired
    elbow_l: tuple[float, float]
    wrist_l: tuple[float, float]


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_pt(
    p: tuple[float, float], q: tuple[float, float], t: float
) -> tuple[float, float]:
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))


def smoothstep(t: float) -> float:
    """Smoothstep easing: 3t²-2t³."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# Key poses
# ---------------------------------------------------------------------------

# Rest pose: right arm hangs down, cup at hip height
ELBOW_R_REST = (SHOULDER_R[0] + 18, SHOULDER_R[1] + 30)   # (200, 165)
WRIST_R_REST = (SHOULDER_R[0] + 24, TORSO_Y + 5)           # (206, 190)

ELBOW_L_REST = (SHOULDER_L[0] - 18, SHOULDER_L[1] + 30)   # (120, 165)
WRIST_L_REST = (SHOULDER_L[0] - 20, TORSO_Y + 5)           # (118, 190)

# Drink pose: right arm raised, wrist near mouth (just below head centre)
ELBOW_R_DRINK = (SHOULDER_R[0] + 10, SHOULDER_R[1] - 15)  # (192, 120)
WRIST_R_DRINK = (CX + 8, HEAD_Y + 14)                      # (168, 119)

ELBOW_L_DRINK = (SHOULDER_L[0] - 8, SHOULDER_L[1] - 5)    # (130, 130) slight raise
WRIST_L_DRINK = (SHOULDER_L[0] - 10, SHOULDER_L[1] + 20)  # (128, 155)

# Head tilt-back at peak drink
HEAD_DY_REST = 0.0
HEAD_DY_DRINK = -5.0   # slight backward tilt (head moves up a little)


def build_poses() -> list[Pose]:
    """
    Build 24 poses for the animation cycle:
      frames  0-5  : raise cup (rest -> drink)
      frames  6-10 : hold / drinking (small sip oscillation)
      frames 11-17 : lower cup (drink -> rest)
      frames 18-23 : rest pause before loop
    """
    poses: list[Pose] = []

    # --- Phase 1: raise (frames 0-5) ---
    raise_frames = 6
    for i in range(raise_frames):
        t = smoothstep(i / (raise_frames - 1))
        elbow_r = lerp_pt(ELBOW_R_REST, ELBOW_R_DRINK, t)
        wrist_r = lerp_pt(WRIST_R_REST, WRIST_R_DRINK, t)
        elbow_l = lerp_pt(ELBOW_L_REST, ELBOW_L_DRINK, t)
        wrist_l = lerp_pt(WRIST_L_REST, WRIST_L_DRINK, t)
        head_dy = lerp(HEAD_DY_REST, HEAD_DY_DRINK, t)
        poses.append(Pose(elbow_r, wrist_r, head_dy, elbow_l, wrist_l))

    # --- Phase 2: drinking sip oscillation (frames 6-10) ---
    sip_frames = 5
    for i in range(sip_frames):
        # Small oscillation: cup tilts slightly up and down
        osc = math.sin(i / (sip_frames - 1) * math.pi) * 4
        wrist_r = (WRIST_R_DRINK[0], WRIST_R_DRINK[1] - osc)
        elbow_r = (ELBOW_R_DRINK[0], ELBOW_R_DRINK[1] - osc * 0.4)
        head_dy = HEAD_DY_DRINK - osc * 0.3
        poses.append(
            Pose(elbow_r, wrist_r, head_dy, ELBOW_L_DRINK, WRIST_L_DRINK)
        )

    # --- Phase 3: lower cup (frames 11-17) ---
    lower_frames = 7
    for i in range(lower_frames):
        t = smoothstep(i / (lower_frames - 1))
        elbow_r = lerp_pt(ELBOW_R_DRINK, ELBOW_R_REST, t)
        wrist_r = lerp_pt(WRIST_R_DRINK, WRIST_R_REST, t)
        elbow_l = lerp_pt(ELBOW_L_DRINK, ELBOW_L_REST, t)
        wrist_l = lerp_pt(WRIST_L_DRINK, WRIST_L_REST, t)
        head_dy = lerp(HEAD_DY_DRINK, HEAD_DY_REST, t)
        poses.append(Pose(elbow_r, wrist_r, head_dy, elbow_l, wrist_l))

    # --- Phase 4: rest pause (frames 18-23) ---
    rest_frames = NUM_FRAMES - len(poses)  # 24 - 18 = 6
    for _ in range(rest_frames):
        poses.append(
            Pose(ELBOW_R_REST, WRIST_R_REST, HEAD_DY_REST, ELBOW_L_REST, WRIST_L_REST)
        )

    assert len(poses) == NUM_FRAMES, f"Expected {NUM_FRAMES} poses, got {len(poses)}"
    return poses


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def ipt(p: tuple[float, float]) -> tuple[int, int]:
    """Convert float point to int tuple."""
    return (int(round(p[0])), int(round(p[1])))


def draw_line(
    draw: ImageDraw.ImageDraw,
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: tuple[int, int, int],
    width: int,
) -> None:
    draw.line([ipt(p1), ipt(p2)], fill=color, width=width)


def draw_joint(
    draw: ImageDraw.ImageDraw,
    centre: tuple[float, float],
    radius: int,
    color: tuple[int, int, int],
) -> None:
    cx, cy = ipt(centre)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=color,
        outline=color,
    )


def draw_cup(
    draw: ImageDraw.ImageDraw,
    wrist: tuple[float, float],
    tilt_angle: float = 0.0,
) -> None:
    """
    Draw a small trapezoid cup centred on the wrist position.
    tilt_angle (degrees): positive = tilt cup toward mouth (rotate CW for right hand).
    The cup is drawn as a filled trapezoid with a rim highlight.
    """
    # Cup dimensions
    cup_w_bottom = 10
    cup_w_top = 13
    cup_h = 14

    # Build cup points relative to origin (bottom-centre at 0,0)
    pts_local = [
        (-cup_w_bottom / 2, 0),          # bottom-left
        (cup_w_bottom / 2, 0),           # bottom-right
        (cup_w_top / 2, -cup_h),         # top-right
        (-cup_w_top / 2, -cup_h),        # top-left
    ]

    # Apply tilt rotation around bottom-centre
    rad = math.radians(tilt_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    def rotate(x: float, y: float) -> tuple[float, float]:
        return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)

    # Translate so cup bottom-centre is at wrist position
    wx, wy = wrist
    pts = [
        (wx + rx, wy + ry)
        for (lx, ly) in pts_local
        for rx, ry in [rotate(lx, ly)]
    ]

    draw.polygon([ipt(p) for p in pts], fill=CUP_COLOR, outline=CUP_COLOR)

    # Rim highlight: line across the top edge
    draw.line([ipt(pts[3]), ipt(pts[2])], fill=CUP_HIGHLIGHT, width=2)


def draw_frame(pose: Pose) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Ground line ---
    draw.line([(30, FOOT_Y + 2), (290, FOOT_Y + 2)], fill=GROUND_COLOR, width=1)

    head_centre = (float(CX), HEAD_Y + pose.head_dy)

    # --- Legs ---
    # Left leg
    draw_line(draw, HIP_L, KNEE_L, FIG_COLOR, LINE_WIDTH)
    draw_line(draw, KNEE_L, FOOT_L, FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, KNEE_L, JOINT_RADIUS, FIG_COLOR)

    # Right leg
    draw_line(draw, HIP_R, KNEE_R, FIG_COLOR, LINE_WIDTH)
    draw_line(draw, KNEE_R, FOOT_R, FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, KNEE_R, JOINT_RADIUS, FIG_COLOR)

    # --- Torso ---
    draw_line(draw, (CX, SHOULDER_Y), (CX, TORSO_Y), FIG_COLOR, LINE_WIDTH)

    # --- Pelvis line ---
    draw_line(draw, HIP_L, HIP_R, FIG_COLOR, LINE_WIDTH)

    # --- Shoulder line ---
    draw_line(draw, SHOULDER_L, SHOULDER_R, FIG_COLOR, LINE_WIDTH)

    # --- Neck ---
    draw_line(draw, (CX, SHOULDER_Y), ipt(head_centre), FIG_COLOR, LINE_WIDTH)

    # --- Left arm ---
    draw_line(draw, SHOULDER_L, ipt(pose.elbow_l), FIG_COLOR, LINE_WIDTH)
    draw_line(draw, ipt(pose.elbow_l), ipt(pose.wrist_l), FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, pose.elbow_l, JOINT_RADIUS, FIG_COLOR)

    # --- Right arm (holding cup) ---
    draw_line(draw, SHOULDER_R, ipt(pose.elbow_r), FIG_COLOR, LINE_WIDTH)
    draw_line(draw, ipt(pose.elbow_r), ipt(pose.wrist_r), FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, pose.elbow_r, JOINT_RADIUS, FIG_COLOR)

    # --- Cup ---
    # Compute tilt based on how high the wrist is relative to rest
    wrist_ry = pose.wrist_r[1]
    raise_fraction = max(
        0.0,
        min(1.0, (WRIST_R_REST[1] - wrist_ry) / (WRIST_R_REST[1] - WRIST_R_DRINK[1])),
    )
    cup_tilt = raise_fraction * 55.0  # tilt up to 55 degrees when fully raised
    draw_cup(draw, pose.wrist_r, tilt_angle=cup_tilt)

    # --- Head (drawn last so it's on top) ---
    hx, hy = ipt(head_centre)
    draw.ellipse(
        [hx - HEAD_RADIUS, hy - HEAD_RADIUS, hx + HEAD_RADIUS, hy + HEAD_RADIUS],
        fill=FIG_COLOR,
        outline=FIG_COLOR,
    )

    return img


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    poses = build_poses()
    frames: list[Image.Image] = [draw_frame(p) for p in poses]

    # Build a single global palette from all frames to avoid flicker
    combined = Image.new("RGB", (WIDTH * len(frames), HEIGHT))
    for i, f in enumerate(frames):
        combined.paste(f, (i * WIDTH, 0))
    global_palette = combined.quantize(colors=64, method=Image.MEDIANCUT)
    palette_frames = [f.quantize(palette=global_palette, dither=0) for f in frames]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    palette_frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=palette_frames[1:],
        optimize=False,
        disposal=2,
        loop=0,
        duration=FRAME_DURATION,
    )
    print(f"Saved {NUM_FRAMES} frames -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
