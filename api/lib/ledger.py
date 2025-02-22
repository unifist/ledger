"""
Contains the Models for ledger
"""

import relations

class Base(relations.Model):
    """
    Base class for ledger models
    """

    SOURCE = "ledger"

class Unum(Base):
    """
    Teh single record of this Unum
    """

    id = int
    who = str   # unique way to identify
    meta = dict # any special weird data

class Entity(Base):
    """
    Origin something like Discord, BlueSky and how to handle it
    """

    id = int
    unum_id = int   # The Unum this entity is a part of
    who = str       # unique way to identity this entity
    meta = dict     # any special weird data

relations.OneToMany(Unum, Entity)

class Origin(Base):
    """
    Origin something like Discord, BlueSky and how to handle it
    """

    id = int
    who = str   # unique way to identity this origin, class method in this cases
    meta = dict # any special weird data

class Witness(Base):
    """
    Witness is a specific account we're geting facts from
    """

    id = int
    entity_id = int # Entity this is witnessing
    origin_id = int # Origin this is witnessing
    who = str       # unique way to identity this witness, account id, etc
    meta = dict     # any special weird data

relations.OneToMany(Entity, Witness)
relations.OneToMany(Origin, Witness)

class Fact(Base):
    """
    Fact, a record of what happened according to a witness
    """

    id = int
    witness_id = int    # Witness this is referencing
    who = str           # unique way to identity this witness, event id, etc
    when = int          # Epech time this happened
    what = dict         # playlof of the entire fact from the Origin
    meta = dict         # any special weird data

    INDEX = "when"
    ORDER = "-when"

relations.OneToMany(Witness, Fact)
