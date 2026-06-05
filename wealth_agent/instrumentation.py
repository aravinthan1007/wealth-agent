"""Tracing initialization for Phoenix + ADK instrumentation.

This module follows the snippet in the plan. If the tracing libraries are
not installed in the local environment, `init_tracing()` becomes a noop
and prints a short message instead of crashing the runtime.
"""
try:
    from phoenix.otel import register
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
except Exception:  # pragma: no cover - optional dependencies
    def init_tracing():
        print("Phoenix or OpenInference instrumentation not installed; tracing disabled")
else:
    def init_tracing():
        tp = register(project_name="wealth-agent", auto_instrument=True)
        GoogleADKInstrumentor().instrument(tracer_provider=tp)
