import csv

def load_mapping(mapping_file):
    mapping = {}
    with open(mapping_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')  # 也可改為 ',' if your file is comma-separated
        for row in reader:
            if len(row) >= 2:
                mapping[row[0]] = row[1]
    return mapping

def apply_mapping_to_csv(input_csv, output_csv, mapping):
    with open(input_csv, newline='', encoding='utf-8') as infile, \
         open(output_csv, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            new_row = [replace_all(cell, mapping) for cell in row]
            writer.writerow(new_row)

def replace_all(text, mapping):
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text

# 設定檔案名稱
mapping_file = 'mapping.csv'
input_csv = 'output_processed.csv'
output_csv = 'changed.csv'

# 讀取對照表並處理資料
mapping = load_mapping(mapping_file)
apply_mapping_to_csv(input_csv, output_csv, mapping)

print("✅ 替換完成！輸出檔案為：", output_csv)
