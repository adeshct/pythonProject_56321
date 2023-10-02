import yfinance as yf
from datetime import datetime, timedelta

previous_day = datetime.now().date() - timedelta(days=1)


# df = yf.download('^NSEBANK',start = "2023-09-22", end = "2023-09-22")

# high =  df['High'].iloc[0]
#
# low = df['Low'].iloc[0]
# close = df['Close'].iloc[0]
class Cpr_compute:
    def compute_cpr():
        high = 44936.55
        low = 44400.90
        close = 44766.10
    
        central_pivot = round((high + low + close) / 3)
        bottom_cpr = round((high + low) / 2)
        top_cpr = round((central_pivot - bottom_cpr) + central_pivot)
        R1 = round((2 * central_pivot) - low)
        S1 = round((2 * central_pivot) - high)
        R2 = round(central_pivot + (high - low))
        S2 = round(central_pivot - (high - low))
        R3 = round(high + 2 * (central_pivot - low))
        S3 = round(low - 2 * (high - central_pivot))
        R4 = round(R3+(R2-R1))
        S4 = round(S3-(S1-S2))

        if bottom_cpr > top_cpr:
            bottom_cpr, top_cpr = top_cpr, bottom_cpr

        print("Central_pivot = ", central_pivot)
        print("bottom_cpr = ",bottom_cpr)
        print("top_cpr = ",top_cpr)
        print("R1 = ",R1)
        print("R2 = ",R2)
        print("R3 = ",R3)
        print("R4 = ",R4)
    
        print("S1 = ",S1)
        print("S2 = ",S2)
        print("S3 = ",S3)
        print("S4 = ",S4)
        
        return central_pivot, top_cpr, bottom_cpr, R1,R2,R3,R4,S1,S2,S3,S4


