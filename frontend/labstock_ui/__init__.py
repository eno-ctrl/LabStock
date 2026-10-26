import flet as ft

# Ensure Flet 1.0+ compatibility for Control.page setter and unparented controls
_orig_page_fget = ft.Control.page.fget


def _control_page_getter(self):
    p = getattr(self, "_app_page", None)
    if p is not None:
        return p
    try:
        return _orig_page_fget(self)
    except Exception:
        return getattr(self, "_app_page", None)


def _control_page_setter(self, value):
    self._app_page = value


ft.Control.page = property(_control_page_getter, _control_page_setter)


# Backward-compatibility wrappers for Flet 0.x button constructors accepting `text`
def _wrap_button_init(orig_init):
    def wrapper(self, *args, **kwargs):
        if "text" in kwargs and "content" not in kwargs:
            kwargs["content"] = kwargs.pop("text")
        return orig_init(self, *args, **kwargs)

    return wrapper


for _btn_cls in [ft.FilledButton, ft.TextButton, ft.OutlinedButton]:
    _btn_cls.__init__ = _wrap_button_init(_btn_cls.__init__)


# Backward-compatibility wrapper for Dropdown accepting `on_change` (renamed to `on_select` in Flet 1.0)
def _wrap_dropdown_init(orig_init):
    def wrapper(self, *args, **kwargs):
        if "on_change" in kwargs and "on_select" not in kwargs:
            kwargs["on_select"] = kwargs.pop("on_change")
        return orig_init(self, *args, **kwargs)

    return wrapper


ft.Dropdown.__init__ = _wrap_dropdown_init(ft.Dropdown.__init__)

# Compatibility aliases for Flet 0.x -> 1.0+
if not hasattr(ft, "ElevatedButton"):
    ft.ElevatedButton = ft.FilledButton
if not hasattr(ft, "app"):
    ft.app = ft.run
