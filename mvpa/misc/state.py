#emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyMVPA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Class to control and store state information"""

__docformat__ = 'restructuredtext'

import operator, copy
from copy import deepcopy

from mvpa.misc.exceptions import UnknownStateError
from mvpa.misc import warning

if __debug__:
    from mvpa.misc import debug


class StateVariable(object):
    """Descriptor intended to conditionally store the value

    Unfortunately manipulation of enable is not straightforward and
    has to be done via class object, e.g.

      StateVariable.enable(self.__class__.values, self, False)

      if self is an instance of the class which has
    """

    def __init__(self, name=None, enabled=True, doc="State variable"):
        self._values = {}
        self._isenabled_default = enabled
        self._isenabled = {}
        self.__doc__ = doc
        self.name = name
        if __debug__:
            debug("STV",
                  "Initialized new state variable %s " % name + `self`)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if not self.isSet(obj):
            raise UnknownStateError("Unknown yet value of %s for '%s'" % (self.name, `obj`))
        return self._values[obj]

    def __set__(self, obj, val):
        # print "! I am in set"
        # print "Object ", obj, " and it is ", self.isEnabled(obj), ' all are ', self._isenabled
        if self.isEnabled(obj):
            self._values[obj] = val

    def isSet(self, obj):
        return self._values.has_key(obj)

    def isEnabled(self, obj):
        return (self._isenabled.has_key(obj) and self._isenabled[obj]) or \
                   (not self._isenabled.has_key(obj) and self._isenabled_default)

        return self._isenabled[obj]

    def enable(self, obj, val=False):
        if __debug__:
            debug("STV", "%s variable %s for %s" %
                  ({True: 'Enabling', False: 'Disabling'}[val], self.name, `obj`))
        self._isenabled[obj] = val

    def __delete__(self, obj):
        try:
            del self._values[key]
        except:
            raise AttributeError


class StateCollection(object):
    """Container of states class for stateful object.

    Classes inherited from this class gain ability to provide state
    variables, accessed via __getitem__ method (currently implemented
    by inherining `dict` class).
    XXX

    :Groups:
     - `Public Access Functions`: `isKnown`, `isEnabled`, `isActive`
     - `Access Implementors`: `_getListing`, `_getNames`, `_getEnabled`
     - `Mutators`: `__init__`, `enable`, `disable`, `_setEnabled`
     - `R/O Properties`: `listing`, `names`, `items`
     - `R/W Properties`: `enabled`
    """

    def __init__(self, items = {}, owner = None):
        """Initialize the state variables of a derived class

        :Parameters:
          states : dict
            dictionary of states
          enable_states : list
            list of states to enable. If it contains 'all' (in any casing),
            then all states (besides the ones in disable_states) will be enabled
          disable_states : list
            list of states to disable
        """

        self.__owner = owner

        self.__items = items
        """Dictionary to contain registered states as keys and
        values signal either they are enabled
        """

        self.__storedTemporarily = []
        """List to contain sets of enabled states which were enabled temporarily"""

    def __str__(self):
        num = len(self.__items)
        res = "%d states:" % (num)
        for i in xrange(min(num, 4)):
            index = self.__items.keys()[i]
            res += " %s" % index
            if self.isEnabled(index):
                res += '+'              # it is enabled but no value is assigned yet
            if self.isSet(index):
                res += '*'              # so we have the value already

        if len(self.__items) > 4:
            res += "..."
        return res

    #
    # XXX TODO: figure out if there is a way to define proper
    #           __copy__'s for a hierarchy of classes. Probably we had
    #           to define __getinitargs__, etc... read more...
    #
    #def __copy__(self):

    def _copy_states_(self, fromstate, deep=False):
        """Copy known here states from `fromstate` object into current object

        Crafted to overcome a problem mentioned above in the comment
        and is to be called from __copy__ of derived classes

        Probably sooner than later will get proper __getstate__,
        __setstate__
        """
        # Bad check... doesn't generalize well...
        # if not issubclass(fromstate.__class__, self.__class__):
        #     raise ValueError, \
        #           "Class  %s is not subclass of %s, " % \
        #           (fromstate.__class__, self.__class__) + \
        #           "thus not eligible for _copy_states_"
        # TODO: FOR NOW NO TEST! But this beast needs to be fixed...
        operation = { True: copy.deepcopy,
                      False: copy.copy }[deep]

        if isinstance(fromstate, Statefull):
            fromstate = fromstate.states

        self.enabled = fromstate.enabled
        for name in self.names:
            if fromstate.isKnown(name):
                self.__items[name] = operation(fromstate.__items[name])


    def __checkIndex(self, index):
        """Verify that given `index` is a known/registered state.

        :Raise `KeyError`: if given `index` is not known
        """
        if not self.isKnown(index):
            raise KeyError, \
                  "State of %s has no key '%s' registered" \
                  % (self.__class__.__name__, index)


    def isKnown(self, index):
        """Returns `True` if state `index` is known at all"""
        return self.__items.has_key(index)

    def isEnabled(self, index):
        """Returns `True` if state `index` is enabled"""
        self.__checkIndex(index)
        return StateVariable.isEnabled(self.__items[index], self.__owner)


    def isSet(self, index):
        """Returns `True` if state `index` has value set"""
        self.__checkIndex(index)
        return StateVariable.isSet(self.__items[index], self.__owner)


    def get(self, index):
        """Returns the value by index"""
        self.__checkIndex(index)
        return StateVariable.__get__(self.__items[index], self.__owner)

    def set(self, index, value):
        """Sets the value by index"""
        self.__checkIndex(index)
        return StateVariable.__set__(self.__items[index], self.__owner, value)


    def isActive(self, index):
        """Returns `True` if state `index` is known and is enabled"""
        return self.isKnown(index) and self.isEnabled(index)


    def enable(self, index, value=True, missingok=False):
        if isinstance(index, basestring):
            if index.upper() == 'ALL':
                for index_ in self.__items:
                    self.enable(index_, value, missingok=missingok)
            else:
                try:
                    self.__checkIndex(index)
                    StateVariable.enable(self.__items[index], self.__owner, value)
                except:
                    if missingok:
                        return
                    raise
        elif operator.isSequenceType(index):
            for item in index:
                self.enable(item, value, missingok=missingok)
        else:
            raise ValueError, \
                  "Don't know how to handle state variable given by %s" % index

    def disable(self, index):
        """Disable state variable defined by `index` id"""
        self.enable(index, False)


    def _enableTemporarily(self, enable_states, other=None):
        """Temporarily enable needed states for computation

        Enable states which are enabled in `other` and listed in
        `enable _states`. Use `resetEnabledTemporarily` to reset
        to previous state of enabled.

        `other` can be a Statefull object or StateCollection
        """
        self.__storedTemporarily.append(self.enabled)

        if isinstance(other, Statefull):
            other = other.states

        # Lets go one by one enabling only disabled once... but could be as simple as
        # self.enable(enable_states)
        for state in enable_states:
            if not self.isEnabled(state) and \
               ((other is None) or other.isEnabled(state)):
                if __debug__:
                    debug("ST", "Temporarily enabling state %s" % state)
                self.enable(state)

    def _resetEnabledTemporarily(self):
        """Reset to previousely stored set of enabled states"""
        if __debug__:
            debug("ST", "Resetting to previous set of enabled states")
        if len(self.enabled)>0:
            self.enabled = self.__storedTemporarily.pop()
        else:
            raise ValueError("Trying to restore not-stored list of enabled states")


    def _getListing(self):
        """Return a list of registered states along with the documentation"""

        # lets assure consistent litsting order
        items = self.__items.items()
        items.sort()
        return [ "%s%s: %s" % (x[0],
                               {True:"[enabled]",
                                False:""}[self.isEnabled(x[0])],
                               x[1].__doc__) for x in items ]


    def _getEnabled(self):
        """Return list of enabled states"""
        return filter(lambda y: self.isEnabled(y), self.names)


    def _setEnabled(self, indexlist):
        """Given `indexlist` make only those in the list enabled

        It might be handy to store set of enabled states and then to restore
        it later on. It can be easily accomplished now::

        >>> states_enabled = stateful.enabled
        >>> stateful.enabled = ['blah']
        >>> stateful.enabled = states_enabled

        """
        for index in self.__items.keys():
            self.enable(index, index in indexlist)


    def _getNames(self):
        """Return ids for all registered state variables"""
        return self.__items.keys()


    def _getOwner(self):
        return self.__owner

    def _setOwner(self, owner):
        if not isinstance(owner, Statefull):
            raise ValueError, \
                  "Owner of the StateCollection must be Statefull object"
        self.__owner = owner
    

    # Properties
    listing = property(fget=_getListing)
    names = property(fget=_getNames)
    items = property(fget=lambda x:x.__items)
    enabled = property(fget=_getEnabled, fset=_setEnabled)
    owner = property(fget=_getOwner, fset=_setOwner)



class statecollector(type):
    """Intended to collect and compose StateCollection for any child
    class of this metaclass
    """

    def __init__(cls, name, bases, dict):

        if __debug__:
            debug("STCOL", "Collector call for %s.%s, where bases=%s, dict=%s " %
                  (cls, name, bases, dict))

        super(statecollector, cls).__init__(name, bases, dict)

        items = {}
        for name, value in dict.iteritems():
            if isinstance(value, StateVariable):
                items[name] = value
                # and assign name if not yet was set
                if value.name is None:
                    value.name = name

        for base in bases:
            if hasattr(base, "__metaclass__") and \
                   base.__metaclass__ == statecollector:
                # TODO take care about overriding one from super class
                # for state in base.states:
                #    if state[0] =
                newitems = base._states_template.items
                if len(newitems) == 0:
                    continue
                if __debug__:
                    debug("STCOL",
                          "Collect states %s for %s from %s" %
                          (newitems, cls, base))
                items.update(newitems)

        if __debug__:
            debug("STCOL",
                  "Creating StateCollection template %s" % cls)

        statecollection = StateCollection(items, cls) # and give it ownwership of class
        setattr(cls, "_states_template", statecollection)



class Statefull(object):
    """Base class for stateful objects.

    Classes inherited from this class gain ability to provide state
    variables, accessed as simple properties. Access to state variables
    "internals" is done via states property and interface of
    `StateCollection`.

    NB This one is to replace old State base class
    """

    __metaclass__ = statecollector

    def __init__(self,
                 enable_states=[],
                 disable_states=[]):
        self._states = copy.copy(self._states_template)
        self._states.owner = self
        self._states.enable(enable_states, missingok=True)
        self._states.disable(disable_states)
        # bad to have str(self) here since it is a base class and
        # some attributes most probably are not yet set in the original child's __str__
        #if __debug__:
        #    debug("ST", "Statefull.__init__ done for %s" % self)

        if __debug__:
            debug("ST", "Statefull.__init__ was done for %s id %s" % (self.__class__, id(self)))

#    def ____deepcopy__(self, memo=None):
#        #out = super(Statefull, self).__new__(self.__class__)
#        #Statefull.__init__(out)
#        out = deepcopy(self, memo)
#        # copy entries
#        for state in self._states.names:
#            out._states.items[state] = self._states.items[state]
#        return out

    # we want to have __init__ called on copied/pickled objects,
    # so _states.owner is set correctly
    def __getinitargs__(self):
        return {}

    def __getstate__(self):

        out = {}
        for state in self.states.names:
            value = None
            set = self.states.isSet(state)
            if set:
                value = self.states.get(state)
            enabled = self.states.isEnabled(state)
            if self.states.isSet(state):
                out[state] = (set, value, enabled)

        if __debug__:
            debug("ST", "__getstate__ for %s id %s with values %s" % (self.__class__, id(self), out))
        import pydb
        pydb.debugger()
        return out

    def __setstate__(self, values):
        if __debug__:
            debug("ST", "__setstate__ for %s id %s with values %s" % (self.__class__, id(self), values))

        Statefull.__init__(self)
        for state in values.keys():
            (set, value, enabled) = values[state]
            if set:
                self.states.set(state, value)
            self.states.enable(state, enabled)

    @property
    def states(self):
        return self._states

    def __str__(self):
        return "%s with %s" % (self.__class__.__name__, str(self.states))

    def __repr__(self):
        return "<%s>" % Statefull.__str__(self)

