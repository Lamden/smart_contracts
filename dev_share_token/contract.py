from contracting.client import ContractingClient
from unittest import TestCase


def coin():
    import currency
    import submission

    supply = Variable()
    balances = Hash(default_value=0)
    owner = Variable()

    @construct
    def seed(amount=1_000_000):
        balances[ctx.caller] = amount
        supply.set(amount)
        owner.set(ctx.caller)

    @export
    def transfer(amount: float, to: str):
        assert amount > 0, 'Cannot send negative balances!'
        sender = ctx.caller
        assert balances[sender] >= amount, 'Not enough coins to send!'

        balances[sender] -= amount
        balances[to] += amount

    @export
    def balance_of(account: str):
        return balances[account]

    @export
    def total_supply():
        return supply.get()

    @export
    def allowance(main: str, spender: str):
        return balances[main, spender]

    @export
    def approve(amount: float, to: str):
        assert amount > 0, 'Cannot approve negative amounts!'
        sender = ctx.caller
        balances[sender, to] += amount
        return balances[sender, to]

    @export
    def transfer_from(amount: float, to: str, main_account: str):
        assert amount > 0, 'Cannot send negative balances!'
        sender = ctx.caller

        assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
            .format(balances[main_account, sender], amount)
        assert balances[main_account] >= amount, 'Not enough coins to send!'

        balances[main_account, sender] -= amount
        balances[main_account] -= amount

        balances[to] += amount

    @export
    def redeem(amount: float):
        assert balances[ctx.caller] >= amount, 'Not enough tokens to redeem!'
        assert amount > 0, 'Invalid amount!'

        balances[ctx.caller] -= amount

        share = amount / supply.get()
        reward = share * currency.balance_of(ctx.this)

        if reward > 0:
            currency.transfer(reward, ctx.caller)

        supply.set(supply.get() - amount)

    @export
    def change_ownership(new_owner: str):
        assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

        owner.set(new_owner)

    @export
    def change_developer(contract: str, new_developer: str):
        assert ctx.caller == owner.get(), 'Only the owner can change the developer!'

        submission.change_developer(contract=contract, new_developer=new_developer)


def mock():
    @export
    def some_contract():
        # Fees for this will go into the coin
        pass


class TestCoinContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        with open('../common/currency.py') as f:
            code = f.read()
            self.c.submit(code, name='currency')

        self.currency = self.c.get_contract('currency')

        self.c.submit(coin)
        self.coin = self.c.get_contract('coin')
        self.submission = self.c.get_contract('submission')

    def tearDown(self):
        self.c.flush()

    def test_change_developer_works(self):
        self.c.submit(mock)
        m = self.c.get_contract('mock')

        # Set up rev share
        self.submission.change_developer(contract='mock', new_developer='coin')

        self.assertEqual(m.__developer__, 'coin')

        # Change it
        self.coin.change_developer(contract='mock', new_developer='not_stu')

        self.assertEqual(m.__developer__, 'not_stu')

    def test_redeem_not_enough_balance_throws_assert(self):
        with self.assertRaises(AssertionError):
            self.coin.redeem(amount=1, signer='not_stu')

    def test_redeem_negative_throws_assert(self):
        with self.assertRaises(AssertionError):
            self.coin.redeem(amount=-1, signer='stu')

    def test_redeem_adjusts_supply(self):
        self.coin.redeem(amount=1, signer='stu')
        self.assertEqual(self.coin.supply.get(), 999_999)

    def test_redeem_reduces_balance(self):
        self.coin.redeem(amount=1, signer='stu')
        self.assertEqual(self.coin.balances['stu'], 999_999)

    def test_redeem_gives_correct_reward(self):
        self.currency.transfer(amount=10000, to='coin')
        self.coin.transfer(amount=10000, to='not_stu')
        self.coin.redeem(amount=10000, signer='not_stu')

        self.assertEqual(self.currency.balances['not_stu'], 100)

    def test_coin_construction(self):
        self.assertEqual(self.coin.balances['stu'], 1000000)

    def test_transfer_not_enough(self):
        with self.assertRaises(AssertionError):
            self.coin.transfer(amount=9999999, to='raghu')

    def test_transfer_enough(self):
        self.coin.transfer(amount=123, to='raghu')
        self.assertEqual(self.coin.balances['raghu'], 123)

    def test_balance_of_works(self):
        self.coin.transfer(amount=123, to='raghu')
        self.assertEqual(self.coin.balance_of(account='raghu'), 123)

    def test_total_supply_pre_mint(self):
        self.assertEqual(self.coin.total_supply(), 1000000)
        self.assertEqual(self.coin.supply.get(), 1000000)

    def test_approve_modified_balances(self):
        self.coin.approve(amount=100, to='raghu')
        self.assertEqual(self.coin.balances['stu', 'raghu'], 100)

    def test_allowance_returns_approve(self):
        self.coin.approve(amount=100, to='raghu')
        self.assertEqual(self.coin.allowance(main='stu', spender='raghu'), 100)

    def test_transfer_from_failure_not_enough_allowance(self):
        self.coin.approve(amount=100, to='raghu')
        with self.assertRaises(AssertionError):
            self.coin.transfer_from(amount=101, to='colin', main_account='stu', signer='raghu')

    def test_transfer_from_failure_not_enough_in_main_account(self):
        self.coin.approve(amount=1000000000, to='raghu')
        with self.assertRaises(AssertionError):
            self.coin.transfer_from(amount=1000000000, to='colin', main_account='stu', signer='raghu')

    def test_transfer_from_success_modified_balance_to_and_allowance(self):
        self.coin.approve(amount=100, to='raghu')
        self.coin.transfer_from(amount=33, to='colin', main_account='stu', signer='raghu')

        self.assertEqual(self.coin.balances['colin'], 33)
        self.assertEqual(self.coin.balances['stu'], 1000000 - 33)
        self.assertEqual(self.coin.balances['stu', 'raghu'], 67)

    def test_change_ownership_modifies_owner(self):
        self.coin.change_ownership(new_owner='raghu')
        self.assertEqual(self.coin.owner.get(), 'raghu')

    def test_change_ownership_only_prior_owner(self):
        with self.assertRaises(AssertionError):
            self.coin.change_ownership(new_owner='colin', signer='raghu')