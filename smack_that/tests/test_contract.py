#tests/test_contract.py
import unittest
import base64
from contracting.client import ContractingClient
client = ContractingClient()

with open('./currency.py') as f:
    code = f.read()
    client.submit(code, name='currency')
with open('../contracts/con_smack_that.py') as f:
    code = f.read()
    client.submit(
        code,
        name='con_smack_that'
    )

initial_state = {
    "odds": 20,
    "cost": 10
}

class MyTestCase(unittest.TestCase):
    con_smack_that = None
    currency_contract = None

    def change_signer(self, name):
        client.signer = name
        self.con_smack_that = client.get_contract('con_smack_that')
        self.currency_contract = client.get_contract('currency')

    def test_1_seed_constants(self):
        self.change_signer('stu')
        print("TEST SEED CONSTANTS")

        self.assertEqual(self.con_smack_that.quick_read('settings', 'odds'), initial_state['odds'])
        self.assertEqual(self.con_smack_that.quick_read('settings', 'cost'), initial_state['cost'])

    def test_2_smack(self):
        self.change_signer('stu')

        prev_balance = self.currency_contract.quick_read('balances', 'stu')

        self.con_smack_that.smack()

        new_balance = self.currency_contract.quick_read('balances', 'stu')
        print ('prev_balance:', prev_balance, 'new_balance:', new_balance)
        self.assertNotEqual(prev_balance, new_balance)


    def test_3_win(self):
        self.change_signer('stu')

        prev_balance = self.currency_contract.quick_read('balances', 'stu')

        self.con_smack_that.test_smack_win()

        new_balance = self.currency_contract.quick_read('balances', 'stu')
        print('prev_balance:', prev_balance, 'new_balance:', new_balance)
        self.assertLess(prev_balance, new_balance)


    def test_4_lose(self):
        self.change_signer('stu')

        prev_balance = self.currency_contract.quick_read('balances', 'stu')

        self.con_smack_that.test_smack_lose()

        new_balance = self.currency_contract.quick_read('balances', 'stu')
        print('prev_balance:', prev_balance, 'new_balance:', new_balance)
        self.assertGreater(prev_balance, new_balance)

if __name__ == '__main__':
    unittest.main()