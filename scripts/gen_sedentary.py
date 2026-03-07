"""
Generate sedentary.gif — stick figure rises from a chair and stretches arms overhead.

Style matches drink_water.gif / squats.gif:
  - 320x320, dark navy background #1a1b2e
  - Lavender stick figure #b8b8d0, line width 3
  - Ground line near bottom in slightly lighter shade
  - Joint circles at elbows/knees radius 4
  - Head circle radius 20
  - Chair/stool outline drawn in a muted lavender-grey
  - 24 frames, 140 ms/frame, loop=0

Animation phases
  frames  0-3  : sitting still (slight idle breath)
  frames  4-10 : stand-up transition (hips rise, legs straighten, torso lifts)
  frames 11-16 : arms sweep outward then up overhead (victory stretch)
  frames 17-20 : hold stretched pose
  frames 21-23 : brief return / loop-ready rest
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
BG_COLOR = (26, 27, 46)       # #1a1b2e
FIG_COLOR = (184, 184, 208)   # #b8b8d0
GROUND_COLOR = (50, 52, 80)   # slightly lighter than bg
CHAIR_COLOR = (70, 72, 105)   # muted lavender-grey for chair

LINE_WIDTH = 3
JOINT_RADIUS = 4
HEAD_RADIUS = 20

NUM_FRAMES = 24
FRAME_DURATION = 140  # ms

OUTPUT_PATH = (
    Path(__file__).parent.parent / "vibe_wellness" / "gifs" / "sedentary.gif"
)

# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

CX = 160  # horizontal centre

# Standing layout (top-down)
HEAD_Y_STAND = 98
NECK_Y_STAND = HEAD_Y_STAND + HEAD_RADIUS + 5   # 123
SHOULDER_Y_STAND = NECK_Y_STAND + 5             # 128
TORSO_Y_STAND = 180                             # hip / pelvis
KNEE_Y_STAND = 218
FOOT_Y = 255                                    # ground level

SHOULDER_L_STAND = (CX - 22, SHOULDER_Y_STAND)
SHOULDER_R_STAND = (CX + 22, SHOULDER_Y_STAND)
HIP_L_STAND = (CX - 14, TORSO_Y_STAND)
HIP_R_STAND = (CX + 14, TORSO_Y_STAND)
KNEE_L_STAND = (CX - 17, KNEE_Y_STAND)
KNEE_R_STAND = (CX + 17, KNEE_Y_STAND)
FOOT_L_STAND = (CX - 19, FOOT_Y)
FOOT_R_STAND = (CX + 19, FOOT_Y)

# Sitting layout — chair seat at y=215, feet flat on floor
SEAT_Y = 215
HEAD_Y_SIT = 148
NECK_Y_SIT = HEAD_Y_SIT + HEAD_RADIUS + 5      # 173
SHOULDER_Y_SIT = NECK_Y_SIT + 5                # 178
TORSO_Y_SIT = SEAT_Y - 4                       # 211  (hips just above seat)

SHOULDER_L_SIT = (CX - 22, SHOULDER_Y_SIT)
SHOULDER_R_SIT = (CX + 22, SHOULDER_Y_SIT)
HIP_L_SIT = (CX - 14, TORSO_Y_SIT)
HIP_R_SIT = (CX + 14, TORSO_Y_SIT)

# Bent knees when sitting: knees forward, shins go straight down
KNEE_L_SIT = (CX - 22, SEAT_Y + 5)
KNEE_R_SIT = (CX + 22, SEAT_Y + 5)
FOOT_L_SIT = (CX - 22, FOOT_Y)
FOOT_R_SIT = (CX + 22, FOOT_Y)

# Chair geometry (drawn once per frame based on sitting fraction)
CHAIR_SEAT_LEFT = CX - 34
CHAIR_SEAT_RIGHT = CX + 34
CHAIR_SEAT_Y = SEAT_Y
CHAIR_BACK_TOP_Y = SHOULDER_Y_SIT - 10
CHAIR_LEG_BOTTOM_Y = FOOT_Y

# ---------------------------------------------------------------------------
# Arm key positions
# ---------------------------------------------------------------------------

# Sitting rest: arms hang at sides on the chair
ELBOW_L_SIT = (SHOULDER_L_SIT[0] - 6, SHOULDER_L_SIT[1] + 28)
WRIST_L_SIT = (SHOULDER_L_SIT[0] - 4, TORSO_Y_SIT + 6)
ELBOW_R_SIT = (SHOULDER_R_SIT[0] + 6, SHOULDER_R_SIT[1] + 28)
WRIST_R_SIT = (SHOULDER_R_SIT[0] + 4, TORSO_Y_SIT + 6)

# Standing rest: arms hang naturally
ELBOW_L_STAND_REST = (SHOULDER_L_STAND[0] - 8, SHOULDER_Y_STAND + 32)
WRIST_L_STAND_REST = (SHOULDER_L_STAND[0] - 10, TORSO_Y_STAND + 6)
ELBOW_R_STAND_REST = (SHOULDER_R_STAND[0] + 8, SHOULDER_Y_STAND + 32)
WRIST_R_STAND_REST = (SHOULDER_R_STAND[0] + 10, TORSO_Y_STAND + 6)

# Arms wide (mid-stretch): elbows level with shoulders, wrists further out
ELBOW_L_WIDE = (CX - 62, SHOULDER_Y_STAND + 8)
WRIST_L_WIDE = (CX - 90, SHOULDER_Y_STAND + 12)
ELBOW_R_WIDE = (CX + 62, SHOULDER_Y_STAND + 8)
WRIST_R_WIDE = (CX + 90, SHOULDER_Y_STAND + 12)

# Arms overhead: V-shape victory stretch
ELBOW_L_UP = (CX - 38, SHOULDER_Y_STAND - 28)
WRIST_L_UP = (CX - 52, SHOULDER_Y_STAND - 62)
ELBOW_R_UP = (CX + 38, SHOULDER_Y_STAND - 28)
WRIST_R_UP = (CX + 52, SHOULDER_Y_STAND - 62)

# ---------------------------------------------------------------------------
# Data types & interpolation utilities
# ---------------------------------------------------------------------------


class Pose(NamedTuple):
    """Full skeleton pose for one frame."""
    head_y: float
    shoulder_y: float
    torso_y: float
    # Hip, knee, foot — left/right pairs stored as (x, y)
    hip_l: tuple[float, float]
    hip_r: tuple[float, float]
    knee_l: tuple[float, float]
    knee_r: tuple[float, float]
    foot_l: tuple[float, float]
    foot_r: tuple[float, float]
    # Arms
    elbow_l: tuple[float, float]
    wrist_l: tuple[float, float]
    elbow_r: tuple[float, float]
    wrist_r: tuple[float, float]
    # Fraction of sitting pose visible (for chair fade-out)
    sit_fraction: float


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_pt(
    p: tuple[float, float], q: tuple[float, float], t: float
) -> tuple[float, float]:
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    """Ken Perlin's quintic — even smoother acceleration/deceleration."""
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


# ---------------------------------------------------------------------------
# Pose builders
# ---------------------------------------------------------------------------

def _sit_pose(arm_sit_t: float = 1.0) -> Pose:
    """Full seated pose. arm_sit_t unused here but kept for consistency."""
    return Pose(
        head_y=HEAD_Y_SIT,
        shoulder_y=SHOULDER_Y_SIT,
        torso_y=TORSO_Y_SIT,
        hip_l=HIP_L_SIT,
        hip_r=HIP_R_SIT,
        knee_l=KNEE_L_SIT,
        knee_r=KNEE_R_SIT,
        foot_l=FOOT_L_SIT,
        foot_r=FOOT_R_SIT,
        elbow_l=ELBOW_L_SIT,
        wrist_l=WRIST_L_SIT,
        elbow_r=ELBOW_R_SIT,
        wrist_r=WRIST_R_SIT,
        sit_fraction=1.0,
    )


def _stand_rest_pose() -> Pose:
    return Pose(
        head_y=HEAD_Y_STAND,
        shoulder_y=SHOULDER_Y_STAND,
        torso_y=TORSO_Y_STAND,
        hip_l=HIP_L_STAND,
        hip_r=HIP_R_STAND,
        knee_l=KNEE_L_STAND,
        knee_r=KNEE_R_STAND,
        foot_l=FOOT_L_STAND,
        foot_r=FOOT_R_STAND,
        elbow_l=ELBOW_L_STAND_REST,
        wrist_l=WRIST_L_STAND_REST,
        elbow_r=ELBOW_R_STAND_REST,
        wrist_r=WRIST_R_STAND_REST,
        sit_fraction=0.0,
    )


def _stretch_pose(arm_t: float) -> Pose:
    """
    Standing pose with arms at a blend position.
    arm_t=0 -> hands at sides (stand rest)
    arm_t=0.5 -> arms wide
    arm_t=1.0 -> arms overhead
    """
    if arm_t <= 0.5:
        t2 = arm_t / 0.5
        el = lerp_pt(ELBOW_L_STAND_REST, ELBOW_L_WIDE, t2)
        wl = lerp_pt(WRIST_L_STAND_REST, WRIST_L_WIDE, t2)
        er = lerp_pt(ELBOW_R_STAND_REST, ELBOW_R_WIDE, t2)
        wr = lerp_pt(WRIST_R_STAND_REST, WRIST_R_WIDE, t2)
    else:
        t2 = (arm_t - 0.5) / 0.5
        el = lerp_pt(ELBOW_L_WIDE, ELBOW_L_UP, t2)
        wl = lerp_pt(WRIST_L_WIDE, WRIST_L_UP, t2)
        er = lerp_pt(ELBOW_R_WIDE, ELBOW_R_UP, t2)
        wr = lerp_pt(WRIST_R_WIDE, WRIST_R_UP, t2)
    return Pose(
        head_y=HEAD_Y_STAND,
        shoulder_y=SHOULDER_Y_STAND,
        torso_y=TORSO_Y_STAND,
        hip_l=HIP_L_STAND,
        hip_r=HIP_R_STAND,
        knee_l=KNEE_L_STAND,
        knee_r=KNEE_R_STAND,
        foot_l=FOOT_L_STAND,
        foot_r=FOOT_R_STAND,
        elbow_l=el,
        wrist_l=wl,
        elbow_r=er,
        wrist_r=wr,
        sit_fraction=0.0,
    )


def _blend_pose(a: Pose, b: Pose, t: float) -> Pose:
    s = smootherstep(t)
    return Pose(
        head_y=lerp(a.head_y, b.head_y, s),
        shoulder_y=lerp(a.shoulder_y, b.shoulder_y, s),
        torso_y=lerp(a.torso_y, b.torso_y, s),
        hip_l=lerp_pt(a.hip_l, b.hip_l, s),
        hip_r=lerp_pt(a.hip_r, b.hip_r, s),
        knee_l=lerp_pt(a.knee_l, b.knee_l, s),
        knee_r=lerp_pt(a.knee_r, b.knee_r, s),
        foot_l=lerp_pt(a.foot_l, b.foot_l, s),
        foot_r=lerp_pt(a.foot_r, b.foot_r, s),
        elbow_l=lerp_pt(a.elbow_l, b.elbow_l, s),
        wrist_l=lerp_pt(a.wrist_l, b.wrist_l, s),
        elbow_r=lerp_pt(a.elbow_r, b.elbow_r, s),
        wrist_r=lerp_pt(a.wrist_r, b.wrist_r, s),
        sit_fraction=lerp(a.sit_fraction, b.sit_fraction, s),
    )


# ---------------------------------------------------------------------------
# Build full animation sequence
# ---------------------------------------------------------------------------

def build_poses() -> list[Pose]:
    """
    Phase 0 (0-3):   sitting still with idle micro-breath (4 frames)
    Phase 1 (4-10):  stand-up transition, sit_fraction 1->0 (7 frames)
    Phase 2 (11-16): sweep arms wide then overhead (6 frames)
    Phase 3 (17-20): hold overhead stretch (4 frames)
    Phase 4 (21-23): lower arms back to stand-rest, ready to loop (3 frames)
    Total: 24 frames
    """
    poses: list[Pose] = []
    sit = _sit_pose()
    stand_rest = _stand_rest_pose()

    # --- Phase 0: sitting idle, micro-breath (4 frames) ---
    for i in range(4):
        # Tiny vertical oscillation to suggest breathing
        osc = math.sin(i / 3.0 * math.pi) * 1.5
        p = Pose(
            head_y=sit.head_y - osc,
            shoulder_y=sit.shoulder_y - osc,
            torso_y=sit.torso_y - osc * 0.5,
            hip_l=sit.hip_l,
            hip_r=sit.hip_r,
            knee_l=sit.knee_l,
            knee_r=sit.knee_r,
            foot_l=sit.foot_l,
            foot_r=sit.foot_r,
            elbow_l=(sit.elbow_l[0], sit.elbow_l[1] - osc),
            wrist_l=(sit.wrist_l[0], sit.wrist_l[1] - osc * 0.5),
            elbow_r=(sit.elbow_r[0], sit.elbow_r[1] - osc),
            wrist_r=(sit.wrist_r[0], sit.wrist_r[1] - osc * 0.5),
            sit_fraction=1.0,
        )
        poses.append(p)

    # --- Phase 1: stand up (7 frames) ---
    standup_frames = 7
    for i in range(standup_frames):
        t = i / (standup_frames - 1)
        poses.append(_blend_pose(sit, stand_rest, t))

    # --- Phase 2: sweep arms up (6 frames) ---
    sweep_frames = 6
    for i in range(sweep_frames):
        t = smootherstep(i / (sweep_frames - 1))
        poses.append(_stretch_pose(arm_t=t))

    # --- Phase 3: hold overhead (4 frames) ---
    for _ in range(4):
        poses.append(_stretch_pose(arm_t=1.0))

    # --- Phase 4: lower arms to stand-rest (3 frames) ---
    lower_frames = 3
    overhead = _stretch_pose(arm_t=1.0)
    for i in range(lower_frames):
        t = (i + 1) / lower_frames
        poses.append(_blend_pose(overhead, stand_rest, t))

    assert len(poses) == NUM_FRAMES, f"Expected {NUM_FRAMES}, got {len(poses)}"
    return poses


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def ipt(p: tuple[float, float]) -> tuple[int, int]:
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


def _chair_color(alpha: float) -> tuple[int, int, int]:
    """Blend chair color toward background based on fade amount (0=visible, 1=hidden)."""
    r = int(round(lerp(CHAIR_COLOR[0], BG_COLOR[0], alpha)))
    g = int(round(lerp(CHAIR_COLOR[1], BG_COLOR[1], alpha)))
    b = int(round(lerp(CHAIR_COLOR[2], BG_COLOR[2], alpha)))
    return (r, g, b)


def draw_chair(draw: ImageDraw.ImageDraw, sit_fraction: float) -> None:
    """
    Draw a simple stool/chair outline.  It fades out as the figure stands.
    sit_fraction: 1.0 = fully visible (sitting), 0.0 = invisible (standing).
    """
    if sit_fraction <= 0.01:
        return

    fade = 1.0 - sit_fraction   # 0 = fully visible
    cc = _chair_color(fade)
    lw = max(1, int(round(2 * sit_fraction)))

    seat_l = CHAIR_SEAT_LEFT
    seat_r = CHAIR_SEAT_RIGHT
    seat_y = CHAIR_SEAT_Y

    # Seat
    draw.line([(seat_l, seat_y), (seat_r, seat_y)], fill=cc, width=lw)

    # Back rest (left side of figure)
    back_x = seat_l + 4
    draw.line([(back_x, seat_y), (back_x, CHAIR_BACK_TOP_Y)], fill=cc, width=lw)
    draw.line(
        [(back_x, CHAIR_BACK_TOP_Y), (back_x + 20, CHAIR_BACK_TOP_Y)],
        fill=cc, width=lw,
    )

    # Front-left leg
    draw.line(
        [(seat_l + 6, seat_y), (seat_l + 6, CHAIR_LEG_BOTTOM_Y)],
        fill=cc, width=lw,
    )
    # Front-right leg
    draw.line(
        [(seat_r - 6, seat_y), (seat_r - 6, CHAIR_LEG_BOTTOM_Y)],
        fill=cc, width=lw,
    )


def draw_frame(pose: Pose) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Ground line ---
    draw.line([(30, FOOT_Y + 2), (290, FOOT_Y + 2)], fill=GROUND_COLOR, width=1)

    # --- Chair (behind figure) ---
    draw_chair(draw, pose.sit_fraction)

    # Derived positions from pose scalars
    shoulder_l = (SHOULDER_L_STAND[0], pose.shoulder_y)
    shoulder_r = (SHOULDER_R_STAND[0], pose.shoulder_y)
    hip_l = pose.hip_l
    hip_r = pose.hip_r
    knee_l = pose.knee_l
    knee_r = pose.knee_r
    foot_l = pose.foot_l
    foot_r = pose.foot_r
    head_centre = (float(CX), pose.head_y)

    # --- Left leg ---
    draw_line(draw, hip_l, knee_l, FIG_COLOR, LINE_WIDTH)
    draw_line(draw, knee_l, foot_l, FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, knee_l, JOINT_RADIUS, FIG_COLOR)

    # --- Right leg ---
    draw_line(draw, hip_r, knee_r, FIG_COLOR, LINE_WIDTH)
    draw_line(draw, knee_r, foot_r, FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, knee_r, JOINT_RADIUS, FIG_COLOR)

    # --- Torso ---
    torso_top = (float(CX), pose.shoulder_y)
    torso_bot = (float(CX), pose.torso_y)
    draw_line(draw, torso_top, torso_bot, FIG_COLOR, LINE_WIDTH)

    # --- Pelvis line ---
    draw_line(draw, hip_l, hip_r, FIG_COLOR, LINE_WIDTH)

    # --- Shoulder line ---
    draw_line(draw, shoulder_l, shoulder_r, FIG_COLOR, LINE_WIDTH)

    # --- Neck ---
    draw_line(draw, torso_top, head_centre, FIG_COLOR, LINE_WIDTH)

    # --- Left arm ---
    draw_line(draw, shoulder_l, pose.elbow_l, FIG_COLOR, LINE_WIDTH)
    draw_line(draw, pose.elbow_l, pose.wrist_l, FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, pose.elbow_l, JOINT_RADIUS, FIG_COLOR)

    # --- Right arm ---
    draw_line(draw, shoulder_r, pose.elbow_r, FIG_COLOR, LINE_WIDTH)
    draw_line(draw, pose.elbow_r, pose.wrist_r, FIG_COLOR, LINE_WIDTH)
    draw_joint(draw, pose.elbow_r, JOINT_RADIUS, FIG_COLOR)

    # --- Head (on top of everything) ---
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
