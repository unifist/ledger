"""
Contains the Models for ledger
"""

import relations

class Base(relations.Model):
    """
    Base class for ledger models
    """

    SOURCE = "ledger"


class Origin(Base):
    """
    Origin model what can produces facts
    """

    id = int
    name = str
    description = str
    meta = dict


class Fact(Base):
    """
    Fact, a record of what happened
    """

    id = int
    origin_id = int
    when = int
    meta = dict

relations.OneToMany(Origin, Fact)
