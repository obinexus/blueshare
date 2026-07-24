# Experimental Python package

`packages/python/blueshare/` contains the two legacy Python demonstrations:

- `blueshare.py` models a cost-sharing session in memory.
- `nsiggi.py` models YES/NO/MAYBE echo behaviour.

They are experimental scripts, not a transport implementation, Bluetooth
service, payment processor, or published package. No packaging metadata exists
yet. Run them from the repository root with:

```powershell
python packages/python/blueshare/blueshare.py
python packages/python/blueshare/nsiggi.py
```

The spatial acceptance model remains separate under `acceptance/`.
