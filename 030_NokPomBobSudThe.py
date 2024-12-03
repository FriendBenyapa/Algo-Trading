import pandas as pd
import numpy as np
import os
from datetime import datetime

# กำหนดไดเรกทอรีหลัก
output_dir = os.path.expanduser("~/Desktop/competition_api")
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created main directory: {output_dir}")

team_name = "030_NokPomBobSudThe"  # รหัสทีม_ชื่อทีม 

# ฟังก์ชันโหลดข้อมูลที่บันทึกไว้ก่อนหน้า
def load_previous(file_type, teamName):
    global prev_portfolio_df
    folder_path = output_dir + f"/Previous/{file_type}"
    file_path = folder_path + f"/{teamName}_{file_type}.csv"

    if os.path.exists(file_path):
        prev_portfolio_df = pd.read_csv(file_path)
        print(f"Loaded '{file_type}' Previous")
    else:
        print(f"Previous '{file_type}' file not found")

# ฟังก์ชันบันทึกผลลัพธ์
def save_output(data, file_type, teamName):
    folder_path = output_dir + f"/Result/{file_type}"
    file_path = folder_path + f"/{teamName}_{file_type}.csv"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        print(f"Directory created: '{folder_path}'")

    # Save CSV
    data.to_csv(file_path, index=False)
    print(f"{file_type} saved at {file_path}")

# อ่านไฟล์ Daily_Ticks.csv
File_Daily_Tick = os.path.expanduser("~/Desktop/Daily_Ticks.csv")

if os.path.exists(File_Daily_Tick):
    daily_ticks = pd.read_csv(File_Daily_Tick)
    print(f"Loaded Daily_Ticks file from {File_Daily_Tick}")
else:
    print(f"Daily_Ticks file not found at {File_Daily_Tick}")

# === กำหนดค่าพื้นฐานและตัวแปรที่ใช้ในการประมวลผล ===
starting_balance = 10000000
cash_balance = starting_balance

statements = []
portfolio = []

count_wins = 0
count_matched_trades = 0
realized_profit_loss = 0.0000 # ตัวแปรนี้เก็บผลรวม Realized P/L ทั้งหมดจากการขายหุ้น
unrealized_profit_loss = 0.0000
unrealized_profit_loss_percentage = 0.0000
max_balance = starting_balance
min_balance = starting_balance
drawdowns = []
max_value = starting_balance  # จุดสูงสุดเริ่มต้น
min_value = starting_balance   # จุดต่ำสุดเริ่มต้น
# เพิ่มตัวแปรสำหรับเก็บจำนวนเงินสุทธิจากการซื้อและขาย
total_buy = 0.0000
total_sell = 0.0000

# === วนลูปประมวลผลข้อมูลการซื้อขาย ===
for _, row in daily_ticks.iterrows():
    # กำหนดค่า today ให้เป็นวันที่ปัจจุบัน
    today = datetime.now().strftime('%Y-%m-%d')

    stock_name = row['ShareCode']
    price = round(row['LastPrice'], 4)
    volume = max(100, int(row['Volume'] // 100) * 100)  # ซื้อ-ขายเป็นจำนวนเต็มของ 100 หุ้น
    side = row['Flag']
    transaction_cost = round(price * volume, 4)

    if side == 'Buy' and cash_balance >= transaction_cost:
        cash_balance = round(cash_balance - transaction_cost, 4)

        # เพิ่มยอดการซื้อ
        total_buy += transaction_cost  

        # Append stock to portfolio
        portfolio.append({
            'file_csv': 'portfolio_file',
            'namefile': '030',
            'Symbol': stock_name,
            'Start_Vol': 0.0,
            'Actual_Vol': volume,
            'Avg_Cost': round(price, 4),
            'Market_Price': round(price, 4),
            'Amount_Cost': round(transaction_cost, 4),
            'Market_Value': round(volume * price, 4),
            'Unrealized_P/L': 0.0000,
            '%Unrealized_P/L': 0.0000,
            'Realized_P/L': 0.0000 # กำไร/ขาดทุนจากการขาย
        })

    elif side == 'Sell':
        # ตรวจสอบว่ามีหุ้นในพอร์ตเพียงพอสำหรับขาย
        stock_in_portfolio = next((stock for stock in portfolio if stock['Symbol'] == stock_name), None)

        if stock_in_portfolio and stock_in_portfolio['Actual_Vol'] >= volume:
            cash_balance = round(cash_balance + transaction_cost, 4)
            # คำนวณผลกำไร/ขาดทุนที่เกิดจากการขาย
            realized_profit_loss += round(price * volume - stock_in_portfolio['Avg_Cost'] * volume, 4)

            # Update portfolio (ลดจำนวนหุ้นในพอร์ต เมื่อขายหุ้นสำเร็จ)
            stock_in_portfolio['Actual_Vol'] -= volume
            stock_in_portfolio['Market_Value'] = round(stock_in_portfolio['Actual_Vol'] * price, 4)

            # คำนวณกำไร/ขาดทุนที่เกิดขึ้นจริง (Realized P/L) ในพอร์ต
            stock_in_portfolio['Realized_P/L'] += round(price * volume - stock_in_portfolio['Avg_Cost'] * volume, 4)

            # เพิ่มใน win count หากมีผลกำไร
            if price > stock_in_portfolio['Avg_Cost']:
                count_wins += 1

            # เพิ่มจำนวน matched trades
            count_matched_trades += 1  

        # แจ้งเตือนเมื่อขายไม่ได้ หากไม่มีหุ้นในพอร์ตหรือจำนวนหุ้นไม่เพียงพอ
        else: 
            print(f"Cannot sell {volume} shares of {stock_name}. Not enough shares in portfolio.")

    # === คำนวณ Unrealized P/L และ % Unrealized P/L ===
    for stock in portfolio:
        if stock['Actual_Vol'] > 0:  # คำนวณ Unrealized P/L เฉพาะหุ้นที่ยังคงอยู่ในพอร์ต
            stock['Unrealized_P/L'] = round((price - stock['Avg_Cost']) * stock['Actual_Vol'], 4)
            stock['%Unrealized_P/L'] = round((stock['Unrealized_P/L'] / stock['Market_Value']) * 100, 4) if stock['Market_Value'] != 0 else 0.0000

    # คำนวณผลรวม Unrealized P/L และ % Unrealized P/L
    unrealized_pnl = round(sum([stock['Unrealized_P/L'] for stock in portfolio]), 4)
    total_market_value = round(sum([stock['Market_Value'] for stock in portfolio]), 4)
    percentage_unrealized_pnl = round((unrealized_pnl / total_market_value) * 100, 4) if total_market_value != 0 else 0.0000

    # Update statement
    statements.append({
        'file_csv': 'statement_file',
        'namefile': '030',
        'Symbol': stock_name,
        'Date': today,
        'Time': pd.to_datetime(row['TradeDateTime']).strftime('%H:%M:%S'),
        'Side': side,
        'Volume': volume,
        'Price': round(price, 4),
        'Amount_Cost': round(transaction_cost, 4),
        'End_line_available': round(cash_balance, 4)
    })

# กำหนด trading_day ให้เป็นวันที่ปัจจุบัน
trading_day = datetime.now().strftime('%Y-%m-%d')

# คำนวณ Net Amount (Sell - Buy)
net_amount = round(total_sell - total_buy, 4)

# === คำนวณ NAV, Drawdown และ Return Rate ===
nav = round(cash_balance + sum([stock['Market_Value'] for stock in portfolio]), 4)
if nav > max_value:
    max_value = nav  
if nav < min_value:
    min_value = nav  

max_drawdown = round((nav - max_value) / max_value, 4)  # Max Drawdown = ผลต่างระหว่างจุดสูงสุดและจุดต่ำสุด
relative_drawdown = round((max_balance - nav) / max_balance, 4) * 100  # Relative Drawdown = ความขาดทุนสูงสุดจาก max_balance

return_rate = round(((nav - starting_balance) / starting_balance) * 100, 4)

# คำนวณ Calmar Ratio
calmar_ratio = round(return_rate / abs(max_drawdown), 4) if max_drawdown != 0 else 0.0000

# สร้าง Summary
summary = {
    'file_csv': 'sum_file',
    'namefile': '030',
    'trading_day': trading_day,
    'nav': nav,
    'End_line_available': round(cash_balance, 4),
    'Start_line_available': round(starting_balance, 4),
    'Count_wins': count_wins,
    'Count_matched_trades': count_matched_trades, 
    'Count_transactions': len(statements),
    'Net_Amount_today': net_amount,
    'Unrealized_P/L': unrealized_pnl,  # ผลรวม Unrealized P/L
    '%Unrealized_P/L': percentage_unrealized_pnl,  # ผลรวม Unrealized P/L เป็น %
    'Realized_P/L': realized_profit_loss,  
    'Max_Value': max_value,  # Max Value ที่เป็นจุดสูงสุดของ NAV
    'Min_Value': min_value,  # Min Value ที่เป็นจุดต่ำสุดของ NAV
    '%Win_rate': round((count_wins / count_matched_trades) * 100, 4) if count_matched_trades != 0 else 0.0000,  # คำนวณ Win Rate
    'Calmar_Ratio': calmar_ratio,
    '%Relative_drawdown': relative_drawdown,  
    '%Max_drawdown': max_drawdown * 100,  # Max Drawdown เป็นเปอร์เซ็นต์
    'percent_Return': return_rate

}

# บันทึกข้อมูล
portfolio_df = pd.DataFrame(portfolio)
statements_df = pd.DataFrame(statements)
summary_df = pd.DataFrame([summary])

save_output(portfolio_df, "Portfolio", team_name)
save_output(statements_df, "Statements", team_name)
save_output(summary_df, "Summary", team_name)

print("Process complete. Results saved.")
