"""
Module that provides range_t class which offers a simple and compact way of representing number sets.
"""

from copy import deepcopy

class range_t():

    """
    Class offers simple representation of multiple ranges as one object.
    Subranges are represented as two element tuples, where first element is a left boundary and second element is a
    right range boundary. The left one is always included, whereas right is always excluded from the range.

    Attributes
    ----------
    __has : set
        Set of subranges.

    Parameters
    ----------
    initset : set, optional
        Initial set of subranges. Empty set is the default value.
    """

    def __init__(self, initset=set()):

        self.__has = set()

        if not isinstance(initset, set):
            raise TypeError("Expected set of tuples")

        for t in initset:
            if not isinstance(t, tuple) or len(t) != 2 or t[1] <= t[0] or t[1] < 0:
                raise ValueError("Your tuples are wrong :(")

        self.__has = initset
        self.__optimize()

    def __match_l(self, k, _set):

        """
        Method for searching subranges from `_set` that overlap on `k` range.

        Parameters
        ----------
        k : tuple or list or range
            Range for which we search overlapping subranges from `_set`.
        _set : set
            Subranges set.

        Returns
        -------
        matched : set
            Set of subranges from `_set` that overlaps on `k`.
        """

        return {r for r in _set if k[0] in range(*r) or k[1] in range(*r) or (k[0] < r[0] and k[1] >= r[1])}
                                   #k partially or wholly in r               #r is wholly contained by k
    def __optimize(self):

        """
        Merge overlapping or contacting subranges from ``self.__has`` attribute and update it. Called from all methods
        that modify object contents.

        Returns
        -------
        None
            Method does not return. It does internal modifications on ``self.__has`` attribute.
        """

        ret = []

        for (begin, end) in sorted(self.__has):

            if ret and begin <= ret[-1][1] < end: # when current range overlaps with the last one from ret
                ret[-1] = (ret[-1][0], end)
            elif not ret or begin > ret[-1][1]:
                ret.append( (begin, end) )

        self.__has = set(ret)

    def __val_convert(self, val): # maybe I should make a decorator from this.

        """
        Convert input data to a range tuple (start, end).

        Parameters
        ----------
        val : int or tuple or list or range
            Two element indexed object, that represents a range, or integer.

        Returns
        -------
        converted : tuple
            Tuple that represents a range.
        """

        converted = (0, 0) # just in case

        # validate and change val to a tuple.

        if isinstance(val, range) and 0 <= val.start < val.stop and val.step == 1:

            converted = (val.start, val.stop)

        elif (isinstance(val, tuple) or isinstance(val, list)) and 0 <= val[0] < val[1] and len(val) == 2:

            converted = val

        elif isinstance(val, int):
            converted = (val, val+1)

        else:
            raise ValueError("Expected indexed positive value of lenght 2, integer or range of step 1")

        return converted

    def contains(self, val):

        """
        Check if given value or range is present.

        Parameters
        ----------
        val : int or tuple or list or range
            Range or integer being checked.

        Returns
        -------
        retlen : int
            Length of overlapping with `val` subranges.
        """

        (start, end) = self.__val_convert(val) # conversion

        retlen = 0
        for r in self.__has:
            if start < r[1] and end > r[0]:
                retlen += ((end < r[1] and end) or r[1]) - ((start > r[0] and start) or r[0])

        return retlen

    def __contains__(self, val):

        """
        Method which allows ``in`` operator usage.

        Parameters
        ----------
        val : int or tuple or list or range
            Range or integer being checked.

        Returns
        -------
        bool
            ``True`` if **whole** examined range is present in object. Otherwise ``False``.
        """
        
        conv = self.__val_convert(val) # conversion
        return self.contains(val) == conv[1] - conv[0]

    def match(self, val):

        """
        Search for overlapping with `val` subranges. In fact, it is a visible wrapper of hidden ``__match_l``.

        Parameters
        ----------
        val : int or tuple or list or range
            Range or integer being checked.

        Returns
        -------
        set
            Set of overlapping subranges.
        """
        
        conv = self.__val_convert(val) # conversion

        return self.__match_l(conv, self.__has)

    def toset(self):

        """
        Convert object to a set of subranges.

        Returns
        -------
        set
            ``self.__has`` is returned.
        """

        return self.__has

    def __add(self, val):

        """
        Helper method for range addition. It is allowed to add only one compact subrange or ``range_t`` object at once.

        Parameters
        ----------
        val : int or tuple or list or range
            Integer or range to add.

        Returns
        -------
        __has : set
            ``self.__has`` extended by `val`.
        """

        if not isinstance(val, range_t):
            #sanitize it
            val = {self.__val_convert(val)} # convert to a set, coz I like it that way.

        else:
            val = val.toset()

        __has = deepcopy(self.__has) # simply add to a set.
        __has.update(val)

        return __has

    def __add__(self, val):

        """
        ``a + b`` operation support.

        Parameters
        ----------
        val : int or tuple or list or range
            Integer or range to add.

        Returns
        -------
        range_t
            New ``range_t`` object extended by `val`.
        """

        return range_t(self.__add(val))

    def __iadd__(self, val):

        """
        ``a += b`` operation support. The difference from ``+`` is that no new object is created.

        Parameters
        ----------
        val : int or tuple or list or range
            Integer or range to add.

        Returns
        -------
        self : range_t
            No new object is created, the current one is extended by `val` and returned.
        """

        self.__has = self.__add(val)
        self.__optimize()

        return self

    def __sub__(self, val):

        """
        Substracting support.
        
        Parameters
        ----------
        val : int or tuple or list or range
            Integer or range to substract.

        Returns
        -------
        range_t
            New ``range_t`` object bereft of `val`.
        """

        if not isinstance(val, range_t):
            #sanitize it!
            val = {self.__val_convert(val)}
        else:
            val = val.toset()

        __has = deepcopy(self.__has)

        for v in val:
            common = self.__match_l(v, __has) # search for colliding subranges.
            if not common: continue # no collisions - nothing to substract.

            __has.difference_update(common) # we delete collisions, beacause we need to cut them.

            minmax = (min({l[0] for l in common}), max({r[1] for r in common}))

            if minmax[0] < v[0]: __has.add((minmax[0], v[0]))
            if minmax[1] > v[1]: __has.add((v[1], minmax[1]))
            # we get two, one or zero "new" subranges. __optimize is not necessary.

        return range_t(__has)

    def __len__(self):

        """
        Length of object.

        Returns
        -------
        ret : int
            Sum of subranges lengths.
        """

        ret = 0
        for t in self.__has:
            ret += t[1] - t[0]

        return ret

    def __eq__(self, val):

        """
        ``=`` operator support.

        Parameters
        ----------
        val : range_t
            ``range_t`` object for comparison.

        Returns
        -------
        bool
            ``True`` if set of subranges in this object is identical as in `val` object.
        """
        if not isinstance(val, range_t):
            raise ValueError("Expected range_t to compare.")

        return self.__has == val.toset()
