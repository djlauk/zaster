#!/usr/bin/env python
#
# This file is part of the `zaster` software package.
# zaster is released under the MIT license (see LICENSE.txt)
#
# Copyright (c) 2015 - 2016 Daniel J. Lauk

import collections
import optparse
import os
import sys
import xml.sax


PROG = os.path.basename(sys.argv[0])


class MissingRequiredAttributeError(Exception):

    def __init__(self, element, attribute):
        Exception.__init__(self, "Element '%s' lacks required attribute '%s'" % (element, attribute))


class DuplicateError(Exception):
    pass


class ZasterHandler(xml.sax.ContentHandler):

    def __init__(self):
        self.accounts = {}
        self.transactions = {}

    def _addAccount(self, attrs):
        if 'id' not in attrs:
            raise MissingRequiredAttributeError('account', 'id')
        id_ = attrs.get('id', None)
        if id_ in self.accounts:
            raise DuplicateError("Account '%(id)s' is defined multiple times" % attrs)
        parent = attrs.get('parent', None)
        if parent:
            if parent not in self.accounts:
                raise KeyError("Account '%(id)s' references unknown parent '%(parent)s'" % attrs)
            parent = self.accounts[parent]
        self.accounts[id_] = Account(id_, parent)

    def _addTransaction(self, attrs):
        for a in ('id', 'date', 'from', 'to', 'amount'):
            if a not in attrs or not attrs[a]:
                raise MissingRequiredAttributeError('transaction', a)
        id_ = attrs['id']
        if id_ in self.transactions:
            raise DuplicateError("Transaction '%(id)s' is defined multiple times" % attrs)
        account_from = self.accounts.get(attrs['from'], None)
        if not account_from:
            raise KeyError("Transaction '%(id)s' references unknown account '%(from)s' in 'from' field" % attrs)
        account_to = self.accounts.get(attrs['to'], None)
        if not account_to:
            raise KeyError("Transaction '%(id)s' references unknown account '%(to)s' in 'to' field" % attrs)
        try:
            amount = float(attrs['amount'])
        except ValueError:
            raise ValueError("Transaction '%(id)s' specifies bad value for field 'amount': %(amount)s" % attrs)
        txn = Transaction(id_, attrs.get('date'), amount, account_from, account_to, attrs.get('comment'))
        self.transactions[txn.id] = txn
        account_from.register_transaction(txn)
        account_to.register_transaction(txn)

    def startElement(self, name, attrs):
        if name == "account":
            self._addAccount(attrs)
        elif name == "transaction":
            self._addTransaction(attrs)
        else:
            pass


Transaction = collections.namedtuple('Transaction', ('id', 'date', 'amount', 'account_from', 'account_to', 'comment'))


class Account(object):
    """
    An account
    """

    def __init__(self, id_, parent=None, transactions=None):
        self.id = id_
        self.parent = parent
        self.balance = 0.0
        self.total_in = 0.0
        self.total_out = 0.0
        self.transactions = []
        for t in transactions or []:
            self.register_transaction(t)

    def __add__(self, other):
        self.balance += other
        if other > 0:
            self.total_in += other
        else:
            self.total_out += -other
        if self.parent:
            self.parent += other
        return self

    def __sub__(self, other):
        return self.__add__(-other)

    def __getitem__(self, key):
        if key == 'balance':
            return self.balance
        if key == 'id':
            return self.id
        if key == 'parent':
            return self.parent
        if key == 'total_in':
            return self.total_in
        if key == 'total_out':
            return self.total_out
        if key == 'transactions':
            return self.transactions
        raise KeyError("No such field: %s" % key)

    def __str__(self):
        return "%s (%.2f)" % (self.name, self.balance)

    def register_transaction(self, txn):
        if self is txn.account_from:
            self -= txn.amount
        elif self is txn.account_to:
            self += txn.amount
        else:
            raise ValueError("Account is not part of this transaction")
        self.transactions.append(txn)


def parse_xml_string(s):
    handler = ZasterHandler()
    parser = xml.sax.parseString(s, handler)
    return (handler.accounts, handler.transactions)


def parse_xml_file(file_name):
    with open(file_name, 'r') as f:
        return parse_xml_string(f.read())


def command_balance(file_name):
    accounts, _ = parse_xml_file(file_name)
    ids = list(accounts.keys())
    ids.sort()
    sys.stdout.write("ACCOUNT;TOTAL OUT;TOTAL IN;BALANCE\n")
    for id_ in ids:
        sys.stdout.write("%(id)s;%(total_out).2f;%(total_in).2f;%(balance).2f\n" % accounts[id_])
    return 0


def command_statement(file_name, account):
    accounts, _ = parse_xml_file(file_name)
    if account not in accounts:
        raise KeyError('Account unknown: %s' % account)
    sys.stdout.write("Statement for account: %s\n" % account)
    sys.stdout.write("TRANSACTION;DATE;OUT;IN;BALANCE;COMMENT\n")
    balance = 0.0
    for t in accounts[account].transactions:
        amount_in = 0.0
        amount_out = 0.0
        if accounts[account] is t.account_from:
            amount_out = t.amount
            balance -= amount_out
        if accounts[account] is t.account_to:
            amount_in = t.amount
            balance += amount_in
        sys.stdout.write("(%s);%s;%.2f;%.2f;%.2f;%s\n" % (t.id, t.date, amount_out, amount_in, balance, t.comment))
    return 0


def command_help(*args):
    sys.stdout.write('''Usage: %(prog)s COMMAND [ARGUMENTS]

Possible commands are:

  balance       - Print the summary balance for each account
  help          - Print these instructions
  statement     - Print a detailed statement for an account
''' % {
    'prog': PROG
})
    return 0


def find_command(name):
    if name == 'balance':
        return command_balance
    if name == 'statement':
        return command_statement
    if name in ('-h', '--help', 'help'):
        return command_help
    return None


def main(args):
    if len(args) < 1:
        raise RuntimeError('No command given')
    command = find_command(args[0])
    if command is None:
        raise RuntimeError('Unknown command: %s' % args[0])
    if command is command_help:
        return command()
    args = args[1:]
    if len(args) < 1:
        raise RuntimeError('No file name given')
    return command(*args)


def __debug_enabled():
    return os.environ.get('ZASTER_DEBUG', '').lower() in ('1', 'yes', 'true', 'on')


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        if __debug_enabled():
            raise e
        sys.stderr.write("%s: %s\n" % (PROG, str(e)))
        sys.exit(1)
