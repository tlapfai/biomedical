import QuantLib as ql
import pandas as pd

class OISYieldTermStructureBuilder:
    def __init__(self):
        pass
    def __call__(self, date, csv_path):
        yts_handle_ois = ql.RelinkableYieldTermStructureHandle()
        cv_df = pd.read_csv(csv_path ,index_col = 'Term')
        cv = cv_df.drop(columns=['Shift','Shifted Rate','Zero Rate','Discount'])
        cv['Market Rate'] = cv_df['Market Rate'] * 0.01
        helpers = ql.RateHelperVector()
        overnight_index = ql.OvernightIndex('USD EFFR', 0, ql.USDCurrency(), ql.UnitedStates(), ql.Actual360(), yts_handle_ois)
        simple_quote = []
        
        for term, data in cv.iterrows():
            term = term.replace(' ','')
            if term == '1D':
                simple_quote.append( ql.SimpleQuote(float(data['Market Rate'])) )
                helpers.append( ql.DepositRateHelper(ql.QuoteHandle(simple_quote[-1]), overnight_index) )
                #index.addFixing(rev_date, float(data['Market Rate']))
            else:
                settlementDays = 2
                swapIndex = ql.OvernightIndexedSwapIndex("EFFR", ql.Period(term), settlementDays, ql.USDCurrency(), overnight_index)
                simple_quote.append( ql.SimpleQuote(float(data['Market Rate'])) )
                helpers.append( ql.OISRateHelper(   2, 
                                                    ql.Period(term), 
                                                    ql.QuoteHandle(simple_quote[-1]), 
                                                    overnight_index,
                                                    paymentLag=0, 
                                                    paymentCalendar=ql.UnitedStates()
                                                ) )
        #ois_curve = ql.PiecewiseLogLinearDiscount(date, helpers, ql.Actual365Fixed())
        #yts_handle_ois.linkTo(ois_curve)
        return ql.PiecewiseLogLinearDiscount(date, helpers, ql.Actual365Fixed())


class LiborSwapYieldTermStructureBuilder:
    def __init__(self):
        pass
    def __call__(self, date, csv_path, yts_handle_ois):
        yts_handle = ql.RelinkableYieldTermStructureHandle()
        cv_df = pd.read_csv(csv_path ,index_col = 'Term')
        cv = cv_df.drop(columns=['Shift','Shifted Rate','Zero Rate','Discount'])
        cv['Market Rate'] = cv_df['Market Rate'] * 0.01
        helpers = ql.RateHelperVector()
        index_libor = ql.USDLibor(ql.Period('3m'), yts_handle)
        simple_quote = []

        for term, data in cv.iterrows():
            term = term.replace(' ','')
            if term == '3MO':
                simple_quote.append( ql.SimpleQuote(float(data['Market Rate'])) )
                helpers.append( ql.DepositRateHelper(ql.QuoteHandle(simple_quote[-1]), index_libor) )
            elif term[:2] == 'ED':
                simple_quote.append( ql.SimpleQuote((1.0-float(data['Market Rate']))*100) )
                helpers.append( ql.FuturesRateHelper(ql.QuoteHandle(simple_quote[-1]), ql.IMM.date(term[-2:]), index_libor) )
            elif term[-2:] == 'YR':
                simple_quote.append( ql.SimpleQuote(float(data['Market Rate'])) ) 
                swapIndex = ql.UsdLiborSwapIsdaFixAm(ql.Period(term.replace('YR','y')))
                helpers.append( ql.SwapRateHelper(ql.QuoteHandle(simple_quote[-1]), 
                                                    swapIndex, 
                                                    ql.QuoteHandle(), 
                                                    ql.Period(), 
                                                    yts_handle_ois
                                                    )
                                )
        return ql.PiecewiseLogLinearDiscount(date, helpers, ql.Actual365Fixed())
