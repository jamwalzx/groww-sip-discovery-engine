"""Views package for Streamlit application."""
from importlib import import_module

def render_overview():
    mod = import_module("app.views.1_overview")
    mod.render()

def render_questions():
    mod = import_module("app.views.2_questions")
    mod.render()

def render_opportunity_matrix():
    mod = import_module("app.views.3_opportunity_matrix")
    mod.render()

def render_segments():
    mod = import_module("app.views.4_segments")
    mod.render()

def render_cohorts():
    mod = import_module("app.views.5_cohorts")
    mod.render()

def render_evals():
    mod = import_module("app.views.6_evals")
    mod.render()

def render_try_it():
    mod = import_module("app.views.7_try_it")
    mod.render()

__all__ = [
    "render_overview",
    "render_questions",
    "render_opportunity_matrix",
    "render_segments",
    "render_cohorts",
    "render_evals",
    "render_try_it"
]

