"""Explicit text-font targets. Icon, symbol and emoji fonts are excluded."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FontTarget:
    filename: str
    family: str
    weight: int
    static_style: str
    registry_name: str

    @property
    def output_filename(self):
        return self.filename[:-4] + '_system_mod.ttf'


SEGOE_TARGETS = (
    FontTarget('segoeuil.ttf', 'Segoe UI', 300, 'Light', 'Segoe UI Light (TrueType)'),
    FontTarget('segoeuisl.ttf', 'Segoe UI', 350, 'Light', 'Segoe UI Semilight (TrueType)'),
    FontTarget('segoeui.ttf', 'Segoe UI', 400, 'Regular', 'Segoe UI (TrueType)'),
    FontTarget('seguisb.ttf', 'Segoe UI', 600, 'SemiBold', 'Segoe UI Semibold (TrueType)'),
    FontTarget('segoeuib.ttf', 'Segoe UI', 700, 'Bold', 'Segoe UI Bold (TrueType)'),
    FontTarget('seguibl.ttf', 'Segoe UI', 900, 'Black', 'Segoe UI Black (TrueType)'),
)
MALGUN_TARGETS = (
    FontTarget('malgunsl.ttf', 'Malgun Gothic', 300, 'Light', 'Malgun Gothic Semilight (TrueType)'),
    FontTarget('malgun.ttf', 'Malgun Gothic', 400, 'Regular', 'Malgun Gothic (TrueType)'),
    FontTarget('malgunbd.ttf', 'Malgun Gothic', 700, 'Bold', 'Malgun Gothic Bold (TrueType)'),
)
ALL_TARGETS = SEGOE_TARGETS + MALGUN_TARGETS
TARGET_BY_FILENAME = {t.filename: t for t in ALL_TARGETS}
