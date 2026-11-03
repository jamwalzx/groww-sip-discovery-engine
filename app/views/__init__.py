"""Views package for Streamlit application with hot-reloading support."""
import sys
from importlib import import_module, reload

def _load_view(module_name: str):
    """Loads or reloads a view module to ensure immediate hot-reloading on changes."""
    if module_name in sys.modules:
        try:
            return reload(sys.modules[module_name])
        except Exception:
            return import_module(module_name)
    return import_module(module_name)

def render_overview():
    mod = _load_view("app.views.1_overview")
    mod.render()

def render_questions():
    mod = _load_view("app.views.2_questions")
    mod.render()

def render_opportunity_matrix():
    mod = _load_view("app.views.3_opportunity_matrix")
    mod.render()

def render_segments():
    mod = _load_view("app.views.4_segments")
    mod.render()

def render_cohorts():
    mod = _load_view("app.views.5_cohorts")
    mod.render()

def render_evals():
    mod = _load_view("app.views.6_evals")
    mod.render()

def render_try_it():
    mod = _load_view("app.views.7_try_it")
    mod.render()
