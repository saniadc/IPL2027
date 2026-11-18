"""Minimal stand-ins for streamlit and plotly, used ONLY by the page smoke tests.

They run each page's Python with the real data and real calculations, and check that every DataFrame column a
page or chart names exists. They do not render anything: no widget, layout or chart is displayed or checked
visually. A passing smoke test means the code runs, not that the page looks right in a browser."""
import sys
import types


class Anything:
    """Accepts any attribute, call, or context-manager use."""

    def __getattr__(self, name):
        return lambda *a, **k: Anything()

    def __call__(self, *a, **k):
        return Anything()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(())


class StopPage(Exception):
    """Raised by st.stop(); the harness records it."""


def _multiselect(label, options, default=None, **kw):
    return list(default) if default is not None else list(options)


def _radio(label, options, **kw):
    return list(options)[0]


def _selectbox(label, options, index=0, **kw):
    return list(options)[index]  # first option (or the index asked for), as a user starts


def _checkbox(label, value=False, **kw):
    return value


def _slider(label, min_value=0, max_value=None, value=None, **kw):
    return value if value is not None else min_value


class _Column(Anything):
    """st.columns(...) items: they carry the same input widgets as the top-level st module."""
    multiselect = staticmethod(_multiselect)
    radio = staticmethod(_radio)
    slider = staticmethod(_slider)
    selectbox = staticmethod(_selectbox)
    checkbox = staticmethod(_checkbox)


def _columns(spec, **kw):
    n = spec if isinstance(spec, int) else len(spec)
    return [_Column() for _ in range(n)]


def _stop():
    raise StopPage()


def _cache_data(*args, **kw):
    if len(args) == 1 and callable(args[0]) and not kw:
        return args[0]
    return lambda f: f


def _generic_streamlit():
    st = types.ModuleType("streamlit")
    st.columns = _columns
    st.tabs = lambda names, **kw: [_Column() for _ in names]  # one stand-in per tab, so tabs can be unpacked
    st.multiselect = _multiselect
    st.radio = _radio
    st.checkbox = lambda label, value=False, **kw: value
    st.selectbox = lambda label, options, index=0, **kw: list(options)[index]  # first option, as a user starts
    st.slider = _slider
    st.stop = _stop
    st.cache_data = _cache_data
    st.StopPage = StopPage
    st.Page = lambda *a, **k: a[0] if a else k.get("page")
    st.navigation = lambda pages, **k: Anything()
    st.sidebar = Anything()
    st.session_state = {}
    # any other st.xxx(...) is a no-op; module-level __getattr__ must live in the module namespace
    st.__dict__["__getattr__"] = lambda name: (lambda *a, **k: Anything())
    return st


_PX_COLUMN_ARGS = ("x", "y", "color")


def _px_module():
    px = types.ModuleType("plotly.express")

    def checked(name):
        def fn(df, *a, **kw):
            for key in _PX_COLUMN_ARGS:
                v = kw.get(key)
                if isinstance(v, str) and v not in df.columns:
                    raise KeyError(f"plotly.express.{name}: column '{v}' not in frame {list(df.columns)}")
            return Anything()
        return fn

    for name in ("histogram", "bar", "line"):
        setattr(px, name, checked(name))
    return px


def _go_module():
    go = types.ModuleType("plotly.graph_objects")
    go.Figure = lambda *a, **k: Anything()
    for name in ("Scatter", "Bar", "Heatmap"):
        setattr(go, name, lambda *a, **k: Anything())
    return go


def install():
    """Install the stubs in sys.modules. Call before importing any dashboard module."""
    st = _generic_streamlit()
    plotly = types.ModuleType("plotly")
    plotly.express = _px_module()
    plotly.graph_objects = _go_module()
    sys.modules["streamlit"] = st
    sys.modules["plotly"] = plotly
    sys.modules["plotly.express"] = plotly.express
    sys.modules["plotly.graph_objects"] = plotly.graph_objects
    return st
