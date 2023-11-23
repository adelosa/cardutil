__version__ = '0.6.4'


class CardutilError(Exception):

    binary_context_data = None
    record_number = None
    ex = None

    def __init__(self, *args, **kwargs):
        super(CardutilError, self).__init__(*args)
        if kwargs.get('record_number'):
            self.record_number = kwargs['record_number']
        if kwargs.get('binary_context_data'):
            self.binary_context_data = kwargs['binary_context_data']
        if kwargs.get('original_exception'):
            self.ex = kwargs['original_exception']
