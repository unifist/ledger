#!/usr/bin/env python

import json

import micro_logger

import relations
import relations_pymysql

logger = micro_logger.getLogger("ledger-api")

with open("/opt/service/secret/mysql.json", "r") as mysql_file:
    source = relations_pymysql.Source("ledger", schema="ledger", autocommit=True, **json.loads(mysql_file.read()))

cursor = source.connection.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS `ledger`")

migrations = relations.Migrations()

logger.info("migrations", extra={"migrated": migrations.apply("ledger")})
