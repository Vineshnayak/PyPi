import pytest
import faultsnap
from faultsnap.serializer import summarize
from faultsnap.core import extract_environment, build_crash_data
from faultsnap.capsule import write_capsule, read_capsule, CapsuleCorruptedError
from faultsnap.mask import is_sensitive_key
from faultsnap.config import config, configure
import sys
import os

class DummyClass:
    def __init__(self):
        self.password = "mysecret"
        self.normal = 123
        
class BrokenRepr:
    def __repr__(self):
        raise ValueError("I am broken")

def test_serializer_circular():
    d = {}
    d['self'] = d
    res = summarize(d)
    assert "CircularReference" in str(res['self'])

def test_serializer_limits():
    l = list(range(200))
    res = summarize(l)
    assert len(res) == 51 # 50 items + 1 truncation message
    assert "<... 150 more items>" in res[-1]

def test_serializer_masking():
    assert is_sensitive_key("API_KEY")
    assert is_sensitive_key("my_password")
    
    d = {"user_password": "123", "public_id": "456"}
    res = summarize(d)
    assert res["user_password"] == "********"
    assert res["public_id"] == "456"

def test_serializer_custom_class():
    obj = DummyClass()
    res = summarize(obj)
    
    # Needs to match the <DummyClass object> key
    class_key = "<DummyClass object>"
    assert class_key in res
    assert res[class_key]["password"] == "********"
    assert res[class_key]["normal"] == 123

def test_serializer_broken_repr():
    from faultsnap.serializer import safe_repr
    obj = BrokenRepr()
    res = safe_repr(obj)
    assert "Exception in repr" in str(res)

def test_build_crash_data():
    try:
        1 / 0
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
        
        assert crash_data["metadata"]["exception_type"] == "ZeroDivisionError"
        assert len(crash_data["frames"]) > 0
        assert "ZeroDivisionError" in crash_data["exception_text"]

def test_capsule_corrupted():
    with open("bad_capsule.faultsnap", "w") as f:
        f.write("not a zip file")
        
    with pytest.raises(CapsuleCorruptedError):
        read_capsule("bad_capsule.faultsnap")
        
    os.remove("bad_capsule.faultsnap")
