"""ContradictPrompt: scoped instruction checking with optional LLM analysis."""
__version__ = '1.0.1'
from .engine import analyze
from .models import Label
__all__=['analyze','Label']
