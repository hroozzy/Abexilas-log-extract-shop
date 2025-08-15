import csv
import re
from collections import defaultdict
import math

def parse_int_safe(s):
    """Safely parses a string with commas into an integer, returning 0 for empty strings."""
    return int(s.replace(',', '')) if s else 0

# --- Data Parsing ---
parsed_data = []
try:
    # Try reading with utf-8 first, fallback to cp950 if unicode fails (common for some Windows logs)
    try:
        with open("input.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        print("⚠️ 警告：使用 UTF-8 解碼失敗，嘗試使用 CP950 (Big5)...")
        try:
            with open("input.txt", "r", encoding="cp950") as file:
                lines = file.readlines()
        except Exception as e:
            print(f"❌ 錯誤：讀取 input.txt 時發生錯誤 (嘗試 UTF-8 和 CP950 後): {e}")
            exit()
    except FileNotFoundError:
        print("❌ 錯誤：找不到 input.txt 檔案。")
        exit()

except Exception as e: # Catch other potential errors during file opening
    print(f"❌ 錯誤：開啟 input.txt 時發生未預期的錯誤: {e}")
    exit()


i = 0
current_land = "Unknown" # Initialize land name
while i < len(lines):
    line = lines[i].strip()

    # Check for land teleport message and update the current land
    if "Successfully teleported to the spawn of land" in line:
        land_match = re.search(r"Successfully teleported to the spawn of land (\S+)", line)
        if land_match:
            # Clean the land name, removing potential apostrophes
            current_land = land_match.group(1).replace("'", "")
        i += 1
        continue

    if "[CHAT] Owner:" in line:
        # Extract basic info
        owner_match = re.search(r"Owner:\s*(.+)", line)
        owner = owner_match.group(1).strip() if owner_match else "Unknown" # Handle cases where owner name might be missing

        # Ensure we don't go out of bounds when reading subsequent lines
        if i + 2 >= len(lines):
            print(f"⚠️ 警告：Owner '{owner}' 的資料不完整 (缺少 Stock 或 Item 行)，已跳過。")
            i += 1
            continue

        stock_line = lines[i + 1].strip()
        stock_match = re.search(r"Stock:\s*([\d,]+)", stock_line)
        stock = parse_int_safe(stock_match.group(1)) if stock_match else 0

        item_line = lines[i + 2].strip()
        item_match = re.search(r"Item:\s*\[(.+?)\]", item_line)
        # Handle potential color codes like §f
        item = re.sub(r"§[0-9a-fk-or]", "", item_match.group(1).strip()) if item_match else ""


        # Default fields
        repair_cost = ""
        enchantments = []
        buy_price = 0.0 # Use float for prices
        sell_price = 0.0 # Use float for prices

        # Scan downwards until "Sell" or end of related block
        j = i + 3
        while j < len(lines):
            current_line = lines[j].strip()

            # FIX: Check for land teleport message INSIDE the shop block scan as well
            # This catches teleports that happen between two shop listings.
            if "Successfully teleported to the spawn of land" in current_line:
                land_match = re.search(r"Successfully teleported to the spawn of land (\S+)", current_line)
                if land_match:
                    current_land = land_match.group(1).replace("'", "")
                # Don't break, just update the state and continue scanning the shop block

            # Stop condition: another owner starts or end of file
            if "[CHAT] Owner:" in current_line:
                break # Stop processing this item block

            if "Buy" in current_line:
                # Regex updated to handle potential color codes before numbers
                buy_match = re.search(r"Buy\s+§[0-9a-f](\d+)\s+for\s+§[0-9a-f]([\d,]+)\s+Coins", current_line)
                if not buy_match: # Try without color codes if the first pattern failed
                     buy_match = re.search(r"Buy\s+(\d+)\s+for\s+([\d,]+)\s+Coins", current_line)

                if buy_match:
                    buy_qty = int(buy_match.group(1))
                    buy_total = parse_int_safe(buy_match.group(2))
                    # Use float division and handle division by zero
                    buy_price = round(buy_total / buy_qty, 2) if buy_qty != 0 else 0.0

            elif "Sell" in current_line:
                 # Regex updated to handle potential color codes before numbers
                sell_match = re.search(r"Sell\s+§[0-9a-f](\d+)\s+for\s+§[0-9a-f]([\d,]+)\s+Coins", current_line)
                if not sell_match: # Try without color codes
                    sell_match = re.search(r"Sell\s+(\d+)\s+for\s+([\d,]+)\s+Coins", current_line)

                if sell_match:
                    sell_qty = int(sell_match.group(1))
                    sell_total = parse_int_safe(sell_match.group(2))
                    # Use float division and handle division by zero
                    sell_price = round(sell_total / sell_qty, 2) if sell_qty != 0 else 0.0
                    # Don't break here necessarily, other info might follow Sell

            elif "Repair Cost:" in current_line:
                repair_match = re.search(r"Repair Cost:\s*(\d+)", current_line)
                repair_cost = repair_match.group(1) if repair_match else ""

            elif "[CHAT]" in current_line:
                # Extract potential enchantments, excluding known lines
                content = current_line.split("[CHAT]")[-1].strip()
                # Remove color codes from content before checking
                content_no_color = re.sub(r"§[0-9a-fk-or]", "", content)

                # More robust check to avoid adding unrelated chat lines as enchantments
                # Check if it's not a known info line AND matches the enchantment pattern
                is_known_info = any(keyword in current_line for keyword in ["Owner:", "Stock:", "Item:", "Buy", "Sell", "Repair Cost:"])

                # *** Refined Enchantment Regex ***
                # Matches "Words I", "Words II", ..., "Words V" at the end of the line
                enchantment_pattern = r"^[A-Za-z\s']+\s(?:I|II|III|IV|V)$"

                if content_no_color and not is_known_info and re.match(enchantment_pattern, content_no_color):
                    enchantments.append(content_no_color) # Add the version without color codes

            j += 1 # Move to the next line within the item block

        # Sort enchantments for consistent merging key
        enchantment_str = ", ".join(sorted(enchantments))
        # Determine if the item originally had enchantments *before* merging
        has_enchantments = bool(enchantment_str)

        parsed_data.append({
            "owner": owner,
            "stock": stock,
            "item": item,
            "repair_cost": repair_cost,
            "enchantment_str": enchantment_str,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "has_enchantments": has_enchantments, # Store the enchantment status
            "land": current_land # Add the current land
        })
        i = j # Start next search from where the inner loop stopped
    else:
        i += 1 # Move to the next line if it's not an Owner line

# --- Data Processing ---

# 1. Merge identical items (summing stock)
merged_items = defaultdict(int) # Use defaultdict for easier summing
# Store the full data associated with each merge key to retain info like 'has_enchantments'
merged_data_details = {} # Stores the first encountered item_data for a merge_key
merged_item_counts = defaultdict(int) # Stores the count of items merged into a key

for item_data in parsed_data:
    # Create a tuple key for merging, including 'has_enchantments' and prices
    merge_key = (
        item_data["owner"],
        item_data["land"],
        item_data["item"],
        item_data["repair_cost"],
        item_data["enchantment_str"],
        item_data["buy_price"],
        item_data["sell_price"],
        item_data["has_enchantments"] # Include enchantment status in key
    )
    merged_items[merge_key] += item_data["stock"] # Sum the stock
    merged_item_counts[merge_key] += 1 # Increment the count of merged items
    # Store the details (we only need one copy per key, the first one is fine)
    if merge_key not in merged_data_details:
        merged_data_details[merge_key] = item_data


# Convert merged data back to list of dicts and calculate Left Stock
processed_results = []
for merge_key, total_stock in merged_items.items():
    # Unpack the key
    owner, land, item, repair_cost, enchantment_str, buy_price, sell_price, has_enchantments = merge_key

    # 3. Calculate Left Stock based on merged stock and original enchantment status
    base_stock = (54 if has_enchantments else 3456) * merged_item_counts[merge_key]
    left_stock = base_stock - total_stock

    # Calculate the actual repair cost value instead of creating a string
    try:
        # If repair_cost is an empty string, treat it as 0. Otherwise, convert to int.
        cost_val = int(repair_cost) if repair_cost else 0
        # Calculate log2(cost + 1).
        calculated_repair_cost = math.log2(cost_val + 1)
    except (ValueError, TypeError):
        calculated_repair_cost = 0.0 # Fallback

    # Format the repair cost for display: show as integer if not zero, otherwise show empty.
    if calculated_repair_cost > 0:
        repair_cost_display = int(calculated_repair_cost)
    else:
        repair_cost_display = ""

    processed_results.append({
        "Owner": owner,
        "Land": land,
        "Stock": total_stock,
        "Item": item,
        "Repair Cost": repair_cost_display, # Use the formatted value
        "Enchantments": enchantment_str,
        "Buy Price": buy_price,
        "Sell Price": sell_price,
        "Left Stock": left_stock, # Add the new field
        "Merged Count": merged_item_counts[merge_key] # Add the merged count
    })

# 2. Sort items: primarily by Item name, secondarily by Enchantments
processed_results.sort(key=lambda x: (x["Land"], x["Item"], x["Enchantments"]))

# --- CSV Output ---
output_filename = "output_processed.csv"
try:
    with open(output_filename, "w", newline="", encoding="utf-8-sig") as csvfile: # Use utf-8-sig for Excel compatibility
        # Define field names    
        fieldnames = ["Owner", "Land", "Item", "Enchantments", "Stock", "Left Stock", "Buy Price", "Sell Price", "Repair Cost", "Merged Count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader() # Write the header row
        writer.writerows(processed_results) # Write the processed data

    print(f"✅ 轉換與處理完成！請查看 {output_filename}")

except IOError:
    print(f"❌ 錯誤：無法寫入檔案 {output_filename}。請檢查權限或檔案是否被其他程式占用。")
except Exception as e:
    print(f"❌ 處理過程中發生未預期的錯誤：{e}")
