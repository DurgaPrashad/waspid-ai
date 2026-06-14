# Waspid AI OS
"""Waspid — enterprise AI workforce operating system.

The agent runtime is provided by the upstream MIT-licensed SDK
distributions (``openhands-sdk``, ``openhands-tools``,
``openhands-agent-server``, ``openhands-aci``), which install into the
``openhands.*`` namespace. The alias finder below exposes those modules
under ``waspid.*`` (e.g. ``waspid.sdk`` -> ``openhands.sdk``) while
sharing the *same* module objects, so isinstance checks and module-level
state remain consistent across both names.
"""

import importlib
import importlib.abc
import importlib.util
import os
import sys

# The upstream SDK prints its own startup banner; keep Waspid's console
# output Waspid-branded. Users can re-enable it explicitly if they want.
os.environ.setdefault('OPENHANDS_SUPPRESS_BANNER', '1')

# Subpackages provided by the upstream SDK distributions rather than by
# this repository. ``waspid.<name>`` resolves to ``openhands.<name>``.
_UPSTREAM_SUBPACKAGES = ('sdk', 'tools', 'agent_server', 'workspace')


class _AliasLoader(importlib.abc.Loader):
    """Loader that hands back an already-imported module unchanged."""

    def __init__(self, module):
        self._module = module

    def create_module(self, spec):
        return self._module

    def exec_module(self, module):
        pass


def _add_waspid_symbol_aliases(module):
    """Expose Waspid-named aliases for upstream OpenHands-named symbols.

    Lets Waspid code import e.g. ``WaspidModel`` or ``VERIFIED_WASPID_MODELS``
    from upstream modules whose public names contain "OpenHands". The alias
    resolves to the same object, so isinstance/identity semantics hold.
    Installed as a module ``__getattr__`` (PEP 562) because upstream modules
    may export their public names lazily.
    """
    if module.__dict__.get('_waspid_alias_getattr'):
        return
    orig_getattr = module.__dict__.get('__getattr__')

    def __getattr__(name):
        if 'Waspid' in name:
            upstream = name.replace('Waspid', 'OpenHands')
        elif 'WASPID' in name:
            upstream = name.replace('WASPID', 'OPENHANDS')
        else:
            upstream = None
        if upstream is not None:
            try:
                return getattr(module, upstream)
            except AttributeError:
                pass
        if orig_getattr is not None:
            return orig_getattr(name)
        raise AttributeError(
            f'module {module.__name__!r} has no attribute {name!r}'
        )

    module.__dict__['__getattr__'] = __getattr__
    module.__dict__['_waspid_alias_getattr'] = True


class _UpstreamAliasFinder(importlib.abc.MetaPathFinder):
    """Resolve waspid.<upstream> imports to the openhands.<upstream> modules."""

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith('waspid.'):
            return None
        parts = fullname.split('.')
        if parts[1] not in _UPSTREAM_SUBPACKAGES:
            return None
        upstream_name = 'openhands.' + '.'.join(parts[1:])
        try:
            module = importlib.import_module(upstream_name)
        except ImportError:
            return None
        _add_waspid_symbol_aliases(module)
        spec = importlib.util.spec_from_loader(fullname, _AliasLoader(module))
        # Mark alias packages as packages so `from waspid.sdk.x import y` works.
        if hasattr(module, '__path__'):
            spec.submodule_search_locations = list(module.__path__)
        return spec


def _patch_llm_waspid_prefix(llm_module):
    """Teach the upstream LLM validator the ``waspid/`` provider prefix.

    Upstream rewrites ``openhands/X`` to ``litellm_proxy/X`` and fills in the
    managed-proxy base URL inside the LLM before-validator. Waspid model
    strings use the ``waspid/`` prefix, so normalize it to the upstream
    prefix first and let the original validator do the rest. The wrap happens
    immediately after the module executes — before any dependent pydantic
    model (e.g. AgentSettings) embeds the LLM schema — so every consumer
    sees the patched behaviour.
    """
    llm_cls = llm_module.LLM
    if getattr(llm_cls, '_waspid_prefix_patched', False):
        return
    llm_cls._waspid_prefix_patched = True
    decorators = llm_cls.__pydantic_decorators__.model_validators
    for decorator in decorators.values():
        if decorator.info.mode != 'before':
            continue
        orig = decorator.func

        def _coerce_waspid_prefix(data, _orig=orig):
            if isinstance(data, dict):
                model_val = data.get('model')
                if isinstance(model_val, str) and model_val.startswith('waspid/'):
                    data = {
                        **data,
                        'model': 'openhands/' + model_val.removeprefix('waspid/'),
                    }
            return _orig(data)

        decorator.func = _coerce_waspid_prefix
    llm_cls.model_rebuild(force=True)


class _LLMPatchLoader(importlib.abc.Loader):
    """Run the waspid-prefix patch right after the SDK llm module executes."""

    def __init__(self, inner):
        self._inner = inner

    def create_module(self, spec):
        return self._inner.create_module(spec)

    def exec_module(self, module):
        self._inner.exec_module(module)
        _patch_llm_waspid_prefix(module)


class _LLMPatchFinder(importlib.abc.MetaPathFinder):
    _resolving = False

    def find_spec(self, fullname, path=None, target=None):
        if fullname != 'openhands.sdk.llm.llm' or _LLMPatchFinder._resolving:
            return None
        _LLMPatchFinder._resolving = True
        try:
            spec = importlib.util.find_spec(fullname)
        finally:
            _LLMPatchFinder._resolving = False
        if spec is None or spec.loader is None:
            return None
        spec.loader = _LLMPatchLoader(spec.loader)
        return spec


if not any(isinstance(f, _UpstreamAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _UpstreamAliasFinder())
    sys.meta_path.insert(0, _LLMPatchFinder())

# If the SDK was imported before waspid, the loader hook above never fired;
# patch in place. Dependent schemas built in between keep working because the
# wrapped validator is also re-registered on the (rebuilt) LLM schema used by
# anything constructed afterwards.
if 'openhands.sdk.llm.llm' in sys.modules:
    _patch_llm_waspid_prefix(sys.modules['openhands.sdk.llm.llm'])

from waspid.app_server.version import __version__, get_version  # noqa: E402

__all__ = ['__version__', 'get_version']
