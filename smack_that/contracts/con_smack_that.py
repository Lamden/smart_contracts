import currency

balances = ForeignHash(foreign_contract='currency', foreign_name='balances')
settings = Hash(default_value=0)

random.seed()

@construct
def seed():
    settings['odds'] = 20
    settings['cost'] = 10

@export
def smack():
    currency.transfer_from(amount=settings['cost'], to=ctx.this, main_account=ctx.caller)
    x = random.randint(1, settings['odds'])
    if x == settings['odds']:
        currency.transfer(amount=balances[ctx.this], to=ctx.caller)

# REMOVE FOR PRODUCTION
@export
def test_smack_win():
    currency.transfer_from(amount=settings['cost'], to=ctx.this, main_account=ctx.caller)
    x = settings['odds']
    if x == settings['odds']:
        currency.transfer(amount=balances[ctx.this], to=ctx.caller)

@export
def test_smack_lose():
    currency.transfer_from(amount=settings['cost'], to=ctx.this, main_account=ctx.caller)
    x = settings['odds']
    if x == 19:
        currency.transfer(amount=balances[ctx.this], to=ctx.caller)