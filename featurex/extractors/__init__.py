from abc import ABCMeta, abstractproperty, abstractmethod


class Extractor(object):

    ''' Base Extractor class. '''

    def __init__(self, name=None):
        if name is None:
            name = self.__class__.__name__
        self.name = name

    __metaclass__ = ABCMeta

    @abstractmethod
    def apply(self):
        pass


class StimExtractor(Extractor):

    ''' Abstract class for stimulus-specific extractors. Defines a target Stim
    class that all subclasses must override. '''
    @abstractproperty
    def target(self):
        pass


class ExtractorCollection(Extractor):

    def __init__(self, extractors=None):
        if extractors is None:
            extractors = []
        self.extractors = extractors

    def apply(self, stim):
        pass


def get_extractor(name):
    ''' Scans list of currently available Extractor classes and returns an
    instantiation of the first one whose name perfectly matches
    (case-insensitive).
    Args:
        name (str): The name of the extractor to retrieve. Case-insensitive;
            e.g., 'stftextractor' or 'CornerDetectionExtractor'. For
            convenience, the 'extractor' suffix can be dropped--i.e., passing
            'stft' is equivalent to passing 'stftextractor'.
    '''

    if not name.lower().endswith('extractor'):
        name += 'extractor'

    # Recursively get all classes that inherit from Extractor
    def get_subclasses(cls):
        subclasses = []
        for sc in cls.__subclasses__():
            subclasses.append(sc)
            subclasses.extend(get_subclasses(sc))
        return subclasses

    extractors = get_subclasses(StimExtractor) + get_subclasses(ExtractorCollection)

    for a in extractors:
        if a.__name__.lower().split('.')[-1] == name.lower():
            return a()

    raise KeyError("No extractor named '%s' found." % name)
