#!/usr/bin/env python
#
# This file is part of the `zaster` software package.
# zaster is released under the MIT license (see LICENSE.txt)
#
# Copyright (c) 2015 - 2016 Daniel J. Lauk


import zaster


def check_account(account, expected_balance, expected_total_in, expected_total_out):
    assert abs(account.balance - expected_balance) < 1e-6
    assert abs(account.total_in - expected_total_in) < 1e-6
    assert abs(account.total_out - expected_total_out) < 1e-6


def test_parse_xml_string():
    input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="Account A" />
  <account name="Account B" />
  <account name="Account C" />
</accounts>
<transactions>
  <transaction id="1" date="2015-03-22" amount="10.00" from="Account A" to="Account B" />
  <transaction id="2" date="2015-03-22" amount="5.00" from="Account A" to="Account C" />
  <transaction id="3" date="2015-03-22" amount="3.50" from="Account B" to="Account C" />
</transactions>
</zaster>
'''
    accounts, transactions = zaster.parse_xml_string(input)
    assert len(accounts) == 3
    assert len(transactions) == 3
    assert len(accounts["Account A"].transactions) == 2
    assert len(accounts["Account B"].transactions) == 2
    assert len(accounts["Account C"].transactions) == 2
    check_account(accounts["Account A"], -15, 0, 15)
    check_account(accounts["Account B"], 6.50, 10, 3.50)
    check_account(accounts["Account C"], 8.50, 8.50, 0)


def test_balance_of_parents():
    input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="A1" parent="A" />
  <account name="A11" parent="A1" />
  <account name="A12" parent="A1" />
  <account name="A2" parent="A" />
  <account name="A21" parent="A2" />
  <account name="A22" parent="A2" />
  <account name="B" />
  <account name="B1" parent="B" />
  <account name="B11" parent="B1" />
  <account name="B12" parent="B1" />
</accounts>
<transactions>
  <transaction id="1" date="2016-02-16" amount="10.00" from="A11" to="B11" comment="test" />
  <transaction id="2" date="2016-02-16" amount="20.00" from="A12" to="B12" comment="test" />
  <transaction id="3" date="2016-02-16" amount="30.00" from="A21" to="B11" comment="test" />
  <transaction id="4" date="2016-02-16" amount="40.00" from="A22" to="B12" comment="test" />
</transactions>
</zaster>
'''
    accounts, transactions = zaster.parse_xml_string(input)
    assert len(accounts) == 11
    assert len(transactions) == 4
    check_account(accounts["A"], -100, 0, 100)
    check_account(accounts["A1"], -30, 0, 30)
    check_account(accounts["A11"], -10, 0, 10)
    check_account(accounts["A12"], -20, 0, 20)
    check_account(accounts["A2"], -70, 0, 70)
    check_account(accounts["A21"], -30, 0, 30)
    check_account(accounts["A22"], -40, 0, 40)
    check_account(accounts["B"], 100, 100, 0)
    check_account(accounts["B1"], 100, 100, 0)
    check_account(accounts["B11"], 40, 40, 0)
    check_account(accounts["B12"], 60, 60, 0)

    
def test_undefined_account_from():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="Account B" />
</accounts>
<transactions>
  <transaction id="1" date="2015-03-22" amount="10.00" from="Account A" to="Account B" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected KeyError")
    except KeyError as e:
        s = str(e).lower()
        assert "unknown account" in s
        assert "from" in s


def test_undefined_account_to():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="Account A" />
</accounts>
<transactions>
  <transaction id="1" date="2015-03-22" amount="10.00" from="Account A" to="Account B" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected KeyError")
    except KeyError as e:
        s = str(e).lower()
        assert "unknown account" in s
        assert "to" in s


def test_ambiguous_account():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="Account A" />
  <account name="Account A" />
</accounts>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected AmbiguousAccountError")
    except zaster.DuplicateError as e:
        s = str(e).lower()
        assert "account" in s
        assert "defined multiple times" in s

        
def test_nonexisting_parent_account():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="Account A" />
  <account name="Account B" parent="Account A" />
  <account name="Account C" parent="no-such-parent" />
</accounts>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected KeyError")
    except KeyError as e:
        s = str(e).lower()
        assert "account c" in s
        assert "references unknown parent" in s
        assert "no-such-parent" in s


def test_txn_missing_id():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="B" />
</accounts>
<transactions>
<transaction date="2016-02-16" amount="1.00" from="A" to="B" comment="test" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected zaster.MissingRequiredAttributeError")
    except zaster.MissingRequiredAttributeError as e:
        s = str(e).lower()
        assert "transaction" in s
        assert "id" in s


def test_txn_missing_date():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="B" />
</accounts>
<transactions>
<transaction id="1" amount="1.00" from="A" to="B" comment="test" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected zaster.MissingRequiredAttributeError")
    except zaster.MissingRequiredAttributeError as e:
        s = str(e).lower()
        assert "transaction" in s
        assert "date" in s

        
def test_txn_missing_amount():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="B" />
</accounts>
<transactions>
<transaction id="1" date="2016-02-16" from="A" to="B" comment="test" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected zaster.MissingRequiredAttributeError")
    except zaster.MissingRequiredAttributeError as e:
        s = str(e).lower()
        assert "transaction" in s
        assert "amount" in s


def test_txn_missing_from():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="B" />
</accounts>
<transactions>
<transaction id="1" date="2016-02-16" amount="1.00" to="B" comment="test" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected zaster.MissingRequiredAttributeError")
    except zaster.MissingRequiredAttributeError as e:
        s = str(e).lower()
        assert "transaction" in s
        assert "from" in s


def test_txn_missing_to():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="B" />
</accounts>
<transactions>
<transaction id="1" date="2016-02-16" amount="1.00" from="A" comment="test" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected zaster.MissingRequiredAttributeError")
    except zaster.MissingRequiredAttributeError as e:
        s = str(e).lower()
        assert "transaction" in s
        assert "to" in s


def test_txn_duplicate_id():
    bad_input = r'''<?xml version="1.0"?>
<zaster>
<accounts>
  <account name="A" />
  <account name="B" />
</accounts>
<transactions>
<transaction id="1" date="2016-02-16" amount="1.00" from="A" to="B" comment="test" />
<transaction id="1" date="2016-02-17" amount="1.00" from="A" to="B" comment="test" />
</transactions>
</zaster>
'''
    try:
        _ = zaster.parse_xml_string(bad_input)
        raise AssertionError("Expected zaster.DuplicateError")
    except zaster.DuplicateError as e:
        s = str(e).lower()
        assert "transaction" in s
        assert "defined multiple times" in s
