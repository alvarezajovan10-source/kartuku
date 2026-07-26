from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

# Gradasi netral sebagai pengganti foto asli di halaman preview.
GRADIENTS = [
    ((243, 217, 196), (231, 185, 194)),
    ((247, 215, 116), (231, 142, 160)),
    ((127, 176, 214), (158, 27, 50)),
    ((250, 242, 228), (201, 162, 76)),
]
SIZE = 700


class Command(BaseCommand):
    help = (
        "Buat foto contoh di static/img/sample/ untuk halaman preview template. "
        "Ganti file-file ini dengan foto asli kapan saja."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Timpa file yang sudah ada (default: file yang ada dibiarkan).",
        )

    def handle(self, *args, **options):
        out_dir = Path(settings.BASE_DIR) / "static" / "img" / "sample"
        out_dir.mkdir(parents=True, exist_ok=True)

        for index, (start, end) in enumerate(GRADIENTS, start=1):
            path = out_dir / f"{index}.jpg"
            if path.exists() and not options["force"]:
                self.stdout.write(f"{path.name} sudah ada, dilewati")
                continue

            image = Image.new("RGB", (SIZE, SIZE))
            draw = ImageDraw.Draw(image)
            for y in range(SIZE):
                ratio = y / (SIZE - 1)
                draw.line(
                    [(0, y), (SIZE, y)],
                    fill=tuple(
                        int(start[c] + (end[c] - start[c]) * ratio) for c in range(3)
                    ),
                )
            draw.text((24, SIZE - 40), "FOTO CONTOH", fill=(255, 255, 255))
            image.save(path, "JPEG", quality=85)
            self.stdout.write(f"{path.name} dibuat")
