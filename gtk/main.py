"""Main window and primary entrypoint"""
import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from common import __version__, stack


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, title=f"EnderChest {__version__}")

        version_info = Gtk.Label()
        version_info.set_markup(
            "\n".join(
                (
                    f'<span font_desc="mono bold">{k}</span>: {v}'
                    for get_components in (
                        stack.get_stack,
                        stack.get_dependency_versions,
                    )
                    for k, v in get_components().items()
                )
            )
        )
        version_info.set_margin_start(20)
        version_info.set_margin_end(20)
        version_info.set_margin_top(10)
        version_info.set_margin_bottom(20)
        self.set_child(version_info)


def on_activate(app):
    win = MainWindow(application=app)

    win.present()


def main():
    """Run the application"""

    app = Gtk.Application(application_id="io.github.OpenBagTwo.EnderChest.Gtk")

    app.connect("activate", on_activate)

    # Run the application

    app.run(None)


if __name__ == "__main__":
    main()
