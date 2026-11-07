import pygame
import pygame.gfxdraw
import math
import random
import array

pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1600, 900
GROUND_Y = 750
NET_X = WIDTH // 2
NET_TOP = 400
NET_WIDTH = 12

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Beach Volleyball — Ultimate Edition")
clock = pygame.time.Clock()
FPS = 60

# ========== УРОВЕНЬ СЛОЖНОСТИ ==========
DIFFICULTY = 'normal'
DIFFICULTY_PARAMS = {
    'easy':   {'ai_speed': 0.60, 'ai_error': 0.20, 'ai_predict': False},
    'normal': {'ai_speed': 0.90, 'ai_error': 0.08, 'ai_predict': True},
    'hard':   {'ai_speed': 1.15, 'ai_error': 0.02, 'ai_predict': True},
}
DIFF = DIFFICULTY_PARAMS[DIFFICULTY]

# ========== ЗВУКИ ==========
def make_tone(freq, duration, volume=0.5, decay=True):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        t = i / sample_rate
        val = math.sin(2 * math.pi * freq * t)
        val += 0.3 * math.sin(2 * math.pi * freq * 2 * t)
        if decay:
            val *= (1 - i / n_samples) ** 2
        val = max(-1, min(1, val))
        buf.append(int(val * 32767 * volume))
    return pygame.mixer.Sound(buffer=buf)


def make_whistle():
    sample_rate = 22050
    duration = 0.25
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        t = i / sample_rate
        val = math.sin(2 * math.pi * 2200 * t)
        val += 0.4 * math.sin(2 * math.pi * 4400 * t)
        val += 0.2 * math.sin(2 * math.pi * 880 * t)
        env = min(1.0, i / (n_samples * 0.1)) * (1 - i / n_samples) ** 0.5
        val *= env
        val = max(-1, min(1, val))
        buf.append(int(val * 32767 * 0.85))
    return pygame.mixer.Sound(buffer=buf)


try:
    SND_HIT = make_tone(500, 0.06, 0.55)
    SND_WHISTLE = make_whistle()
except Exception as e:
    print("Ошибка звука:", e)
    SND_HIT = SND_WHISTLE = None


def play(snd, volume=1.0):
    if snd is not None:
        snd.set_volume(volume)
        snd.play()


# ========== ПАЛИТРА ==========
SKY_TOP = (110, 170, 215)
SKY_MID = (170, 205, 230)
SKY_HORIZON = (238, 218, 195)
OCEAN_TOP = (85, 130, 165)
OCEAN_BOTTOM = (65, 105, 140)
WAVE_HIGHLIGHT = (215, 230, 240)
CITY_COLOR = (195, 190, 195)
CITY_WINDOW = (150, 145, 155)
SAND_BASE = (224, 205, 178)
SAND_LIGHT = (235, 218, 190)
SAND_DARK = (200, 180, 155)
SAND_SHADOW = (175, 155, 132)
TRUNK_BASE = (120, 90, 65)
TRUNK_LIGHT = (155, 120, 90)
TRUNK_DARK = (75, 50, 35)
FROND_BASE = (70, 120, 70)
FROND_LIGHT = (105, 160, 95)
FROND_DARK = (45, 85, 50)
TRIBUNE_SHADOW = (105, 100, 95)
TRIBUNE_SEAT_RED = (175, 65, 60)
TRIBUNE_SEAT_BLUE = (65, 90, 160)

SKIN_TONES = [(250, 215, 180), (235, 195, 160), (215, 175, 140),
              (190, 150, 120), (165, 125, 95), (140, 100, 75),
              (110, 78, 55), (85, 60, 42)]
HAIR_COLORS = [(35, 25, 18), (60, 42, 28), (105, 68, 42), (155, 115, 70),
               (195, 170, 95), (130, 130, 130), (190, 190, 190), (160, 65, 45)]
SHIRT_COLORS = [(200, 70, 70), (70, 110, 190), (225, 190, 70), (75, 170, 100),
                (185, 85, 165), (225, 130, 55), (65, 175, 185), (235, 235, 235),
                (45, 45, 55), (145, 95, 55), (110, 75, 165), (235, 175, 195)]

CHEERS = ["GO GO GO!", "AWESOME!", "OH YEAH!", "COME ON!", "LET'S GO!",
          "NICE HIT!", "WOW!", "BOOM!", "OLE OLE!", "HEY!", "YES!",
          "AMAZING!", "SUPER!", "GREAT!", "KEEP IT UP!", "FIGHT!",
          "LET'S GO TEAM!", "BRAVO!", "WOOO!", "YEAH BABY!"]

# ========== ФИЗИКА (замедлено) ==========
GRAVITY = 900                # было 1400 — мяч летит медленнее
AIR_DRAG_COEF = 0.0001
MAGNUS_COEF = 0.002
BALL_RADIUS = 52

PLAYER_GRAVITY = 3500
PLAYER_SPEED = 520
PLAYER_JUMP = 1200
CROUCH_TIME = 0.09


# ========== АМБИЕНТНОЕ ОСВЕЩЕНИЕ ==========
class LightingSystem:
    KEYFRAMES = [
        (0,  (15, 20, 55),   (25, 30, 75),   (50, 60, 105),
             (40, 50, 110, 110), 0.75, 0.15, (220, 220, 200), 50,  0.6),
        (5,  (60, 60, 100),  (120, 90, 130), (200, 140, 150),
             (80, 70, 120, 70),  0.20, 0.40, (255, 200, 180), 80,  1.4),
        (7,  (255, 140, 110),(255, 180, 150),(255, 220, 180),
             (255, 180, 130, 30),0.10, 0.45, (255, 210, 160), 110, 1.5),
        (12, (110, 170, 215),(170, 205, 230),(238, 218, 195),
             (255, 255, 255, 0), 0.60, 0.10, (255, 250, 220), 140, 0.5),
        (17, (200, 180, 200),(230, 190, 180),(255, 210, 170),
             (255, 200, 150, 25),0.80, 0.40, (255, 220, 160), 120, 1.1),
        (19, (255, 110, 80), (255, 150, 100),(255, 200, 140),
             (255, 140, 90, 55), 0.88, 0.55, (255, 180, 100), 150, 1.7),
        (20, (255, 70, 60),  (200, 90, 90),  (180, 120, 110),
             (190, 90, 90, 75),  0.92, 0.65, (255, 150, 100), 110, 1.5),
        (22, (15, 20, 55),   (25, 30, 75),   (50, 60, 105),
             (40, 50, 110, 110), 0.75, 0.15, (220, 220, 200), 50,  0.6),
        (24, (15, 20, 55),   (25, 30, 75),   (50, 60, 105),
             (40, 50, 110, 110), 0.75, 0.15, (220, 220, 200), 50,  0.6),
    ]

    CYCLE_SECONDS = 180.0

    def __init__(self, start_hour=12.0):
        self.hour = start_hour

    def update(self, dt):
        self.hour += (24.0 / self.CYCLE_SECONDS) * dt
        if self.hour >= 24:
            self.hour -= 24

    @staticmethod
    def _lerp(a, b, t):
        if isinstance(a, tuple):
            return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(len(a)))
        return a * (1 - t) + b * t

    def get_state(self):
        h = self.hour
        kfs = self.KEYFRAMES
        for i in range(len(kfs) - 1):
            h1, h2 = kfs[i][0], kfs[i + 1][0]
            if h1 <= h <= h2:
                t = (h - h1) / (h2 - h1) if h2 > h1 else 0
                k1, k2 = kfs[i], kfs[i + 1]
                return {
                    'sky_top':      self._lerp(k1[1], k2[1], t),
                    'sky_mid':      self._lerp(k1[2], k2[2], t),
                    'sky_horizon':  self._lerp(k1[3], k2[3], t),
                    'ambient':      self._lerp(k1[4], k2[4], t),
                    'sun_x':        self._lerp(k1[5], k2[5], t),
                    'sun_y':        self._lerp(k1[6], k2[6], t),
                    'sun_color':    self._lerp(k1[7], k2[7], t),
                    'shadow_alpha': self._lerp(k1[8], k2[8], t),
                    'shadow_len':   self._lerp(k1[9], k2[9], t),
                }
        return None

    def rebuild_sky(self):
        state = self.get_state()
        surf = pygame.Surface((WIDTH, GROUND_Y))
        horizon = GROUND_Y - 300
        top, mid, bottom = state['sky_top'], state['sky_mid'], state['sky_horizon']
        for y in range(horizon):
            t = y / horizon
            if t < 0.55:
                k = t / 0.55
                c = tuple(int(top[i] * (1 - k) + mid[i] * k) for i in range(3))
            else:
                k = (t - 0.55) / 0.45
                c = tuple(int(mid[i] * (1 - k) + bottom[i] * k) for i in range(3))
            pygame.draw.line(surf, c, (0, y), (WIDTH, y))
        for y in range(horizon, GROUND_Y):
            pygame.draw.line(surf, bottom, (0, y), (WIDTH, y))
        return surf.convert()


# ========== ФОН ==========
def create_sky():
    surf = pygame.Surface((WIDTH, GROUND_Y))
    horizon = GROUND_Y - 300
    for y in range(horizon):
        t = y / horizon
        if t < 0.55:
            k = t / 0.55
            c = tuple(int(SKY_TOP[i] * (1 - k) + SKY_MID[i] * k) for i in range(3))
        else:
            k = (t - 0.55) / 0.45
            c = tuple(int(SKY_MID[i] * (1 - k) + SKY_HORIZON[i] * k) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))
    for y in range(horizon, GROUND_Y):
        pygame.draw.line(surf, SKY_HORIZON, (0, y), (WIDTH, y))
    return surf.convert()


def create_ocean_city_band():
    h = 90
    surf = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / h
        c = tuple(int(OCEAN_TOP[i] * (1 - t) + OCEAN_BOTTOM[i] * t) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))
    rng = random.Random(7)
    for _ in range(250):
        wx = rng.randint(0, WIDTH - 1)
        wy = rng.randint(8, h - 6)
        w = rng.randint(20, 70)
        alpha = rng.randint(50, 140)
        wave_surf = pygame.Surface((w, 2), pygame.SRCALPHA)
        wave_surf.fill((*WAVE_HIGHLIGHT, alpha))
        surf.blit(wave_surf, (wx, wy))
    rng2 = random.Random(11)
    x = 0
    while x < WIDTH:
        bw = rng2.randint(30, 75)
        bh = rng2.randint(20, 50)
        building_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        building_surf.fill((*CITY_COLOR, 200))
        for wy in range(4, bh - 4, 8):
            for wx in range(3, bw - 3, 7):
                if rng2.random() < 0.55:
                    pygame.draw.rect(building_surf, (*CITY_WINDOW, 180), (wx, wy, 3, 4))
        surf.blit(building_surf, (x, 2))
        x += bw + rng2.randint(3, 12)
    return surf.convert_alpha()


def create_sand():
    h = HEIGHT - GROUND_Y
    surf = pygame.Surface((WIDTH, h))
    for y in range(h):
        t = y / h
        c = tuple(int(SAND_BASE[i] * (1 - t) + SAND_DARK[i] * t) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))
    rng = random.Random(42)
    for _ in range(5000):
        x = rng.randint(0, WIDTH - 1)
        y = rng.randint(0, h - 1)
        shade = rng.choice([SAND_LIGHT, SAND_BASE, SAND_DARK, SAND_SHADOW,
                            (215, 195, 168), (230, 212, 185), (208, 188, 162)])
        pygame.draw.circle(surf, shade, (x, y), 1)
    return surf.convert()


def create_vignette():
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = WIDTH // 2, HEIGHT // 2
    max_dist = math.hypot(cx, cy)
    for r in range(int(max_dist), 0, -4):
        alpha = int(140 * (r / max_dist) ** 2)
        if alpha > 0:
            pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), r)
    return surf.convert_alpha()


SKY_SURF = create_sky()
OCEAN_CITY_SURF = create_ocean_city_band()
SAND_SURF = create_sand()
VIGNETTE = create_vignette()


# ========== ЛИЦО ==========
def draw_face(surface, cx, cy, r, skin_color, hair_color, eye_dir=0,
              animated=False, blink=False, happy=False, sad=False):
    cx, cy = int(cx), int(cy)
    r = int(r)
    darker_skin = tuple(max(0, c - 25) for c in skin_color)
    ear_color = tuple(max(0, c - 15) for c in skin_color)

    pygame.draw.ellipse(surface, ear_color, (cx - r - 5, cy - 3, 9, 16))
    pygame.draw.ellipse(surface, ear_color, (cx + r - 4, cy - 3, 9, 16))
    pygame.gfxdraw.filled_circle(surface, cx, cy, r, skin_color)
    pygame.gfxdraw.aacircle(surface, cx, cy, r, skin_color)

    shadow_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (*darker_skin, 100), (r + 2, r + 2), r)
    mask = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (r, 0, r + 4, r * 2 + 4))
    shadow_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow_surf, (cx - r - 2, cy - r - 2))

    highlight_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(highlight_surf, (255, 255, 255, 45), (r - r // 3, r - r // 3), r // 3)
    surface.blit(highlight_surf, (cx - r, cy - r))

    hair_dark = tuple(max(0, c - 35) for c in hair_color)
    hair_light = tuple(min(255, c + 25) for c in hair_color)
    hair_rect = pygame.Rect(cx - r - 2, cy - r - 8, r * 2 + 4, r + 12)
    pygame.draw.ellipse(surface, hair_color, hair_rect)
    for i in range(6):
        hx = cx - r + 4 + i * (r * 2 - 8) // 5
        pygame.draw.arc(surface, hair_light,
                        (hx - 5, cy - r - 6, 12, r + 4),
                        math.pi * 1.05, math.pi * 1.7, 2)

    forehead_color = tuple(min(255, c + 8) for c in skin_color)
    pygame.draw.ellipse(surface, forehead_color,
                        (cx - r + 4, cy - r + 6, r * 2 - 8, 12))

    brow_y = cy - int(r * 0.18)
    for side in [-1, 1]:
        bx = cx + side * int(r * 0.42)
        by = brow_y - 3 if happy else (brow_y + 2 if sad else brow_y)
        pygame.draw.arc(surface, hair_dark,
                        (bx - 8, by - 6, 16, 8),
                        math.pi * 1.05, math.pi * 1.95, 3)

    eye_y = cy - int(r * 0.05)
    eye_offset = int(r * 0.42)
    eye_w = int(r * 0.27)
    eye_h = int(r * 0.22)

    for side in [-1, 1]:
        ex = cx + side * eye_offset
        if blink:
            pygame.draw.line(surface, hair_dark,
                             (ex - eye_w, eye_y), (ex + eye_w, eye_y), 2)
            continue
        pygame.draw.ellipse(surface, (250, 248, 245),
                            (ex - eye_w, eye_y - eye_h, eye_w * 2, eye_h * 2))
        iris_r = int(eye_h * 0.85)
        iris_offset = eye_dir * 2
        pygame.gfxdraw.filled_circle(surface, ex + iris_offset, eye_y, iris_r, (95, 55, 25))
        pygame.gfxdraw.filled_circle(surface, ex + iris_offset, eye_y, max(2, iris_r - 3), (15, 10, 8))
        pygame.gfxdraw.filled_circle(surface, ex + iris_offset - 2, eye_y - 2, 2, (255, 255, 255))

    nose_x = cx
    nose_y = cy + int(r * 0.22)
    pygame.gfxdraw.filled_circle(surface, nose_x - 3, nose_y, 2, darker_skin)
    pygame.gfxdraw.filled_circle(surface, nose_x + 3, nose_y, 2, darker_skin)

    mouth_y = cy + int(r * 0.52)
    mouth_w = int(r * 0.45)
    lip_color = (175, 90, 85)

    if animated or happy:
        pygame.draw.arc(surface, lip_color,
                        (cx - mouth_w, mouth_y - 6, mouth_w * 2, 12),
                        math.pi * 1.05, math.pi * 1.95, 3)
        pygame.draw.arc(surface, (250, 245, 240),
                        (cx - mouth_w + 2, mouth_y - 3, mouth_w * 2 - 4, 8),
                        0.3, math.pi - 0.3, 3)
    elif sad:
        pygame.draw.arc(surface, lip_color,
                        (cx - mouth_w, mouth_y + 2, mouth_w * 2, 10),
                        math.pi + 0.4, 2 * math.pi - 0.4, 2)
    else:
        pygame.draw.arc(surface, lip_color,
                        (cx - mouth_w, mouth_y - 4, mouth_w * 2, 10),
                        0.25, math.pi - 0.25, 2)


# ========== ПАЛЬМА ==========
def create_palm_tree(scale=1.0):
    w = int(260 * scale)
    h = int(360 * scale)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    base_x = w // 2
    base_y = h - 4
    top_x = base_x + int(22 * scale)
    top_y = int(50 * scale)
    trunk_points = []
    segments = 30
    for i in range(segments + 1):
        t = i / segments
        px = base_x + math.sin(t * 1.8) * 22 * scale
        py = base_y - t * (base_y - top_y)
        trunk_points.append((px, py))
    pygame.draw.lines(surf, TRUNK_DARK, False, trunk_points, int(18 * scale))
    pygame.draw.lines(surf, TRUNK_BASE, False, trunk_points, int(14 * scale))
    for i in range(2, segments, 2):
        t = i / segments
        px, py = trunk_points[i]
        width_at = int((1 - t * 0.5) * 14 * scale)
        ring_color = TRUNK_DARK if i % 4 == 0 else TRUNK_LIGHT
        pygame.draw.line(surf, ring_color,
                         (int(px - width_at), int(py)),
                         (int(px + width_at), int(py)), 1)
    for cx_off, cy_off, r in [(-10, 4, 9), (6, 6, 8), (14, 0, 8)]:
        coco_x = int(top_x + cx_off * scale)
        coco_y = int(top_y + cy_off * scale)
        coco_r = int(r * scale)
        pygame.gfxdraw.filled_circle(surf, coco_x, coco_y, coco_r, (95, 60, 35))
        pygame.gfxdraw.aacircle(surf, coco_x, coco_y, coco_r, (60, 40, 25))
    for angle in [-175, -155, -135, -115, -95, -75, -55, -35, -15, 5]:
        rad = math.radians(angle)
        length = 120 * scale
        end_x = top_x + math.cos(rad) * length
        end_y = top_y + math.sin(rad) * length * 0.75 + 18 * scale
        pygame.draw.line(surf, FROND_DARK,
                         (int(top_x), int(top_y)), (int(end_x), int(end_y)),
                         max(2, int(4 * scale)))
        num_leaflets = 24
        for i in range(1, num_leaflets):
            t = i / num_leaflets
            lx = top_x + (end_x - top_x) * t
            ly = top_y + (end_y - top_y) * t
            leaf_len = (12 + 14 * math.sin(t * math.pi)) * scale
            perp = rad + math.pi / 2
            dx = math.cos(perp) * leaf_len
            dy = math.sin(perp) * leaf_len * 0.6
            color = FROND_LIGHT if i % 2 == 0 else FROND_BASE
            pygame.draw.line(surf, color,
                             (int(lx), int(ly)),
                             (int(lx + dx), int(ly - dy)), max(2, int(3 * scale)))
            pygame.draw.line(surf, FROND_BASE if i % 2 == 0 else FROND_LIGHT,
                             (int(lx), int(ly)),
                             (int(lx - dx), int(ly + dy)), max(2, int(3 * scale)))
    return surf.convert_alpha()


PALM_SPRITE = create_palm_tree(1.0)


# ========== БОЛЕЛЬЩИК ==========
_spectator_cache = {}


def get_spectator_sprite(skin, hair, shirt, size_key, leg_phase=0, walking=False):
    key = (skin, hair, shirt, size_key)
    if key in _spectator_cache and not walking:
        return _spectator_cache[key]
    scale = 0.65 + size_key * 0.10
    w = int(52 * scale)
    h = int(100 * scale)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    head_r = max(5, int(w * 0.23))
    head_cy = int(h * 0.18)
    darker_skin = tuple(max(0, c - 25) for c in skin)
    shoulder_y = head_cy + head_r + max(2, int(3 * scale))
    body_w = int(w * 0.78)
    body_h = int(h * 0.48)
    body_rect = pygame.Rect(cx - body_w // 2, shoulder_y, body_w, body_h)
    leg_w = max(3, int(6 * scale))
    leg_len = int(h * 0.30)
    leg_top = shoulder_y + body_h
    leg_y_bottom = leg_top + leg_len
    if walking:
        swing = math.sin(leg_phase) * 6 * scale
        left_x = cx - body_w // 4 + swing
        right_x = cx + body_w // 4 - swing
    else:
        left_x = cx - body_w // 4
        right_x = cx + body_w // 4
    pygame.draw.line(surf, darker_skin, (int(left_x), leg_top), (int(left_x), leg_y_bottom), leg_w)
    pygame.draw.line(surf, skin, (int(right_x), leg_top), (int(right_x), leg_y_bottom), leg_w)
    pygame.draw.ellipse(surf, (60, 40, 30), (int(left_x - leg_w), leg_y_bottom - 2, leg_w * 2, 5))
    pygame.draw.ellipse(surf, (60, 40, 30), (int(right_x - leg_w), leg_y_bottom - 2, leg_w * 2, 5))
    arm_thick = max(2, int(4 * scale))
    arm_len = int(w * 0.22)
    arm_y = shoulder_y + int(body_h * 0.25)
    pygame.draw.line(surf, skin, (cx - body_w // 2 + 2, arm_y),
                     (cx - body_w // 2 - arm_len, arm_y + arm_len), arm_thick)
    pygame.draw.line(surf, skin, (cx + body_w // 2 - 2, arm_y),
                     (cx + body_w // 2 + arm_len, arm_y + arm_len), arm_thick)
    pygame.draw.rect(surf, shirt, body_rect, border_radius=max(2, int(4 * scale)))
    pygame.gfxdraw.filled_circle(surf, cx, head_cy, head_r, skin)
    pygame.gfxdraw.aacircle(surf, cx, head_cy, head_r, skin)
    hair_rect = pygame.Rect(cx - head_r - 1, head_cy - head_r - 2, head_r * 2 + 2, head_r + 2)
    pygame.draw.ellipse(surf, hair, hair_rect)
    if head_r >= 4:
        eye_y = head_cy
        eye_offset = max(1, head_r // 3)
        eye_r = max(1, head_r // 5)
        pygame.draw.circle(surf, (250, 248, 245), (cx - eye_offset, eye_y), eye_r)
        pygame.draw.circle(surf, (250, 248, 245), (cx + eye_offset, eye_y), eye_r)
        pygame.draw.circle(surf, (30, 20, 15), (cx - eye_offset, eye_y), max(1, eye_r - 1))
        pygame.draw.circle(surf, (30, 20, 15), (cx + eye_offset, eye_y), max(1, eye_r - 1))
        pygame.draw.arc(surf, (150, 70, 70),
                        (cx - head_r // 2, head_cy + head_r // 3, head_r, head_r // 2),
                        math.pi * 1.15, math.pi * 1.85, 1)
    if not walking:
        _spectator_cache[key] = surf
    return surf


def draw_cheer_bubble(surface, x, y, text, font):
    text_surf = font.render(text, True, (40, 30, 30))
    tw, th = text_surf.get_size()
    pad_x, pad_y = 12, 6
    bubble_w = tw + pad_x * 2
    bubble_h = th + pad_y * 2
    bx = int(x - bubble_w // 2)
    by = int(y - bubble_h - 15)
    pygame.draw.ellipse(surface, (255, 255, 255), (bx, by, bubble_w, bubble_h))
    pygame.draw.ellipse(surface, (200, 200, 200), (bx, by, bubble_w, bubble_h), 2)
    tail = [(bx + bubble_w // 2 - 6, by + bubble_h - 2),
            (bx + bubble_w // 2, by + bubble_h + 10),
            (bx + bubble_w // 2 + 6, by + bubble_h - 2)]
    pygame.draw.polygon(surface, (255, 255, 255), tail)
    pygame.draw.polygon(surface, (200, 200, 200), tail, 2)
    surface.blit(text_surf, (bx + pad_x, by + pad_y))


# ========== ЧАСТИЦЫ ==========
class Particle:
    def __init__(self, x, y, vx, vy, color, size, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt
        self.vx *= 0.98
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * self.life / self.max_life)))
        size = max(1, int(self.size * (self.life / self.max_life)))
        if self.color[0] == 'rainbow':
            c = random.choice([(255, 80, 80), (80, 200, 100), (80, 130, 255),
                               (255, 220, 80), (200, 100, 220), (255, 150, 50)])
        else:
            c = self.color
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*c, alpha), (size, size), size)
        surface.blit(s, (int(self.x - size), int(self.y - size)))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn(self, x, y, count, base_color, speed=200, life=0.6, size=3):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - random.uniform(50, 150)
            self.particles.append(Particle(
                x + random.uniform(-5, 5), y + random.uniform(-5, 5),
                vx, vy, base_color, size * random.uniform(0.7, 1.5),
                life * random.uniform(0.7, 1.3)
            ))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)


# ========== СЛЕДЫ НА ПЕСКЕ ==========
class Footprint:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 6.0
        self.max_life = 6.0

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, int(120 * (self.life / self.max_life)))
        if alpha < 5:
            return
        s = pygame.Surface((20, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (150, 130, 105, alpha), (0, 0, 20, 12))
        surface.blit(s, (int(self.x - 10), int(self.y - 6)))


class FootprintTrail:
    def __init__(self):
        self.trails = {'left': [], 'right': []}
        self.last_step_time = {'left': 0, 'right': 0}

    def add(self, side, x, y, now):
        if now - self.last_step_time[side] > 0.22:
            self.trails[side].append(Footprint(x, y + 3))
            self.last_step_time[side] = now

    def update(self, dt):
        for side in self.trails:
            self.trails[side] = [f for f in self.trails[side] if f.update(dt)]

    def draw(self, surface):
        for side in self.trails:
            for f in self.trails[side]:
                f.draw(surface)


# ========== ОБЛАКО ==========
class Cloud:
    def __init__(self):
        self.reset(random_x=True)

    def reset(self, random_x=False):
        self.x = random.randint(-400, WIDTH) if random_x else -400
        self.y = random.randint(50, 200)
        self.size = random.uniform(60, 120)
        self.speed = random.uniform(0.25, 0.7)

    def update(self):
        self.x += self.speed
        if self.x - self.size * 2 > WIDTH:
            self.reset()

    def draw(self, surface):
        s = self.size
        cx, cy = int(self.x), int(self.y)
        white = (252, 252, 252)
        for ox, oy, rr in [(0, 0, s), (-s * 0.85, s * 0.15, s * 0.7),
                           (s * 0.85, s * 0.15, s * 0.75),
                           (-s * 0.35, -s * 0.35, s * 0.65), (s * 0.4, -s * 0.3, s * 0.7)]:
            ix, iy, ir = int(cx + ox), int(cy + oy), int(rr)
            pygame.gfxdraw.filled_circle(surface, ix, iy, ir, white)
            pygame.gfxdraw.aacircle(surface, ix, iy, ir, white)


# ========== ТРИБУНА ==========
class Tribune:
    ROWS = 4
    ROW_HEIGHT = 50
    START_Y = 350
    SPECTATORS_PER_ROW = 30

    def __init__(self):
        self.spectators = []
        for r in range(self.ROWS):
            row_y = self.START_Y + r * self.ROW_HEIGHT
            for i in range(self.SPECTATORS_PER_ROW):
                base_x = 40 + i * (WIDTH - 80) / self.SPECTATORS_PER_ROW
                self.spectators.append({
                    'x': base_x + random.uniform(-15, 15),
                    'y': row_y + 10, 'size_key': r,
                    'skin': random.choice(SKIN_TONES),
                    'hair': random.choice(HAIR_COLORS),
                    'shirt': random.choice(SHIRT_COLORS),
                    'bounce_phase': random.uniform(0, math.pi * 2),
                    'bounce_speed': random.uniform(0.05, 0.12),
                    'bounce_amp': random.uniform(1.5, 3.5),
                    'row': r, 'target_x': base_x, 'walking': False,
                    'walk_phase': 0, 'walk_speed': random.uniform(15, 35),
                    'stand_timer': random.uniform(1.0, 8.0), 'walk_timer': 0,
                    'cheer_timer': random.uniform(1.5, 45.0),
                    'cheering': False, 'cheer_text': "", 'cheer_duration': 0,
                })
        self.spectators.sort(key=lambda s: s['row'])

    def all_cheer(self, text, duration=3.0):
        for s in self.spectators:
            s['cheering'] = True
            s['cheer_text'] = text
            s['cheer_duration'] = duration

    def update(self, dt):
        for s in self.spectators:
            s['bounce_phase'] += s['bounce_speed']
            if s['walking']:
                s['walk_phase'] += dt * 12
                s['walk_timer'] -= dt
                dx = s['target_x'] - s['x']
                if abs(dx) < 3 or s['walk_timer'] <= 0:
                    s['walking'] = False
                    s['stand_timer'] = random.uniform(3.0, 12.0)
                else:
                    s['x'] += math.copysign(s['walk_speed'] * dt, dx)
            else:
                s['stand_timer'] -= dt
                if s['stand_timer'] <= 0 and random.random() < 0.3:
                    s['target_x'] = max(20, min(WIDTH - 20, s['x'] + random.uniform(-150, 150)))
                    s['walking'] = True
                    s['walk_timer'] = random.uniform(2.0, 6.0)
            if s['cheering']:
                s['cheer_duration'] -= dt
                if s['cheer_duration'] <= 0:
                    s['cheering'] = False
                    s['cheer_timer'] = random.uniform(15.0, 60.0)
            else:
                s['cheer_timer'] -= dt
                if s['cheer_timer'] <= 0:
                    s['cheering'] = True
                    s['cheer_text'] = random.choice(CHEERS)
                    s['cheer_duration'] = random.uniform(1.5, 2.5)

    def draw(self, surface, font, dark=0):
        for r in range(self.ROWS):
            row_y = self.START_Y + r * self.ROW_HEIGHT
            top_shade = 165 + r * 5 - dark
            top_shade = max(30, top_shade)
            pygame.draw.rect(surface, (top_shade, top_shade - 5, top_shade - 10),
                             (0, row_y, WIDTH, self.ROW_HEIGHT))
            pygame.draw.rect(surface, TRIBUNE_SHADOW, (0, row_y, WIDTH, 6))
            pygame.draw.line(surface, (90, 85, 80), (0, row_y), (WIDTH, row_y), 2)
            seat_color = TRIBUNE_SEAT_RED if r % 2 == 0 else TRIBUNE_SEAT_BLUE
            for sx in range(0, WIDTH, 40):
                pygame.draw.rect(surface, seat_color,
                                 (sx + 5, row_y + 18, 30, 8), border_radius=2)
        for s in self.spectators:
            sprite = get_spectator_sprite(s['skin'], s['hair'], s['shirt'], s['size_key'],
                                          leg_phase=s['walk_phase'] if s['walking'] else 0,
                                          walking=s['walking'])
            cheer_bonus = 0
            if s['cheering']:
                cheer_bonus = -abs(math.sin(s['cheer_duration'] * 10)) * 8
            offset_y = -abs(math.sin(s['bounce_phase'])) * s['bounce_amp'] + cheer_bonus
            x = int(s['x'] - sprite.get_width() // 2)
            y = int(s['y'] - sprite.get_height() + offset_y)
            surface.blit(sprite, (x, y))
            if s['cheering']:
                draw_cheer_bubble(surface, s['x'], y, s['cheer_text'], font)


# ========== МЯЧ ==========
class Ball:
    def __init__(self, particles):
        self.particles = particles
        self.trail = []
        self.reset()

    def reset(self):
        self.x = NET_X
        self.y = 280
        self.vx = 0.0
        self.vy = 0.0
        self.spin = 0.0
        self.radius = BALL_RADIUS
        self.hit_cooldown = 0
        self.touched_ground = False
        self.waiting = True
        self.bob_phase = 0
        self.visual_spin = 0.0
        self.trail = []
        self.wind = 0.0

    def update(self, dt):
        self.wind += math.sin(pygame.time.get_ticks() / 3000) * 0.01 * dt
        self.wind = max(-0.5, min(0.5, self.wind))

        if self.waiting:
            self.bob_phase += dt * 2
            self.y = 280 + math.sin(self.bob_phase) * 6
            self.visual_spin += dt * 0.5
            return

        prev_x, prev_y = self.x, self.y

        self.vx += self.wind * 20 * dt
        self.vy += GRAVITY * dt
        speed = math.hypot(self.vx, self.vy)
        if speed > 1:
            drag_force = AIR_DRAG_COEF * speed * speed
            self.vx += -drag_force * (self.vx / speed) * dt
            self.vy += -drag_force * (self.vy / speed) * dt
            perp_x = -self.vy / speed
            perp_y = self.vx / speed
            magnus_force = MAGNUS_COEF * self.spin * speed
            self.vx += perp_x * magnus_force * dt
            self.vy += perp_y * magnus_force * dt

        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        net_left = NET_X - NET_WIDTH / 2 - self.radius
        net_right = NET_X + NET_WIDTH / 2 + self.radius
        crossed_net = False
        if new_y > NET_TOP:
            if prev_x < net_left and new_x >= net_left:
                crossed_net = True
            elif prev_x > net_right and new_x <= net_right:
                crossed_net = True
            elif net_left <= prev_x <= net_right:
                crossed_net = True
        if crossed_net:
            if prev_x < NET_X:
                self.x = net_left - 1
            else:
                self.x = net_right + 1
            self.vx = -self.vx * 0.35
            self.vy = abs(self.vy) * 0.3 + 100
            self.spin = -self.spin * 0.3
            return

        self.x = new_x
        self.y = new_y
        self.spin *= 0.998
        # Уменьшено визуальное вращение
        self.visual_spin += (self.spin * 0.15 + self.vx * 0.05) * dt

        if speed > 400:
            self.trail.append({'x': self.x, 'y': self.y, 'r': self.radius, 'life': 0.35})
        new_trail = []
        for t in self.trail:
            t['life'] -= dt
            if t['life'] > 0:
                new_trail.append(t)
        self.trail = new_trail[-12:]

        if self.y + self.radius >= GROUND_Y:
            self.y = GROUND_Y - self.radius
            if not self.touched_ground:
                self.particles.spawn(self.x, GROUND_Y - 5, 18,
                                     (210, 190, 160), speed=250, life=0.7, size=4)
            self.touched_ground = True
            self.vx = 0
            self.vy = 0
            return

        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx * 0.75
            self.spin = -self.spin * 0.6
        if self.x + self.radius >= WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -self.vx * 0.75
            self.spin = -self.spin * 0.6

        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

    def launch(self):
        self.waiting = False
        direction = random.choice([-1, 1])
        self.vx = direction * random.uniform(300, 400)
        self.vy = -random.uniform(200, 320)
        self.spin = random.uniform(-2, 2)
        play(SND_HIT, 0.4)

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = int(self.radius)

        for t in self.trail:
            alpha = int(140 * (t['life'] / 0.35))
            tr = int(t['r'] * 0.85)
            trail_surf = pygame.Surface((tr * 2, tr * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (200, 200, 210, alpha), (tr, tr), tr)
            surface.blit(trail_surf, (int(t['x']) - tr, int(t['y']) - tr))

        shadow_scale = max(0.4, 1 - (GROUND_Y - self.y) / 600)
        sw = int(r * 2 * shadow_scale)
        shadow_surf = pygame.Surface((sw, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (140, 115, 85, 120), (0, 0, sw, 20))
        surface.blit(shadow_surf, (cx - sw // 2, GROUND_Y - 10))

        pygame.gfxdraw.filled_circle(surface, cx, cy, r, (248, 246, 240))
        angle_offset = math.degrees(self.visual_spin) % 360

        def draw_wedge(start_deg, end_deg, color):
            points = [(cx, cy)]
            steps = 30
            for i in range(steps + 1):
                a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
                points.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            pygame.draw.polygon(surface, color, points)

        draw_wedge(angle_offset % 360, (angle_offset + 120) % 360, (30, 85, 190))
        draw_wedge((angle_offset + 120) % 360, (angle_offset + 240) % 360, (235, 195, 45))

        for k in range(3):
            a = math.radians(angle_offset + k * 120)
            x1 = int(cx + math.cos(a) * r)
            y1 = int(cy + math.sin(a) * r)
            x2 = int(cx - math.cos(a) * r)
            y2 = int(cy - math.sin(a) * r)
            pygame.draw.line(surface, (90, 80, 70), (x1, y1), (x2, y2), 3)

        pygame.gfxdraw.aacircle(surface, cx, cy, r, (60, 55, 50))
        pygame.gfxdraw.aacircle(surface, cx, cy, r - 1, (120, 115, 110))

        highlight_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(highlight_surf, r // 2, r // 2, r // 3,
                                     (255, 255, 255, 160))
        surface.blit(highlight_surf, (cx - r, cy - r))


# ========== ИГРОК ==========
class Player:
    def __init__(self, x, color, skin, hair, is_ai=False, particles=None, footprints=None):
        self.x = x
        self.y = GROUND_Y
        self.color = color
        self.skin = skin
        self.hair = hair
        self.is_ai = is_ai
        self.w = 70
        self.h = 120
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.head_radius = 28
        self.hit_power = 1250
        self.hit_cooldown = 0
        self.reaction_delay = 0
        self.walk_phase = 0.0
        self.is_walking = False
        self.crouch_timer = 0.0
        self.pending_jump = False
        self.blink_timer = 0
        self.is_blinking = False
        self.particles = particles
        self.footprints = footprints
        self.breath_phase = 0
        self.emotion_timer = 0.0
        self.blocking = False
        self.step_side = 'left'

    def get_head_pos(self):
        return self.x, self.y - self.h - 25

    def get_body_rect(self):
        return pygame.Rect(int(self.x - self.w // 2), int(self.y - self.h), self.w, self.h)

    def try_jump(self):
        if self.on_ground and self.crouch_timer <= 0 and not self.pending_jump:
            self.crouch_timer = CROUCH_TIME
            self.pending_jump = True

    def update(self, keys, ball, dt, now):
        if self.pending_jump:
            self.crouch_timer -= dt
            if self.crouch_timer <= 0:
                self.vy = -PLAYER_JUMP
                self.on_ground = False
                self.pending_jump = False
                self.crouch_timer = 0

        if self.is_ai:
            self.ai_update(ball, dt)
        else:
            self.handle_input(keys, dt)

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += PLAYER_GRAVITY * dt

        if self.y >= GROUND_Y:
            if not self.on_ground:
                if self.particles:
                    self.particles.spawn(self.x, GROUND_Y - 5, 8,
                                         (200, 185, 155), speed=150, life=0.4, size=3)
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True

        horizontal_speed = abs(self.vx)
        if horizontal_speed > 20 and self.on_ground and not self.pending_jump:
            self.is_walking = True
            self.walk_phase += dt * (8 + horizontal_speed / 60)
            if self.footprints:
                self.step_side = 'right' if self.step_side == 'left' else 'left'
                offset = -12 if self.step_side == 'left' else 12
                self.footprints.add(self.step_side, self.x + offset, GROUND_Y, now)
            if horizontal_speed > 300 and self.particles and random.random() < 0.15:
                self.particles.spawn(self.x, GROUND_Y - 3, 1,
                                     (215, 200, 175), speed=80, life=0.4, size=2)
        else:
            self.is_walking = False
            self.walk_phase = 0

        self.breath_phase += dt * 1.5
        self.vx *= 0.85

        self.blink_timer += dt * 60
        if self.blink_timer > 180:
            self.is_blinking = True
            if self.blink_timer > 195:
                self.is_blinking = False
                self.blink_timer = 0

        if self.emotion_timer > 0:
            self.emotion_timer -= dt
        elif self.emotion_timer < 0:
            self.emotion_timer += dt

        if self.is_ai:
            self.x = max(50, min(NET_X - 150, self.x))
        else:
            self.x = max(NET_X + 50, min(WIDTH - 50, self.x))

        if self.can_hit(ball):
            self.hit(ball)

        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

    def handle_input(self, keys, dt):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.try_jump()
        self.blocking = keys[pygame.K_s] and not self.on_ground

    def ai_update(self, ball, dt):
        self.vx = 0
        if self.reaction_delay > 0:
            self.reaction_delay -= 1
            return
        if ball.waiting:
            return
        if DIFF['ai_predict']:
            predict_x = self.predict_ball_landing(ball)
        else:
            predict_x = ball.x
        diff = predict_x - self.x
        if abs(diff) > 8:
            speed = PLAYER_SPEED * DIFF['ai_speed']
            self.vx = speed * (1 if diff > 0 else -1)

        if (ball.y < GROUND_Y - 200 and
                abs(ball.x - self.x) < 150 and
                self.on_ground and ball.vy > 0):
            self.try_jump()

    def predict_ball_landing(self, ball):
        x, y = ball.x, ball.y
        vx, vy = ball.vx, ball.vy
        spin = ball.spin
        dt = 0.016
        for _ in range(500):
            vy += GRAVITY * dt
            speed = math.hypot(vx, vy)
            if speed > 1:
                drag_force = AIR_DRAG_COEF * speed * speed
                vx += -drag_force * (vx / speed) * dt
                vy += -drag_force * (vy / speed) * dt
                perp_x = -vy / speed
                perp_y = vx / speed
                magnus_force = MAGNUS_COEF * spin * speed
                vx += perp_x * magnus_force * dt
                vy += perp_y * magnus_force * dt
            x += vx * dt
            y += vy * dt
            spin *= 0.998
            if y + BALL_RADIUS >= GROUND_Y:
                break
            if abs(x - NET_X) < NET_WIDTH // 2 + BALL_RADIUS and y > NET_TOP:
                break
        return max(50, min(NET_X - 150, x))

    def check_collision(self, ball):
        head_x, head_y = self.get_head_pos()
        if math.hypot(ball.x - head_x, ball.y - head_y) < self.head_radius + ball.radius:
            return True, True
        body = self.get_body_rect()
        cx = max(body.left, min(ball.x, body.right))
        cy = max(body.top, min(ball.y, body.bottom))
        if math.hypot(ball.x - cx, ball.y - cy) < ball.radius:
            return True, False
        return False, False

    def can_hit(self, ball):
        if ball.waiting:
            return False
        if self.hit_cooldown > 0 or ball.hit_cooldown > 0:
            return False
        hit, _ = self.check_collision(ball)
        return hit

    def hit(self, ball):
        self.hit_cooldown = 8
        ball.hit_cooldown = 8
        hit, is_head = self.check_collision(ball)

        if is_head:
            cx, cy = self.get_head_pos()
            min_dist = self.head_radius + ball.radius
        else:
            body = self.get_body_rect()
            cx = max(body.left, min(ball.x, body.right))
            cy = max(body.top, min(ball.y, body.bottom))
            min_dist = ball.radius + 2

        dx = ball.x - cx
        dy = ball.y - cy
        dist = max(1, math.hypot(dx, dy))
        if dist < min_dist:
            ball.x = cx + dx / dist * min_dist
            ball.y = cy + dy / dist * min_dist

        direction = 1 if self.is_ai else -1
        power = self.hit_power * (1.0 if is_head else 0.6)

        # Смаш убран — обычный удар, спин небольшой
        ball.spin = random.uniform(4, 10) * direction

        if self.is_ai and random.random() < DIFF['ai_error']:
            power *= 0.55
            ball.vx = power * direction * random.uniform(0.4, 0.6)
            ball.vy = -power * random.uniform(0.4, 0.55)
        else:
            # Замедлено (было 0.85-1.0 и 0.7-0.9)
            ball.vx = power * direction * random.uniform(0.55, 0.7)
            ball.vy = -power * random.uniform(0.5, 0.65)

        ball.vy -= random.uniform(30, 80)

        dx_to_net = NET_X - ball.x
        if dx_to_net * ball.vx > 0 and abs(ball.vx) > 1:
            t = abs(dx_to_net / ball.vx)
            if t < 2.5:
                y_at_net = ball.y + ball.vy * t + 0.5 * GRAVITY * t * t
                target_y = NET_TOP - 60
                if y_at_net > target_y:
                    extra_vy = (target_y - y_at_net) / t
                    extra_vy = max(extra_vy, -3000)
                    ball.vy += extra_vy

        ball.touched_ground = False
        play(SND_HIT, 0.55)

        if self.particles:
            self.particles.spawn(ball.x, ball.y, 6,
                                 (255, 240, 200), speed=180, life=0.4, size=3)

        if self.is_ai:
            self.reaction_delay = random.randint(3, 10)

    def draw(self, surface, lighting_state=None):
        cx = int(self.x)
        crouch_drop = int(15 * (self.crouch_timer / CROUCH_TIME)) if self.pending_jump else 0

        # Тень — динамическая по времени суток
        jump_height = max(0, GROUND_Y - self.y)
        shadow_scale = max(0.35, 1 - jump_height / 500)

        if lighting_state is not None:
            sun_x_px = lighting_state['sun_x'] * WIDTH
            shadow_length = int(60 * lighting_state['shadow_len'])
            shadow_dir = -1 if self.x > sun_x_px else 1
            shadow_alpha = int(lighting_state['shadow_alpha'] * shadow_scale)

            sw = int(100 * shadow_scale + shadow_length)
            sh = int(16 * shadow_scale)
            offset = shadow_dir * shadow_length // 2

            shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (90, 75, 60, shadow_alpha), (0, 0, sw, sh))
            surface.blit(shadow_surf, (cx - sw // 2 + offset, GROUND_Y - sh // 2 - 1))
        else:
            sw = int(110 * shadow_scale)
            sh = int(18 * shadow_scale)
            shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (140, 115, 85, 140), (0, 0, sw, sh))
            surface.blit(shadow_surf, (cx - sw // 2, GROUND_Y - sh // 2 - 1))

        sink = 3 if (self.on_ground and not self.is_walking) else 0
        darker_skin = tuple(max(0, c - 30) for c in self.skin)
        mid_skin = tuple(max(0, c - 15) for c in self.skin)
        light_skin = tuple(min(255, c + 15) for c in self.skin)

        # ===== НОГИ (бедро + голень + колено) =====
        if self.is_walking:
            swing = math.sin(self.walk_phase) * 14
            knee_bend_l = abs(math.sin(self.walk_phase)) * 4
            knee_bend_r = abs(math.sin(self.walk_phase + math.pi)) * 4
            left_leg_offset = swing
            right_leg_offset = -swing
        elif self.pending_jump:
            left_leg_offset = -8
            right_leg_offset = 8
            knee_bend_l = 8
            knee_bend_r = 8
        elif not self.on_ground:
            left_leg_offset = -6
            right_leg_offset = 6
            knee_bend_l = 6
            knee_bend_r = 6
        else:
            left_leg_offset = 0
            right_leg_offset = 0
            knee_bend_l = 0
            knee_bend_r = 0

        hip_y = int(self.y - 45 + crouch_drop + sink)
        knee_y = int(self.y - 22 + crouch_drop + sink)
        foot_y = int(self.y + sink)

        # Левая нога
        hip_l = (int(cx - 14 + left_leg_offset), hip_y)
        knee_l = (int(cx - 16 + left_leg_offset + knee_bend_l), knee_y)
        foot_l = (int(cx - 18 + left_leg_offset), foot_y)
        pygame.draw.line(surface, darker_skin, hip_l, knee_l, 18)
        pygame.draw.line(surface, mid_skin, knee_l, foot_l, 16)
        pygame.draw.circle(surface, darker_skin, knee_l, 10)
        pygame.draw.ellipse(surface, (60, 40, 30),
                            (foot_l[0] - 10, foot_l[1] - 4, 22, 8))

        # Правая нога
        hip_r = (int(cx + 14 + right_leg_offset), hip_y)
        knee_r = (int(cx + 16 + right_leg_offset + knee_bend_r), knee_y)
        foot_r = (int(cx + 18 + right_leg_offset), foot_y)
        pygame.draw.line(surface, self.skin, hip_r, knee_r, 18)
        pygame.draw.line(surface, self.skin, knee_r, foot_r, 16)
        pygame.draw.circle(surface, self.skin, knee_r, 10)
        pygame.draw.circle(surface, darker_skin, knee_r, 10, 2)
        pygame.draw.ellipse(surface, (80, 55, 40),
                            (foot_r[0] - 10, foot_r[1] - 4, 22, 8))

        # ===== Дыхание =====
        breath = math.sin(self.breath_phase) * 1.5 if (self.on_ground and not self.is_walking) else 0

        # ===== ШОРТЫ =====
        shorts_y = int(self.y - 68 + crouch_drop + sink + breath)
        shorts_rect = pygame.Rect(int(cx - self.w // 2 + 4), shorts_y, self.w - 8, 32)
        pygame.draw.rect(surface, (35, 45, 75), shorts_rect, border_radius=8)
        pygame.draw.rect(surface, (20, 25, 45), shorts_rect, width=2, border_radius=8)
        pygame.draw.line(surface, (70, 85, 120),
                         (shorts_rect.left + 6, shorts_rect.top + 4),
                         (shorts_rect.left + 20, shorts_rect.top + 4), 2)

        # ===== ТОРС (майка) =====
        torso_y = int(self.y - self.h + 18 + crouch_drop + sink + breath)
        torso_rect = pygame.Rect(int(cx - self.w // 2 + 6), torso_y,
                                 self.w - 12, self.h - 82)
        pygame.draw.rect(surface, self.color, torso_rect, border_radius=14)
        # Блик слева
        highlight = pygame.Surface((torso_rect.width // 3, torso_rect.height - 8),
                                   pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 45))
        surface.blit(highlight, (torso_rect.left + 3, torso_rect.top + 4))
        # Тень справа
        shadow = pygame.Surface((torso_rect.width // 3, torso_rect.height - 8),
                                pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 50))
        surface.blit(shadow, (torso_rect.right - torso_rect.width // 3 - 3,
                              torso_rect.top + 4))
        # Полоса
        pygame.draw.line(surface, (255, 255, 255),
                         (torso_rect.left + 6, torso_rect.centery),
                         (torso_rect.right - 6, torso_rect.centery), 3)
        pygame.draw.rect(surface, (30, 20, 15), torso_rect, width=2, border_radius=14)

        # Номер
        num_font = pygame.font.SysFont("Arial", 24, bold=True)
        num_shadow = num_font.render("7", True, (0, 0, 0))
        num_text = num_font.render("7", True, (255, 255, 255))
        nx = cx - num_text.get_width() // 2
        ny = torso_rect.top + 8
        surface.blit(num_shadow, (nx + 1, ny + 1))
        surface.blit(num_text, (nx, ny))

        # ===== РУКИ =====
        arm_raised = self.hit_cooldown > 4
        arm_blocking = self.blocking
        shoulder_y = self.y - self.h + 28 + crouch_drop + sink + breath

        if arm_blocking:
            sh_l = (int(cx - 26), int(shoulder_y))
            el_l = (int(cx - 22), int(shoulder_y - 40))
            hand_l = (int(cx - 5), int(shoulder_y - 78))
            pygame.draw.line(surface, self.skin, sh_l, el_l, 14)
            pygame.draw.line(surface, self.skin, el_l, hand_l, 13)
            pygame.draw.circle(surface, mid_skin, el_l, 8)
            pygame.gfxdraw.filled_circle(surface, hand_l[0], hand_l[1], 9, self.skin)

            sh_r = (int(cx + 26), int(shoulder_y))
            el_r = (int(cx + 22), int(shoulder_y - 40))
            hand_r = (int(cx + 5), int(shoulder_y - 78))
            pygame.draw.line(surface, self.skin, sh_r, el_r, 14)
            pygame.draw.line(surface, self.skin, el_r, hand_r, 13)
            pygame.draw.circle(surface, mid_skin, el_r, 8)
            pygame.gfxdraw.filled_circle(surface, hand_r[0], hand_r[1], 9, self.skin)

        elif arm_raised:
            sh_l = (int(cx - 26), int(shoulder_y))
            el_l = (int(cx - 34), int(shoulder_y - 28))
            hand_l = (int(cx - 40), int(shoulder_y - 55))
            pygame.draw.line(surface, self.skin, sh_l, el_l, 14)
            pygame.draw.line(surface, light_skin, el_l, hand_l, 13)
            pygame.draw.circle(surface, mid_skin, el_l, 9)
            pygame.draw.circle(surface, darker_skin, el_l, 9, 2)
            pygame.gfxdraw.filled_circle(surface, hand_l[0], hand_l[1], 10, self.skin)

            sh_r = (int(cx + 26), int(shoulder_y))
            el_r = (int(cx + 34), int(shoulder_y - 28))
            hand_r = (int(cx + 40), int(shoulder_y - 55))
            pygame.draw.line(surface, self.skin, sh_r, el_r, 14)
            pygame.draw.line(surface, mid_skin, el_r, hand_r, 13)
            pygame.draw.circle(surface, mid_skin, el_r, 9)
            pygame.gfxdraw.filled_circle(surface, hand_r[0], hand_r[1], 10, self.skin)

        else:
            if self.is_walking:
                arm_swing = math.sin(self.walk_phase) * 10
            else:
                arm_swing = 0

            # Левая рука
            sh_l = (int(cx - 26), int(shoulder_y))
            el_l = (int(cx - 38), int(shoulder_y + 22 + arm_swing * 0.5))
            hand_l = (int(cx - 42 + arm_swing * 0.3),
                      int(shoulder_y + 48 + arm_swing))
            pygame.draw.line(surface, self.skin, sh_l, el_l, 15)
            pygame.draw.line(surface, mid_skin, el_l, hand_l, 13)
            pygame.draw.circle(surface, mid_skin, el_l, 9)
            pygame.draw.circle(surface, darker_skin, el_l, 9, 2)
            pygame.gfxdraw.filled_circle(surface, hand_l[0], hand_l[1], 10, self.skin)
            pygame.gfxdraw.aacircle(surface, hand_l[0], hand_l[1], 10, darker_skin)

            # Правая рука
            sh_r = (int(cx + 26), int(shoulder_y))
            el_r = (int(cx + 38), int(shoulder_y + 22 - arm_swing * 0.5))
            hand_r = (int(cx + 42 - arm_swing * 0.3),
                      int(shoulder_y + 48 - arm_swing))
            pygame.draw.line(surface, self.skin, sh_r, el_r, 15)
            pygame.draw.line(surface, light_skin, el_r, hand_r, 13)
            pygame.draw.circle(surface, mid_skin, el_r, 9)
            pygame.gfxdraw.filled_circle(surface, hand_r[0], hand_r[1], 10, self.skin)
            pygame.gfxdraw.aacircle(surface, hand_r[0], hand_r[1], 10, darker_skin)

        # ===== ШЕЯ =====
        neck_top = int(self.y - self.h + 4 + crouch_drop + sink)
        neck_bottom = int(self.y - self.h - 10 + crouch_drop + sink)
        pygame.draw.line(surface, darker_skin,
                         (int(cx), neck_bottom), (int(cx), neck_top), 18)
        pygame.draw.ellipse(surface, darker_skin,
                            (int(cx - 10), neck_bottom, 20, 6))

        # ===== ГОЛОВА =====
        head_x, head_y = self.get_head_pos()
        head_y += crouch_drop + sink + breath
        look_dir = -1 if self.is_ai else 1
        happy = self.emotion_timer > 0
        sad = self.emotion_timer < 0
        draw_face(surface, int(head_x), int(head_y), self.head_radius,
                  self.skin, self.hair, eye_dir=look_dir,
                  animated=(self.hit_cooldown > 4),
                  blink=self.is_blinking,
                  happy=happy, sad=sad)


# ========== ИГРА ==========
class Game:
    def __init__(self):
        self.font_big = pygame.font.SysFont("Arial", 72, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 24)
        self.font_label = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_serve = pygame.font.SysFont("Arial", 38, bold=True)
        self.font_cheer = pygame.font.SysFont("Arial", 13, bold=True)

        self.lighting = LightingSystem(start_hour=12.0)
        self.sky_surface = SKY_SURF
        self.sky_rebuild_timer = 0

        self.clouds = [Cloud() for _ in range(7)]
        self.tribune = Tribune()
        self.particles = ParticleSystem()
        self.footprints = FootprintTrail()

        self.palms = [(60, 360, 0.75), (240, 365, 0.9),
                      (1400, 360, 0.85), (1560, 365, 0.7)]

        self.sets_p1 = 0
        self.sets_p2 = 0
        self.current_set = 1
        self.game_over = False
        self.confetti_active = False
        self.tab_flash = 0.0
        self.tab_flash_color = (255, 255, 255)

        self.reset()

    def reset(self):
        self.player = Player(NET_X + 320, (200, 65, 65),
                             skin=(235, 195, 160), hair=(105, 68, 42), is_ai=False,
                             particles=self.particles, footprints=self.footprints)
        self.ai = Player(NET_X - 320, (70, 110, 190),
                         skin=(190, 150, 120), hair=(35, 25, 18), is_ai=True,
                         particles=self.particles, footprints=None)
        self.ball = Ball(self.particles)
        self.score_p1 = 0
        self.score_p2 = 0
        self.message = ""
        self.message_timer = 0
        self.sets_p1 = 0
        self.sets_p2 = 0
        self.current_set = 1
        self.game_over = False
        self.confetti_active = False
        self.tab_flash = 0.0

    def new_set(self):
        if self.score_p1 > self.score_p2:
            self.sets_p1 += 1
        else:
            self.sets_p2 += 1
        if self.sets_p1 >= 2 or self.sets_p2 >= 2:
            self.game_over = True
            self.confetti_active = True
            if self.sets_p1 >= 2:
                self.message = "ЧЕМПИОН!"
                play(SND_WHISTLE, 1.0)
                self.tribune.all_cheer("WINNER!", 4.0)
            else:
                self.message = "ПОРАЖЕНИЕ"
                play(SND_WHISTLE, 0.5)
        else:
            self.current_set += 1
            self.score_p1 = 0
            self.score_p2 = 0
            self.message = f"СЕТ {self.current_set}!"
            self.message_timer = 120
            self.ball.reset()

    def check_point(self):
        if self.game_over or self.message_timer > 60:
            return
        if self.ball.touched_ground:
            if self.ball.x < NET_X:
                self.score_p1 += 1
                self.player.emotion_timer = 1.2
                self.ai.emotion_timer = -1.2
                self.message = "Очко вам!"
                self.tab_flash_color = (80, 255, 80)
            else:
                self.score_p2 += 1
                self.ai.emotion_timer = 1.2
                self.player.emotion_timer = -1.2
                self.message = "Очко ИИ"
                self.tab_flash_color = (255, 80, 80)
            self.message_timer = 90
            self.tab_flash = 0.4
            play(SND_WHISTLE, 1.0)

            if (self.score_p1 >= 15 or self.score_p2 >= 15) and abs(self.score_p1 - self.score_p2) >= 2:
                self.new_set()
            self.ball.reset()
            return

        if self.score_p1 == 14 and self.score_p2 == 14:
            self.message = "МАТЧ-ПОЙНТ!"
            self.message_timer = 60

    def update(self, dt, now):
        self.lighting.update(dt)
        self.sky_rebuild_timer += dt
        if self.sky_rebuild_timer > 0.3:
            self.sky_rebuild_timer = 0
            self.sky_surface = self.lighting.rebuild_sky()

        keys = pygame.key.get_pressed()
        if not self.game_over:
            self.player.update(keys, self.ball, dt, now)
            self.ai.update(keys, self.ball, dt, now)
            self.ball.update(dt)
            self.check_point()
        for c in self.clouds:
            c.update()
        self.tribune.update(dt)
        self.particles.update(dt)
        self.footprints.update(dt)

        if self.message_timer > 0:
            self.message_timer -= 1
        if self.tab_flash > 0:
            self.tab_flash -= dt

        if self.confetti_active and random.random() < 0.4:
            self.particles.spawn(random.randint(0, WIDTH), -20, 1,
                                 'rainbow', speed=50, life=3.5, size=5)

    def draw_sun_rays(self, sun_x, sun_y, sun_color):
        ray_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        num_rays = 20
        for i in range(num_rays):
            angle = (i / num_rays) * math.pi * 2
            length = 700 + random.Random(i).randint(0, 300)
            end_x = sun_x + math.cos(angle) * length
            end_y = sun_y + math.sin(angle) * length
            perp = angle + math.pi / 2
            p1 = (sun_x + math.cos(perp) * 50, sun_y + math.sin(perp) * 50)
            p2 = (sun_x - math.cos(perp) * 50, sun_y - math.sin(perp) * 50)
            alpha = 18 + random.Random(i * 13).randint(0, 15)
            pygame.draw.polygon(ray_surf, (*sun_color, alpha), [p1, p2, (end_x, end_y)])
        screen.blit(ray_surf, (0, 0))

    def draw(self):
        state = self.lighting.get_state()

        screen.blit(self.sky_surface, (0, 0))

        sun_x = int(state['sun_x'] * WIDTH)
        sun_y = int(state['sun_y'] * GROUND_Y)
        sun_color = state['sun_color']

        self.draw_sun_rays(sun_x, sun_y, sun_color)

        for c in self.clouds:
            c.draw(screen)

        glow = pygame.Surface((520, 520), pygame.SRCALPHA)
        for r in range(250, 0, -8):
            alpha = int(22 * (1 - r / 250))
            pygame.draw.circle(glow, (*sun_color, alpha), (260, 260), r)
        screen.blit(glow, (sun_x - 260, sun_y - 260))
        pygame.gfxdraw.filled_circle(screen, sun_x, sun_y, 75, sun_color)
        pygame.gfxdraw.filled_circle(screen, sun_x, sun_y, 62, (255, 255, 245))

        screen.blit(OCEAN_CITY_SURF, (0, 350 - 90))

        for px, py, scale in self.palms:
            scaled = pygame.transform.smoothscale(
                PALM_SPRITE,
                (int(PALM_SPRITE.get_width() * scale),
                 int(PALM_SPRITE.get_height() * scale)))
            screen.blit(scaled, (px - scaled.get_width() // 2,
                                 py - scaled.get_height() + 10))

        dark_factor = int(state['ambient'][3] * 0.8)
        self.tribune.draw(screen, self.font_cheer, dark=dark_factor)

        screen.blit(SAND_SURF, (0, GROUND_Y))
        pygame.draw.line(screen, (200, 220, 230), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

        self.footprints.draw(screen)

        net_left = NET_X - NET_WIDTH // 2
        net_right = NET_X + NET_WIDTH // 2
        for x_pos in (net_left - 4, net_right):
            pygame.draw.rect(screen, (70, 70, 75), (x_pos, NET_TOP, 8, GROUND_Y - NET_TOP))
            pygame.draw.rect(screen, (130, 130, 135), (x_pos, NET_TOP, 3, GROUND_Y - NET_TOP))
        pygame.draw.rect(screen, (240, 240, 240),
                         (net_left - 10, NET_TOP - 8, NET_WIDTH + 20, 12), border_radius=3)
        for y in range(NET_TOP + 5, GROUND_Y, 20):
            pygame.draw.line(screen, (230, 230, 230), (net_left, y), (net_right, y), 1)
        for x in range(net_left, net_right + 1, 8):
            pygame.draw.line(screen, (230, 230, 230), (x, NET_TOP), (x, GROUND_Y), 1)

        self.ai.draw(screen, lighting_state=state)
        self.player.draw(screen, lighting_state=state)
        self.particles.draw(screen)
        self.ball.draw(screen)

        if self.ball.waiting and not self.game_over:
            hint_serve = self.font_serve.render("НАЖМИТЕ ПРОБЕЛ ДЛЯ ПОДАЧИ",
                                                True, (255, 250, 230))
            hx = WIDTH // 2 - hint_serve.get_width() // 2
            hy = 200
            hint_glow = self.font_serve.render("НАЖМИТЕ ПРОБЕЛ ДЛЯ ПОДАЧИ",
                                               True, (255, 220, 90))
            screen.blit(hint_glow, (hx - 2, hy - 2))
            screen.blit(hint_glow, (hx + 2, hy + 2))
            screen.blit(hint_serve, (hx, hy))

        score_str = f"{self.score_p2}  :  {self.score_p1}"
        if self.tab_flash > 0:
            flash_surf = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
            flash_surf.fill((*self.tab_flash_color, int(80 * self.tab_flash / 0.4)))
            screen.blit(flash_surf, (0, 20))
        score_shadow = self.font_big.render(score_str, True, (40, 30, 30))
        score_text = self.font_big.render(score_str, True, (250, 250, 250))
        sx = WIDTH // 2 - score_text.get_width() // 2
        screen.blit(score_shadow, (sx + 4, 34))
        screen.blit(score_text, (sx, 30))

        sets_str = f"Сеты: {self.sets_p2} - {self.sets_p1}  |  Сет {self.current_set}"
        sets_surf = self.font_small.render(sets_str, True, (255, 255, 240))
        sets_shadow = self.font_small.render(sets_str, True, (30, 30, 30))
        sxx = WIDTH // 2 - sets_surf.get_width() // 2
        screen.blit(sets_shadow, (sxx + 2, 113))
        screen.blit(sets_surf, (sxx, 111))

        hour = int(self.lighting.hour)
        minute = int((self.lighting.hour - hour) * 60)
        time_str = f"{hour:02d}:{minute:02d}"
        time_surf = self.font_small.render(time_str, True, (255, 255, 240))
        time_shadow = self.font_small.render(time_str, True, (30, 30, 30))
        screen.blit(time_shadow, (WIDTH - 100, 20))
        screen.blit(time_surf, (WIDTH - 102, 18))

        ai_label = self.font_label.render("ИИ", True, (70, 110, 190))
        p_label = self.font_label.render("ВЫ", True, (200, 65, 65))
        ai_shadow = self.font_label.render("ИИ", True, (30, 30, 30))
        p_shadow = self.font_label.render("ВЫ", True, (30, 30, 30))
        screen.blit(ai_shadow, (NET_X - 278, 53))
        screen.blit(ai_label, (NET_X - 280, 50))
        screen.blit(p_shadow, (NET_X + 222, 53))
        screen.blit(p_label, (NET_X + 220, 50))

        if self.message_timer > 0:
            msg_shadow = self.font_big.render(self.message, True, (30, 20, 20))
            msg_text = self.font_big.render(self.message, True, (250, 220, 90))
            mx = WIDTH // 2 - msg_text.get_width() // 2
            my = HEIGHT // 2 - 60
            screen.blit(msg_shadow, (mx + 4, my + 4))
            screen.blit(msg_text, (mx, my))

        hint = self.font_small.render(
            "← → / A D — движение,   ↑ / W — прыжок,   S — блок,   ПРОБЕЛ — подача,   R — рестарт",
            True, (240, 235, 220))
        screen.blit(hint, (30, HEIGHT - 40))

        ambient = state['ambient']
        if ambient[3] > 0:
            amb_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            amb_surf.fill(ambient)
            screen.blit(amb_surf, (0, 0))

        screen.blit(VIGNETTE, (0, 0))


def main():
    game = Game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        now = pygame.time.get_ticks() / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE and game.ball.waiting and not game.game_over:
                    game.ball.launch()

        game.update(dt, now)
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()