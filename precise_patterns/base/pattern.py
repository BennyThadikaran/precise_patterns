from abc import ABC, abstractmethod
from typing import ClassVar, Dict
from .dtypes import Candle, Pivot


class BasePattern(ABC):
    """
    Base class for all patterns.

    This abstract base class defines the minimal interface required for a
    pattern that can be registered in :class:`Registry`. Subclasses must
    define a non-empty class attribute ``name`` and implement
    :meth:`on_pivot`.

    :param name: Class-level identifier for the pattern subclass.
    :type name: :class:`str` or ``None``

    .. note::
       Subclasses are automatically registered in :class:`Registry`
       upon creation via ``__init_subclass__``.
    """

    name: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs):
        """
        Automatically validates and registers subclasses.

        This method ensures that every subclass of :class:`BasePattern`
        defines a valid ``name`` attribute and that the name is unique
        within the global :class:`Registry`.

        :raises ValueError: If ``name`` is missing, empty, non-string, or
                            duplicates an existing registered pattern.

        .. seealso::
           :class:`Registry`
        """
        super().__init_subclass__(**kwargs)

        if cls.name is None:
            raise ValueError(
                f"`name` attribute must be set on subclass `{cls.__name__}`"
            )

        if not isinstance(cls.name, str) or not cls.name:
            raise ValueError(
                f"`name` attribute of `{cls.__name__}`, must be a non-empty string"
            )

        Registry.register(cls)

    @abstractmethod
    def on_pivot(self, pivot: Pivot, candle: Candle):
        """
        Execute logic when a pivot event occurs.

        This method must be implemented by subclasses to define the behavior
        triggered when a pivot event is detected.

        :raises NotImplementedError: Always, unless implemented by subclass.
        """


class Registry:
    """
    Registry for managing pattern classes.

    This class stores registered subclasses of :class:`BasePattern`.
    """

    _register: Dict[str, type] = {}

    @classmethod
    def register(cls, subcls: type):
        """
        Register a :class:`BasePattern` subclass.

        :param subcls: The subclass to register.
        :type subcls: :class:`type`
        :raises ValueError: If a pattern with the same ``name`` is already registered.

        .. note::
           The subclass must define a unique ``name`` before registration.
        """
        name = subcls.name

        if name in cls._register:
            existing = cls._register[name].__name__
            current = subcls.__name__

            raise ValueError(
                f"Duplicate name assigned for classes `{current}` and `{existing}`"
            )

        cls._register[subcls.name] = subcls

    @classmethod
    def all(cls):
        """
        Return all registered pattern classes.

        :return: A mapping of all registered pattern names to their classes.
        :rtype: :class:`dict` [:class:`str`, :class:`type`]
        """
        return cls._register
