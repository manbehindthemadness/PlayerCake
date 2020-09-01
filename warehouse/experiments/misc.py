"""
This is for general messing around.
"""


class other_test:
    def __init__(self):
        """
        Another class...
        """
        self.var = 'var'


class test:
    """
    inherit test (cause I forgot how this works exactly).
    """
    def __init__(self):
        self.root = 'pooky'

        class MainView(other_test):
            """
            fooling around
            """
            def __init__(self):
                super(other_test, self).__init__()
                # print(self.root)
                print(self.var)

        MainView()
