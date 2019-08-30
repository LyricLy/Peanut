import json


class Data:
    def __init__(self, fn, **kwargs):
        self._fn = fn
        self._dict = kwargs
        self.load()

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            self._dict[key] = value
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key):
        return self._dict[key]

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("keys must be str")
        self._dict[key] = value

    def save(self):
        with open(self._fn, "w") as f:
            json.dump(self._dict, f)

    def load(self):
        try:
            with open(self._fn) as f:
                self._dict = json.load(f)
        except FileNotFoundError:
            self.save()
