"""Run inside the existing API container. Password on stdin, never in files/argv.

Default is read-only preflight; --apply is restricted to the operator-approved
one-million ACP reserve transfer. Uses existing staking and ledger services.
"""
import asyncio
import json
import os
import sys
import tempfile
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select, text
from app.db.models import Account, Agent, JobWatermark, Stake, StakeStatusEnum, UserAcpWallet
from app.db.session import SessionLocal
from app.api.routers import wallet_acp as wallet, ledger as ledger_router
from app.schemas import WithdrawRequest, Money
from app.services.ledger import balance_for_account, is_ledger_invariant_halted
from app.services.stakes import release_stake

USER = os.environ['RACP_FUNDING_USER_ID']
SOURCE = 'acp1qpj54yrltxljjp5rwzd40hpxkwvlq24azuc7xdxd'
DEST = 'acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz'
KEY = 'racp-reserve-d53f91a6'
AMOUNT = Decimal('1000000')
FEE = Decimal('0.00000100')


def live_balance(address):
    result = wallet._run_walletd(['balance', '--rpc', wallet._require_acp_rpc_url(), '--address', address], timeout_s=60)
    return Decimal(str(result['acp']))


async def main():
    password = sys.stdin.readline().rstrip('\r\n')
    if not password:
        raise RuntimeError('Password required on stdin')
    async with SessionLocal() as s:
        row = (await s.execute(select(UserAcpWallet).where(UserAcpWallet.user_id == USER))).scalar_one()
        if row.address != SOURCE:
            raise RuntimeError('Source binding changed')
        signer = await wallet._get_user_wallet_signer(s, USER, password)
        if not signer.get('keystore_json'):
            raise RuntimeError('Full ACP keystore required; mnemonic-only signing is not used')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', dir='/dev/shm') as key:
            os.chmod(key.name, 0o600)
            key.write(signer['keystore_json'])
            key.flush()
            derived = wallet._run_walletd(['address', '--keystore-file', key.name], timeout_s=60)
        del signer
        if derived.get('address') != SOURCE:
            raise RuntimeError('Signer does not match source')
    # No positions are changed before authentication, source key and live chain checks.
    wallet._chain_supply_info(required=True)
    source_before = live_balance(SOURCE)
    reserve_before = live_balance(DEST)
    if reserve_before >= AMOUNT:
        print(json.dumps({'status': 'already-funded', 'reserveACP': str(reserve_before)}))
        return
    if reserve_before != 0:
        raise RuntimeError('Nonzero partial reserve: inspect before continuing')
    async with SessionLocal() as s:
        _, stake_total, liquid = await wallet._in_work_breakdown_for_user(s, USER)
        available = wallet._personal_balance_view(source_before, stake_total, liquid)[2]
        debit = max(AMOUNT + FEE - available, Decimal(0))
        stake_needed = max(debit - liquid, Decimal(0))
        agents = (await s.execute(select(Agent.id).where(Agent.owner_user_id == USER))).scalars().all()
        stakes = (await s.execute(select(Stake).where(Stake.agent_id.in_(agents), Stake.status == StakeStatusEnum.active, Stake.amount_currency == 'ACP').order_by(Stake.amount_value.desc(), Stake.id))).scalars().all()
        selected, released = [], Decimal(0)
        for st in stakes:
            if released >= stake_needed:
                break
            selected.append((st.id, st.agent_id))
            released += st.amount_value
        if released < stake_needed or source_before < AMOUNT + FEE:
            raise RuntimeError('Insufficient funds to satisfy the approved transfer')
        plan = {'sourceACP': str(source_before), 'availableBeforeACP': str(available), 'ledgerWithdrawalACP': str(debit), 'unstakeACP': str(released), 'stakeCount': len(selected), 'amountACP': str(AMOUNT), 'feeACP': str(FEE)}
        print(json.dumps({'preflight': plan}), flush=True)
        if '--apply' not in sys.argv:
            return
    async with SessionLocal() as s:
        async with s.begin():
            await s.execute(text('SELECT pg_advisory_xact_lock(4663, 1000000)'))
            journal = await s.get(JobWatermark, KEY, with_for_update=True)
            if journal is not None:
                raise RuntimeError('Operation already recorded; inspect journal and chain before any retry')
            if await is_ledger_invariant_halted(s):
                raise RuntimeError('Ledger invariant halted')
            accounts = (await s.execute(select(Account).where(Account.owner_id.in_([USER, *agents]), Account.owner_type.in_(['user', 'agent'])).order_by(Account.id).with_for_update())).scalars().all()
            locked = (await s.execute(select(Stake).where(Stake.id.in_([x[0] for x in selected])).with_for_update())).scalars().all()
            if len(locked) != len(selected):
                raise RuntimeError('Stake inventory changed')
            for st_id, agent_id in selected:
                await release_stake(s, stake_id=UUID(str(st_id)), agent_id=UUID(str(agent_id)))
            remaining = debit
            for account in accounts:
                balance = (await balance_for_account(s, account.id, 'ACP')).get('ACP', Decimal(0))
                take = min(max(balance, Decimal(0)), remaining)
                if take > 0:
                    body = WithdrawRequest(account_owner_type=account.owner_type, account_owner_id=str(account.owner_id), amount=Money(currency='ACP', amount=str(take)), reference=KEY)
                    await ledger_router.withdraw(body, session=s, user_id=USER)
                    remaining -= take
            if remaining != 0:
                raise RuntimeError('Insufficient liquid ledger funds after unstake')
            _, stakes_after, ledger_after = await wallet._in_work_breakdown_for_user(s, USER)
            free_after = wallet._personal_balance_view(source_before, stakes_after, ledger_after)[2]
            if free_after < AMOUNT + FEE:
                raise RuntimeError('Funds changed during reservation release')
            job_id = str(uuid4())
            state = {'status':'release-completed','jobId':job_id,'ledgerWithdrawalACP':str(debit),'unstakeACP':str(released)}
            s.add(JobWatermark(key=KEY, value=json.dumps(state)))
    # Persist a send intent before broadcasting; on ambiguous failure, do not auto-repeat.
    async with SessionLocal() as s:
        async with s.begin():
            journal = await s.get(JobWatermark, KEY, with_for_update=True)
            state = json.loads(journal.value)
            state['status'] = 'transfer-intent'
            journal.value = json.dumps(state)
    async with SessionLocal() as s:
        signer = await wallet._get_user_wallet_signer(s, USER, password)
    del password
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', dir='/dev/shm') as key:
        os.chmod(key.name, 0o600)
        key.write(signer['keystore_json'])
        key.flush()
        del signer
        wallet._run_withdraw_transfer_job(job_id=job_id, user_id=USER, rpc_url=wallet._require_acp_rpc_url(), transfer_signer_args=['--keystore-file', key.name], to_address=DEST, amount_acp=str(AMOUNT), fee_acp=str(FEE), from_address=SOURCE)
    result = await wallet._load_withdraw_job(job_id)
    safe = {k:result.get(k) for k in ['status','accepted','txid','reason','error']} if result else {'status':'unknown'}
    async with SessionLocal() as s:
        async with s.begin():
            journal = await s.get(JobWatermark, KEY, with_for_update=True)
            state['status'] = 'transfer-accepted' if safe.get('accepted') else 'transfer-needs-inspection'
            state['txid'] = safe.get('txid')
            journal.value = json.dumps(state)
    print(json.dumps({'transfer':safe}), flush=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        # Do not print exception payloads: upstream crypto/helper errors can contain sensitive material.
        print(json.dumps({'status':'stopped','errorType':type(e).__name__}), flush=True)
        sys.exit(1)
