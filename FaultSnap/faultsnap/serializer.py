import sys
import types
import io
import socket
import sqlite3
import dataclasses
from faultsnap.mask import is_sensitive_key, mask_value
from faultsnap.config import config

class MaxDepthExceeded:
    def __repr__(self):
        return "<MaxDepthExceeded>"

class UnserializableObject:
    def __init__(self, repr_str):
        self.repr_str = repr_str

    def __repr__(self):
        return self.repr_str

def safe_repr(obj):
    try:
        r = repr(obj)
        if len(r) > config.max_string_len:
            return r[:config.max_string_len] + f"... <truncated {len(r)-config.max_string_len} more chars>"
        return r
    except Exception as e:
        return f"<Exception in repr: {type(e).__name__}>"

def summarize_object(obj, seen_ids, state, depth=0):
    if state["total_items"] >= config.max_total_items:
        return "<Truncated: Global size limit reached>"
        
    state["total_items"] += 1

    if obj is None:
        return None
    if isinstance(obj, (int, float, bool)):
        return obj

    obj_id = id(obj)
    if obj_id in seen_ids:
        return f"<CircularReference to {type(obj).__name__} id={obj_id}>"

    if depth >= config.max_depth:
        return "<MaxDepthExceeded>"

    seen_ids.add(obj_id)

    try:
        if isinstance(obj, str):
            if len(obj) > config.max_string_len:
                return obj[:config.max_string_len] + f"... <truncated {len(obj)-config.max_string_len} more chars>"
            return obj

        if isinstance(obj, bytes):
            if len(obj) > config.max_string_len:
                return repr(obj[:config.max_string_len]) + f"... <truncated {len(obj)-config.max_string_len} more bytes>"
            return repr(obj)

        if isinstance(obj, list) or isinstance(obj, tuple):
            is_tuple = isinstance(obj, tuple)
            res = []
            for i, item in enumerate(obj):
                if i >= config.max_items:
                    res.append(f"<... {len(obj) - config.max_items} more items>")
                    break
                res.append(summarize_object(item, seen_ids, state, depth + 1))
            return res if not is_tuple else tuple(res)

        if isinstance(obj, set) or isinstance(obj, frozenset):
            res = []
            for i, item in enumerate(list(obj)):
                if i >= config.max_items:
                    res.append(f"<... {len(obj) - config.max_items} more items>")
                    break
                res.append(summarize_object(item, seen_ids, state, depth + 1))
            return f"<{'frozenset' if isinstance(obj, frozenset) else 'set'} {res}>"

        if isinstance(obj, dict):
            res = {}
            for i, (k, v) in enumerate(obj.items()):
                if i >= config.max_items:
                    res[f"<... {len(obj) - config.max_items} more keys>"] = ""
                    break
                
                # Check for secrets based on key
                k_str = str(k)
                if is_sensitive_key(k_str):
                    res[k_str] = mask_value(None)
                else:
                    res[k_str] = summarize_object(v, seen_ids, state, depth + 1)
            return res

        # Dataclasses
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            res = {}
            for i, f in enumerate(dataclasses.fields(obj)):
                if i >= config.max_items:
                    res[f"<... {len(dataclasses.fields(obj)) - config.max_items} more fields>"] = ""
                    break
                k_str = f.name
                if is_sensitive_key(k_str):
                    res[k_str] = mask_value(None)
                else:
                    try:
                        v = getattr(obj, k_str)
                        res[k_str] = summarize_object(v, seen_ids, state, depth + 1)
                    except Exception:
                        res[k_str] = "<Exception accessing attribute>"
            return {f"<{type(obj).__name__} dataclass>": res}

        # IO handles, sockets, DB connections
        if isinstance(obj, io.IOBase):
            try:
                name = getattr(obj, 'name', 'unknown')
                mode = getattr(obj, 'mode', 'unknown')
                return f"<File handle name={name} mode={mode}>"
            except Exception:
                return "<File handle>"

        if isinstance(obj, socket.socket):
            try:
                fd = obj.fileno()
                fam = obj.family.name
                typ = obj.type.name
                return f"<Socket fd={fd} family={fam} type={typ}>"
            except Exception:
                return "<Socket>"
                
        if isinstance(obj, sqlite3.Connection):
            return "<Database Connection sqlite3>"

        # Duck-typing for Numpy/Pandas/Tensors
        if hasattr(obj, "shape") and hasattr(obj, "dtype"):
            try:
                shape = getattr(obj, "shape")
                dtype = getattr(obj, "dtype")
                return f"<{type(obj).__name__} shape={shape} dtype={dtype}>"
            except Exception:
                pass

        if isinstance(obj, types.FunctionType):
            return f"<function {obj.__name__}>"

        if isinstance(obj, type):
            return f"<class {obj.__name__}>"

        # Attempt to serialize custom classes with __dict__ or __slots__
        if hasattr(obj, "__dict__"):
            res = {}
            try:
                attrs = list(obj.__dict__.items())
                for i, (k, v) in enumerate(attrs):
                    if i >= config.max_items:
                        res[f"<... {len(attrs) - config.max_items} more attributes>"] = ""
                        break
                    k_str = str(k)
                    if is_sensitive_key(k_str):
                        res[k_str] = mask_value(None)
                    else:
                        res[k_str] = summarize_object(v, seen_ids, state, depth + 1)
                return {f"<{type(obj).__name__} object>": res}
            except Exception:
                pass
                
        if hasattr(obj, "__slots__"):
            res = {}
            try:
                slots = obj.__slots__
                if isinstance(slots, str):
                    slots = [slots]
                for i, k in enumerate(slots):
                    if i >= config.max_items:
                        res[f"<... {len(slots) - config.max_items} more attributes>"] = ""
                        break
                    k_str = str(k)
                    if is_sensitive_key(k_str):
                        res[k_str] = mask_value(None)
                    else:
                        try:
                            v = getattr(obj, k_str)
                            res[k_str] = summarize_object(v, seen_ids, state, depth + 1)
                        except AttributeError:
                            pass
                return {f"<{type(obj).__name__} object (slots)>": res}
            except Exception:
                pass

        # Fallback to safe repr for custom classes, objects, etc.
        return safe_repr(obj)
    except Exception as general_err:
        return f"<Exception in serializer: {general_err}>"
    finally:
        # We don't remove obj_id from seen_ids because we don't want to revisit
        # the same object multiple times in the same tree (avoids exponential explosion)
        pass

def summarize(obj):
    """Entry point for smart object summarization."""
    state = {"total_items": 0}
    return summarize_object(obj, seen_ids=set(), state=state, depth=0)
