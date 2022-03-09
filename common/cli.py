from argparse import (
    Action,
    ArgumentParser,
)


class CustomActionSearch(Action):
    def __init__(self, *args, **kwargs):
        super(CustomActionSearch, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

        if len(values) > 3:
            ArgumentParser().error(
                message="argument {0}: {1} arguments provided, expected max 3".format(
                    option_string, len(values)))
        elif len(values) < 2:
            ArgumentParser().error(
                message="argument {0}: {1} arguments provided, expected min 2".format(
                    option_string, len(values)))

        try:
            try:
                if int(values[2]) >= 0:
                    setattr(namespace, self.dest, values)
                else:
                    ArgumentParser().error(
                        message="argument {0}: invalid choice: '{1}', choose value >= 0".format(
                            option_string, values[2]))
            except ValueError:
                ArgumentParser().error(
                    message="argument {0}: invalid type: '{1}', choose an integer value".format(
                        option_string, values[2]))

        except IndexError:
            pass


class CustomActionScrape(Action):
    def __init__(self, options, *args, **kwargs):
        self.options = options
        super(CustomActionScrape, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

        if len(values) > 3:
            ArgumentParser().error(
                message="argument {0}: {1} arguments provided, expected max {2}".format(
                    option_string, len(values), 3))

        try:
            if int(values[0]) >= 0:
                setattr(namespace, self.dest, values)
            else:
                ArgumentParser().error(
                    message="argument {0}: invalid choice: '{1}', choose value >= 0".format(
                        option_string, values[0]))

            if values[1] in self.options:
                setattr(namespace, self.dest, values)
            else:
                ArgumentParser().error(
                    message="argument {0}: invalid choice: '{1}', choose from {2}".format(
                        option_string, values[1], self.options))

            if int(values[2]) >= 0:
                setattr(namespace, self.dest, values)
            else:
                ArgumentParser().error(
                    message="argument {0}: invalid choice: '{1}', choose value >= 0".format(
                        option_string, values[2]))

        except IndexError:
            pass
