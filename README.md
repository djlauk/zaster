# zaster

*zaster* is a simple double account book keeping software.
Main features:

- Double account book keeping
- Simple XML file format makes for easy transfer to or from other tools
- Supports account hierarchies (transactions on child accounts will be
  added to the parents; useful for grouped reporting)


## XML file format

Create an XML file from the following template:

    <?xml version="1.0" encoding="utf-8"?>
    <zaster>
      <accounts>
        <!-- account elements will go here -->
      </accounts>
      <transactions>
        <!-- transaction elements will go here -->
      </transactions>
    </zaster>


### Account elements

Each ``account`` element has the following attributes:

- **name**: ID of the account. Must be unique. Required.
- parent: ID of the parent account (if any). The definition of the parent
  must precede the definition of the child. Optional.
- description: Any description you'd like. Optional.


### Transaction elements

Each ``transaction`` element has the following attributes:

- **id**: ID of the transaction. Must be unique. Required.
- **date**: Date (in ISO8601 format, although that is not enforced) of
  the transaction. Required.
- **amount**: The amount of currency being transferred in the transaction.
  Required.
- **from**: The ID of the account, where the amount is subtracted.
  Required.
- **to**: The ID of the account, where the amount is added. Required.
- **comment**: Any description you'd like. Optional.


## Usage tips

### Use account hierarchies for reporting

If you decided you want to differentiate your expenses between
categories "food", "house", "car" and "other", and for the car you want
to see reports separately for "repairs" and "fuel", you might create
the following XML structure:

    <?xml version="1.0" encoding="utf-8"?>
    <zaster>
      <accounts>
        <account name="expenses" />
        <account name="food" parent="expenses" />
        <account name="house" parent="expenses" />
        <account name="car" parent="expenses" />
        <account name="fuel" parent="car" />
        <account name="repairs" parent="car" />
        <account name="other" parent="expenses" />
      </accounts>
    <!-- ... -->
    </zaster>

With this setup, you can show reports on "expenses" in general, "car"
(a bit more specific, but still a group) or "repairs" (very specific).

*Note* that it would not be possible to have another "repairs" account
for the house. (The next section presents a possible solution.)


### Use alphabitcally sortable identifiers

By default, *zaster*'s commands will sort outputs in lexicographical order.
The ``balance`` command will list all accounts in this order. If you want
all accounts of a parent to be listet below that parent, make the parent's
name a part of the account's name. It would be easiest to use a separator
token, e.g. any of ``/``, ``\``, ``.``, ``::``, ...

Actually, *zaster* does not care about the name of accounts or IDs of
transactions. But to you this may make it more comfortable when the balances
for accounts "car", "fuel" and "repairs" appear under each other. So,
drawing on our previous example, a possible solution would be to use
something like this:

    <?xml version="1.0" encoding="utf-8"?>
    <zaster>
      <accounts>
        <account name="expenses" />
        <account name="expenses/food" parent="expenses" />
        <account name="expenses/house" parent="expenses" />
        <account name="expenses/house/repairs" parent="expenses/house" />
        <account name="expenses/house/mortgage" parent="expenses/house" />
        <account name="expenses/car" parent="expenses" />
        <account name="expenses/car/fuel" parent="expenses/car" />
        <account name="expenses/car/repairs" parent="expenses/car" />
        <account name="expenses/other" parent="expenses" />
      </accounts>
    <!-- ... -->
    </zaster>

Then the *balance* command would then e.g. print out lines like that:

    ACCOUNT;TOTAL OUT;TOTAL IN;BALANCE
    expenses;0.00;920.00;920.00
    expenses/car;0.00;130.00;130.00
    expenses/car/fuel;0.00;50.00;50.00
    expenses/car/repairs;0.00;80.00;80.00
    expenses/food;0.00;240.00;240.00
    expenses/house;0.00;450.00;450.00
    expenses/house/mortgage;0.00;150.00;150.00
    expenses/house/repairs;0.00;300.00;300.00
    expenses/other;0.00;100.00;100.00


## A primer on double account book keeping

I had only little training on accounting in general, so this can only
be a very shallow introduction.

The underlying idea for double account book keeping is, that **everything
must be nicely balanced**. You can only move amounts of money from one place
to another. This is very simple to understand, if you consider withdrawing
money from your bank account at an ATM. In that case a certain amount of
money will be moved from your bank account to your wallet, which also
serves as an account.

Things may get confusing when you consider income (at least it was the
case for me): You define an artificial "income" account and transfer
money from there to the bank account. That means, that the accumulated
balance (as per the bank statement) on the "income" account will be
negative and continue growing towards negative infinity.

This is mathematically required, so on your bank account the balance can
go up. That's all there is to it. It's just an *artificial counterweight*,
so in the end it all adds up to 0.

Expenses, on the other hand, although you give money away, will continue
to grow towards positive infinity. Again, the same "mind trick" is at work.
