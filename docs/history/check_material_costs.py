"""Recompute the dated partial budget; no network, purchases or live-price claim."""
import json
from pathlib import Path


def calculate(ledger):
    subtotal = available = 0
    rows = []
    for item in ledger['quantities']:
        quote = ledger['prices'][item['price_id']]
        required, size, cents = item['required_units'], quote['package_quantity'], quote['package_price_usd_cents']
        assert all(isinstance(value, int) for value in (required, size, cents))
        assert required >= 0 and size > 0 and cents >= 0 and quote['status'] == 'sourced'
        packages = (required+size-1)//size
        cost = packages*cents
        subtotal += cost
        if quote['available_at_retrieval'] is True:
            available += cost
        rows.append((item['price_id'], required, packages, packages*size-required, cost))
    return rows, subtotal, available


if __name__ == '__main__':
    ledger = json.loads(Path(__file__).with_name('material-costs.json').read_text())
    rows, subtotal, available = calculate(ledger)
    assert subtotal == ledger['published_subtotal_usd_cents']
    assert available == ledger['available_priced_subtotal_usd_cents']
    quantities = {row['price_id']: row['required_units'] for row in ledger['quantities']}
    assert quantities['washer'] == 2*quantities['bolt'] == 2*quantities['nut']
    for name, required, packages, spare, cents in rows:
        print(f'{name}: need {required}, buy {packages} package(s), spare {spare}, ${cents/100:.2f}')
    quote = ledger['prices']['spax_comparison']
    costs = {name: ((count+quote['package_quantity']-1)//quote['package_quantity'])*quote['package_price_usd_cents']
             for name, count in ledger['screw_scenarios'].items()}
    assert set(costs.values()) == {1263}
    assert ledger['owned_materials'][0]['retain_existing_purchase'] is True
    assert ledger['unpriced'][0]['required_units'] is None
    assert ledger['candidate'] == 'round-bore-service-development'
    assert ledger['unpriced'][1]['required_units'] == ledger['screw_scenarios']['current_round_development'] == 56
    assert not ledger['optional_unpriced_alternatives'][0]['included_in_base_purchase_budget']
    print(f'Indicative priced portion: ${subtotal/100:.2f}; listed-available portion: ${available/100:.2f}')
    print('Comparison-only SPAX package costs: '+str({k: v/100 for k, v in costs.items()}))
    print('Owned face plywood retained; any shortage, selected screw SKU, hold hardware, tax and shipping remain unresolved.')
