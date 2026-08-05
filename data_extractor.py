import os
import xml.etree.ElementTree as ET

# เปลี่ยน path นี้ให้เป็น path จริงในเครื่องคุณหากต้องการรันจากที่อื่น
# หรือถ้าเอาสคริปต์นี้ไปวางในโฟลเดอร์ไหน ให้รันในโฟลเดอร์นั้นได้เลย
target_dir = os.getcwd()

def get_bin_info(directory, xdf_name):
    """ค้นหาไฟล์ .bin ที่คู่กันเพื่อดึงขนาดไฟล์"""
    base_name = os.path.splitext(xdf_name)[0].lower()
    for f in os.listdir(directory):
        if f.lower().endswith(".bin") and base_name in f.lower():
            size_kb = os.path.getsize(os.path.join(directory, f)) // 1024
            return f"{size_kb}KB"
    return "-"

def parse_xdf_offset(file_path):
    """ดึงค่า Offset จากไฟล์ XDF"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for table in root.findall('.//XDFTABLE'):
            axis = table.find('.//XDFAXIS[@id="z"]')
            if axis is not None:
                data = axis.find('EMBEDDEDDATA')
                if data is not None:
                    return data.get('mmedaddress', '-')
        return "-"
    except:
        return "-"

# พิมพ์หัวตาราง
print("┌" + "─"*28 + "┬" + "─"*15 + "┬" + "─"*12 + "┬" + "─"*16 + "┬" + "─"*10 + "┬" + "─"*7 + "┐")
print(f"│ {'Type Motor':<26} │ {'Part Number':<13} │ {'ECM ID':<10} │ {'Start(Offset)':<14} │ {'Chksum':<8} │ {'Size':<5} │")
print("├" + "─"*28 + "┼" + "─"*15 + "┼" + "─"*12 + "┼" + "─"*16 + "┼" + "─"*10 + "┼" + "─"*7 + "┤")

for root, dirs, files in os.walk(target_dir):
    # ข้ามโฟลเดอร์ชื่อ "ไฟล์ โม"
    if "ไฟล์ โม" in dirs: dirs.remove("ไฟล์ โม")
    
    for file in files:
        if file.endswith(".xdf"):
            # ดึงข้อมูลเบื้องต้น
            folder_name = os.path.basename(root)
            motor = (folder_name[:25] + '...') if len(folder_name) > 25 else folder_name
            part = file.replace(".xdf", "").replace(" ", "")
            offset = parse_xdf_offset(os.path.join(root, file))
            size = get_bin_info(root, file)
            
            print(f"│ {motor:<26} │ {part:<13} │ {'-':<10} │ {offset:<14} │ {'-':<8} │ {size:<5} │")

print("└" + "─"*28 + "┴" + "─"*15 + "┴" + "─"*12 + "┴" + "─"*16 + "┴" + "─"*10 + "┴" + "─"*7 + "┘")
