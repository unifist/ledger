#!/usr/bin/env python

import relations
import relations_pymysql

import ledger

source = relations_pymysql.Source("ledger", schema="ledger", connection=False)

migrations = relations.Migrations()

migrations.generate(relations.models(ledger, ledger.Base))
migrations.convert("ledger")
