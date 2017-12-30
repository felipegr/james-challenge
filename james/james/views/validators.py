import colander


class NumberGreaterThanZero(object):
    def __call__(self, node, value):
        if value <= 0:
            raise colander.Invalid(node, "Value must be greater than zero")
