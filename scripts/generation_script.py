import pandas as pd
import numpy as np
import os

def generate_dach_files_final():
    # 1. Path Management: Find where the script itself is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"--- Script Location: {script_dir} ---")

    # DACH Standard Scaling Constants
    PV_SCALE_FACTOR = 10.0 / 103.42  # Scales original peak to 10 kWp
    BATT_CAPACITY_KWH = 14.0         # Standard home battery size
    BATT_MAX_POWER_KW = 5.0          # Standard inverter power
    BATT_MAX_POWER_15MIN = BATT_MAX_POWER_KW / 4.0 

    years = [2025, 2026, 2027]
    
    for year in years:
        # Define absolute paths to the input files
        pv_path = os.path.join(script_dir, f'pv_{year}_hourly.csv')
        cons_path = os.path.join(script_dir, f'consumption_{year}_hourly.csv')
        price_path = os.path.join(script_dir, f'price_{year}_hourly.csv')

        # Check if files exist
        if not all(os.path.exists(f) for f in [pv_path, cons_path, price_path]):
            print(f"Skipping {year}: Files not found in {script_dir}")
            continue

        print(f"Processing {year}...")
        
        # Load Data
        pv_orig = pd.read_csv(pv_path)
        cons_orig = pd.read_csv(cons_path)
        price_orig = pd.read_csv(price_path)

        # Create 15-min index (Standardizing to UTC)
        idx = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:45:00', freq='15min', tz='UTC')

        # 1. PV Processing
        pv_orig['datetime'] = pd.to_datetime(pv_orig['datetime']).dt.tz_convert('UTC')
        pv_15 = pv_orig.set_index('datetime').reindex(idx).interpolate().fillna(0)
        pv_15['production_kw'] *= PV_SCALE_FACTOR
        
        # 2. Price Processing
        price_orig['datetime'] = pd.to_datetime(price_orig['datetime']).dt.tz_convert('UTC')
        price_15 = price_orig.set_index('datetime').reindex(idx).ffill()

        # 3. Consumption & Component Logic
        cons_orig['datetime'] = pd.to_datetime(cons_orig['datetime']).dt.tz_convert('UTC')
        cons_15 = cons_orig.set_index('datetime').reindex(idx).ffill()
        
        cons_15['household_general_kwh'] = cons_15['consumption_kwh'] / 4.0
        is_winter = cons_15.index.month.isin([1, 2, 3, 10, 11, 12])
        cons_15['heat_pump_kwh'] = np.where(is_winter & (cons_15.index.hour % 2 == 0), 0.375, 0.01)
        cons_15['ev_load_kwh'] = np.where((cons_15.index.weekday.isin([1, 4])) & (cons_15.index.hour >= 22), 2.75, 0.0)
        cons_15['household_base_kwh'] = 0.05
        cons_15['total_consumption_kwh'] = (cons_15['household_general_kwh'] + cons_15['heat_pump_kwh'] + 
                                            cons_15['ev_load_kwh'] + cons_15['household_base_kwh'])

        # 4. Battery & Grid Simulation
        soc = 7.0 # Start 50%
        soc_l, chg_l, dis_l, exp_l, imp_l = [], [], [], [], []
        
        for i in range(len(cons_15)):
            # Energy Balance: All values in kWh per 15 mins
            net = (pv_15['production_kw'].iloc[i]/4) - cons_15['total_consumption_kwh'].iloc[i]
            
            chg = min(max(net, 0), BATT_MAX_POWER_15MIN, BATT_CAPACITY_KWH - soc)
            soc += chg
            dis = min(max(-net, 0), BATT_MAX_POWER_15MIN, soc)
            soc -= dis
            exp = max(net - chg, 0)
            imp = max(-net - dis, 0)
            
            soc_l.append(soc); chg_l.append(chg); dis_l.append(dis); exp_l.append(exp); imp_l.append(imp)

        cons_15['battery_soc_kwh'], cons_15['battery_charging_kwh'] = soc_l, chg_l
        cons_15['battery_discharging_kwh'] = dis_l
        cons_15['grid_export_kwh'], cons_15['grid_import_kwh'] = exp_l, imp_l

        # Save outputs in the same directory as the script
        pv_15.to_csv(os.path.join(script_dir, f'pv_{year}_dach_15min.csv'))
        price_15.to_csv(os.path.join(script_dir, f'price_{year}_dach_15min.csv'))
        cons_15.to_csv(os.path.join(script_dir, f'consumption_{year}_dach_15min.csv'))
        print(f"✅ Success: 2025 DACH 15min files created in {script_dir}")

if __name__ == "__main__":
    generate_dach_files_final()