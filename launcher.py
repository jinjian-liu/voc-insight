import os
import socket
import sys
import threading
import webbrowser

from PIL import Image, ImageDraw
import pystray
import uvicorn

from app.main import app


APP_TITLE = "VoC Insight"


def available_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def run_headless(port: int) -> None:
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def tray_image() -> Image.Image:
    image = Image.new("RGB", (64, 64), "#123c31")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((7, 7, 57, 57), radius=13, fill="#6bd39c")
    draw.line((20, 21, 32, 47, 44, 21), fill="#123c31", width=7, joint="curve")
    return image


def run_desktop(port: int) -> None:
    url = f"http://127.0.0.1:{port}"
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    def open_workspace(_: pystray.Icon, __: pystray.MenuItem) -> None:
        webbrowser.open(url)

    def shutdown(icon: pystray.Icon, _: pystray.MenuItem) -> None:
        server.should_exit = True
        icon.stop()

    icon = pystray.Icon(
        "voc-insight",
        tray_image(),
        APP_TITLE,
        menu=pystray.Menu(
            pystray.MenuItem("打开工作台", open_workspace, default=True),
            pystray.MenuItem("退出", shutdown),
        ),
    )
    if os.getenv("VOC_NO_BROWSER") != "1":
        threading.Timer(1.1, lambda: webbrowser.open(url)).start()
    icon.run()


def main() -> None:
    if "--health-check" in sys.argv:
        return
    port = int(os.getenv("VOC_PORT", available_port()))
    if os.getenv("VOC_HEADLESS") == "1":
        run_headless(port)
    else:
        run_desktop(port)


if __name__ == "__main__":
    main()
