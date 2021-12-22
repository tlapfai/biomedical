import QuantLib as ql
import numpy as np
import pandas as pd
from yieldtermstructurebuilder import OISYieldTermStructureBuilder, LiborSwapYieldTermStructureBuilder

rev_date = ql.Date(17,11,2021)
ql.Settings.instance().evaluationDate = rev_date

#----trade setup----
pay_rec = ql.VanillaSwap.Receiver
calendar = ql.UnitedStates()
effective_date = ql.Date(19,11,2021)
swap_tenor = ql.Period('2y')
maturity = calendar.advance(effective_date, swap_tenor)

notional = 1e9
fixedSchedule = ql.MakeSchedule(effective_date, maturity, ql.Period('6M'), calendar=ql.UnitedStates(), rule=ql.DateGeneration.Forward)
floatSchedule = ql.MakeSchedule(effective_date, maturity, ql.Period('3M'), calendar=ql.UnitedStates(), rule=ql.DateGeneration.Forward)


bucket_nodes = ['2W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '30Y' ]  # the durations
bucket_dates = [ calendar.advance(rev_date, ql.Period(bn)) for bn in bucket_nodes ]
spreads = [ ql.SimpleQuote(0.0) for n in bucket_nodes ] # null spreads to begin

#----curve setup----
ois_builder = OISYieldTermStructureBuilder()
yts_ois = ois_builder(rev_date, 'ois2021-11-17_ticker.csv')
yts_handle_ois = ql.RelinkableYieldTermStructureHandle(yts_ois)
spread_ois = ql.SpreadedLinearZeroInterpolatedTermStructure(yts_handle_ois,[ ql.QuoteHandle(q) for q in spreads ], bucket_dates)
spread_ois_handle = ql.YieldTermStructureHandle(spread_ois)

swap_builder = LiborSwapYieldTermStructureBuilder()
yts_swap = swap_builder(rev_date, 'curve.csv', yts_handle_ois)
yts_handle_swap = ql.RelinkableYieldTermStructureHandle(yts_swap)
spread_swap = ql.SpreadedLinearZeroInterpolatedTermStructure(yts_handle_swap,[ ql.QuoteHandle(q) for q in spreads ], bucket_dates)
spread_swap_handle = ql.YieldTermStructureHandle(spread_swap)

engine = ql.DiscountingSwapEngine(spread_ois_handle)

fixed_rate = 0.32527*0.01
index_libor = ql.USDLibor(ql.Period('3m'), spread_swap_handle)
my_swap = ql.VanillaSwap(pay_rec, notional, fixedSchedule, fixed_rate, ql.Thirty360(), floatSchedule, index_libor, 0, ql.Actual360())

my_swap.setPricingEngine(engine)

fairRate = my_swap.fairRate()
npv = my_swap.NPV()

with open("result.txt", "w") as f:
    f.write(f"Fair swap rate: {fairRate:.16%}\n")
    f.write(f"Swap NPV: {npv:,.2f}\n")

with open("tradecashflow.csv", "w") as f:
    for i in range(2):
        f.write(f"leg {str(i)}\n")
        for cf in list(my_swap.leg(i)):
            f.write(f"{cf.date().ISO()},{cf.amount():.2f},{yts_ois.discount(cf.date()):.16f}\n")

    # f.write("===========BPV============\n")
    # for i in range(len(simple_quote_swap)):
        # simple_quote_swap[i].setValue(simple_quote_swap[i].value() + 0.0001)
        # f.write(f"{cv.index[i]} {my_swap.NPV() - npv:,.2f}\n")
        # simple_quote_swap[i].setValue(simple_quote_swap[i].value() - 0.0001)
        
    # f.write('----- OIS curve ----\n')
    # for n in yts_ois.nodes():
        # f.write(f"{n[0].ISO()},{n[1]}\n")
    # f.write('----- USD curve ----\n')
    # for n in yts_swap.nodes():
        # f.write(f"{n[0].ISO()},{n[1]}\n")
        

with open("result_krr.csv", "w") as f:
    for i in range(len(bucket_nodes)):
        spreads[i].setValue(0.0001)
        for j in range(2):
            print(f"leg {str(j)}\n")
            for cf in list(my_swap.leg(j)):
                print(f"{cf.date().ISO()},{cf.amount():.2f},{yts_ois.discount(cf.date()):.8f}\n")
        f.write(f"{bucket_nodes[i]},{my_swap.NPV() - npv:.2f}\n")
        spreads[i].setValue(0.0)
        
with open("shift_curve.csv", 'w') as f:
    for i in range(1000):
        d = rev_date + ql.Period(i, ql.Days)
        z = spread_swap_handle.zeroRate(d, ql.Actual365Fixed(), ql.Continuous).rate()
        spreads[4].setValue(0.01)
        z2 = spread_swap_handle.zeroRate(d, ql.Actual365Fixed(), ql.Continuous).rate()
        spreads[4].setValue(0.0)
        f.write(f"{d.ISO()},{z:.12f},{z2:.12f}\n")
