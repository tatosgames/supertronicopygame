from dataclasses import dataclass, field


@dataclass(frozen=True)
class Palette:
    name: str
    background: tuple[int, int, int]
    green: tuple[int, int, int]
    glow: tuple[int, int, int]
    dim: tuple[int, int, int]
    red: tuple[int, int, int]
    yellow: tuple[int, int, int]
    cyan: tuple[int, int, int]
    magenta: tuple[int, int, int]
    text: tuple[int, int, int]


PALETTES: tuple[Palette, ...] = (
    Palette(
        name="Classic Tron",
        background=(0, 0, 0),
        green=(0, 255, 40),
        glow=(0, 80, 20),
        dim=(0, 130, 25),
        red=(255, 20, 20),
        yellow=(255, 228, 45),
        cyan=(20, 220, 255),
        magenta=(255, 40, 180),
        text=(160, 255, 170),
    ),
    Palette(
        name="Vector Amber",
        background=(0, 0, 0),
        green=(255, 185, 30),
        glow=(90, 45, 0),
        dim=(150, 90, 10),
        red=(255, 45, 20),
        yellow=(255, 245, 120),
        cyan=(80, 230, 255),
        magenta=(255, 95, 40),
        text=(255, 220, 120),
    ),
    Palette(
        name="Cyan Grid",
        background=(0, 0, 4),
        green=(20, 235, 255),
        glow=(0, 70, 85),
        dim=(0, 120, 135),
        red=(255, 35, 80),
        yellow=(255, 240, 55),
        cyan=(100, 255, 255),
        magenta=(255, 55, 220),
        text=(160, 245, 255),
    ),
    Palette(
        name="Laser Magenta",
        background=(2, 0, 7),
        green=(255, 42, 210),
        glow=(75, 0, 70),
        dim=(135, 18, 120),
        red=(255, 24, 75),
        yellow=(255, 230, 70),
        cyan=(25, 240, 255),
        magenta=(255, 82, 245),
        text=(255, 180, 245),
    ),
    Palette(
        name="Acid Night",
        background=(0, 3, 0),
        green=(170, 255, 20),
        glow=(38, 75, 0),
        dim=(78, 135, 15),
        red=(255, 65, 25),
        yellow=(255, 255, 80),
        cyan=(20, 255, 180),
        magenta=(210, 60, 255),
        text=(215, 255, 145),
    ),
)


@dataclass
class Config:
    width: int = 320
    height: int = 240
    scale: int = 3
    fps: int = 30
    seed: int = 1979
    fullscreen: bool = False

    speed: float = 1.0
    min_speed: float = 0.15
    max_speed: float = 4.0
    speed_step: float = 0.15

    horizon_ratio: float = 0.50
    horizon_min: float = 0.42
    horizon_max: float = 0.58
    focal_ratio: float = 0.74

    scanlines: bool = True
    glow: bool = True
    flicker: bool = True
    show_fps: bool = False
    auto_variation: bool = True
    palette_index: int = 0

    grid_extent_x: float = 22.0
    grid_spacing_x: float = 2.0
    grid_spacing_z: float = 2.0
    grid_z_near: float = 1.2
    grid_z_far: float = 38.0
    grid_scroll_rate: float = 3.8

    mountain_count: int = 46
    city_count: int = 42
    drone_count: int = 7
    star_count: int = 70
    data_column_count: int = 18
    skyline_depth_layers: int = 2

    auto_seed_interval: float = 34.0
    auto_palette_interval: float = 17.0

    palettes: tuple[Palette, ...] = field(default_factory=lambda: PALETTES)

    @property
    def palette(self) -> Palette:
        return self.palettes[self.palette_index % len(self.palettes)]

    @property
    def horizon_y(self) -> int:
        return int(self.height * self.horizon_ratio)

    @property
    def focal_length(self) -> float:
        return self.width * self.focal_ratio
