#!/usr/bin/python3

import os
import re
import csv
import datetime

from beancount.ingest import importer
from beancount.core import amount, data, flags, number

from beancount.core.number import D

class MoneyManagerImporter(importer.ImporterProtocol):
    def name(self):
        return("MoneyManagerImporter")

    def identify(self, f):
        return re.match(r"Spend_Manager-\d+-\d+-\d+_\d+-\d+-\d+.csv",
            os.path.basename(f.name))

    def extract(self, f):
        entries = []

        with open(f.name, "r") as f:
            for index, row in enumerate(csv.DictReader(f)):
                # skip the first row as it is header
                if index == 0:
                    continue
                meta = data.new_metadata(f.name, index)
                txn_date = datetime.datetime.strptime(row["Date"], "%m/%d/%Y %H:%M:%S")

                narrations_builder = [row["Income/Expense"], row["Category"], row["Subcategory"]]
                txn_description = ' '.join(narrations_builder)

                txn_builder = data.Transaction(
                    meta = meta,
                    date = txn_date,
                    flag = flags.FLAG_OKAY,
                    payee = None,
                    narration = txn_description,
                    tags = set(),
                    links = set(),
                    postings = [],
                )

                # determine which checking account is used based on currency
                txn_check_account = row["Account"]
                if re.match("Checking MYR", txn_check_account):
                    txn_check_account = "Assets:MYR:CIMB:Checking"
                elif re.match("Checking IDR", txn_check_account):
                    txn_check_account = "Assets:IDR:BCA:Checking"

                txn_builder.postings.append(
                    data.Posting(
                        txn_check_account,
                        None, None, None, None, None
                    )
                )

                # build the account name for income or expense category
                txn_type = "Expenses" if row["Income/Expense"] == "Expense" else "Income"
                account_name_builder = ["Expenses",row["Category"],row["Subcategory"] if row["Subcategory"] != '' else '']
                for i, s in enumerate(account_name_builder):
                    if i == 0:
                        txn_account = s
                    else:
                        if s != '':
                            txn_account += ":" + s

                # determine if transaction is Income or Expense
                # change the numerical sign accordingly:
                #  (+) for expenses
                #  (-) for income
                currency = row["Currency"]
                num_decimal = D(row["Amount"])
                if row["Income/Expense"] == "Income":
                    txn_amount = amount.Amount(-1*num_decimal, currency)
                elif row["Income/Expense"] == "Expense":
                    txn_amount = amount.Amount(num_decimal, currency)
                txn_builder.postings.append(
                    data.Posting(
                        txn_account,
                        txn_amount,
                        None, None, None, None
                    )
                )

                entries.append(txn_builder)
        return entries