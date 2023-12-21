import os
import re
import pdfplumber
import pandas as pd
CONTENT = ""
FINAL_DFs = []
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'
def create_df(data:dict):
    bag_data = data["packagedata"]["bag_data"]
    overflow_data = data["packagedata"]["overflow_data"]
    num_rows = max(len(bag_data), len(overflow_data))
    rows = []
    for i in range(num_rows):
        row_data = {
            "stage_cd": data["stage_cd"],
            "route_cd": data["route_cd"],
            "dsp_cd": data["dsp_cd"],
            "van_type": data["van_type"],
            "station_cd": data["station_cd"],
            "route_dt": data["route_dt"],
            "cycle_cd": data["cycle_cd"],
            "loadout_tm": data["loadout_tm"],
            "bags_tot": data["bags_tot"],
            "overflow_tot": data["overflow_tot"],
            "packages_tot": data["packages_tot"],
            "commercial_packages_tot": data["commercial_packages_tot"],
        }
        if i < len(bag_data):
            bag = bag_data[i]
            row_data.update({
                "bag_line_no": bag["bag_line_no"],
                "bag_sort_zn": bag["bag_sort_zn"],
                "bag_id": bag["bag_id"],
                "bag_pkgs": bag["bag_pkgs"],
            })
        else:
            row_data.update({
                "bag_line_no": "",
                "bag_sort_zn": "",
                "bag_id": "",
                "bag_pkgs": "",
            })
        if i < len(overflow_data):
            overflow = overflow_data[i]
            row_data.update({
                "overflow_line_no": overflow["overflow_line_no"],
                "overflow_sort_zn": overflow["overflow_sort_zn"],
                "overflow_pkgs": overflow["overflow_pkgs"],
            })
        else:
            row_data.update({
                "overflow_line_no": "",
                "overflow_sort_zn": "",
                "overflow_pkgs": "",
            })
        rows.append(row_data)
    adf = pd.DataFrame(rows)
    return adf
def re_match(regex:str,text):
    matches = re.compile(regex).findall(text)
    return matches[0] if len(matches)!=0 else ""
def re_number_search(regex:str,text):
    match = re.search(regex, text, re.IGNORECASE)
    if match:
        out_string = match.group()
        counts = re.findall(r'\b\d+\b', out_string)
        return counts
    return None
def extract_table(page):
    pdfData = {"stage_cd": '',"route_cd": '',"dsp_cd": '',"van_type": '',"station_cd": '',"route_dt": '',"cycle_cd": '',"loadout_tm": '',"bags_tot": '',"overflow_tot": '',"packages_tot": '',"commercial_packages_tot": '',"packagedata": {"bag_data": [],"overflow_data": []},
    }
    global CONTENT
    text = CONTENT + page.extract_text() if len(CONTENT) > 1 else page.extract_text()
    pdfData["stage_cd"] = re_match(r"\b[A-Z]+\.[A-Z]+\.\d+\b",text)
    pdfData["route_cd"] = re_match(r"\b[A-Z]{2}\d+\b",text)
    pdfData["dsp_cd"] = re_match(r"[A-Z]{4}",text) #TODO: Correct Regex
    pdfData["van_type"] = re_match(r"[A-Z]{4}.*",text).split("·")[1]
    check_station_n_date = re.compile(r'.*· .*· .*').findall(text)
    st_list = check_station_n_date[0].replace('Â', '').split("·")
    if len(st_list)==4:
        pdfData["station_cd"] = st_list[0].strip()
        pdfData["route_dt"] = st_list[1].strip()
        pdfData["cycle_cd"] = st_list[2].strip()
        pdfData["loadout_tm"] = st_list[-1].strip()
    elif len(st_list)==3: #TODO: OPTIMISTIC METHOD COULD BE FOUND
        pdfData["station_cd"] = st_list[0].strip()
        pdfData["route_dt"] = st_list[1].strip()
        pdfData["cycle_cd"] = st_list[2].strip()
        pdfData["loadout_tm"] = ""
    '''Now find bag total and overflow total'''
    bag_p = r'.*bags.*'
    bag_match = re.search(bag_p, text, re.IGNORECASE)
    if bag_match:
        CONTENT= "" #as we found bag data so CONTENT should have nothing
        bag_string = bag_match.group()
        if "over" in bag_string:
            counts = re.findall(r'\b\d+\b', bag_string)
            pdfData["bags_tot"] = counts[0]
            pdfData["overflow_tot"] = counts[1]
        else:
            counts = re.findall(r'\b\d+\b', bag_string)
            pdfData["bags_tot"] = counts[0] #TODO: IMPLEMENT THE OVERFLOW IF NO OVER IN bag_string
            over_p = r'.*over.*'
            overflow_match = re.search(over_p, text, re.IGNORECASE)
            overflow_string = overflow_match.group()
            counts = re.findall(r'\b\d+\b', overflow_string)
            pdfData["overflow_tot"] = counts[0]
    else:
        #As bags not found so data may be in next page so globalize text and function in next page
        CONTENT = text+"\n"
        return None
    #Let's find package total and Commercial Packages total
    pdfData["packages_tot"] = re_number_search(r'.*TOTAL.*',text)[0]
    is_commercial = re_number_search(r'.*Commercial.*', text)
    pdfData["commercial_packages_tot"] = is_commercial[0] if is_commercial else ""
    bag_regex = r"(\d+)\s([A-Z]-\d+\.\d[A-Z])\s(\w+)\s(\d+)\s(\d+)"
    bag_matches = re.compile(bag_regex).findall(text)
    for match in bag_matches:
        bag_data = {}
        bag_data["bag_line_no"], bag_data["bag_sort_zn"] = match[:2]
        bag_data["bag_id"] = match[2] + " " + match[3]
        bag_data["bag_pkgs"] = match[-1]
        pdfData['packagedata']['bag_data'].append(bag_data)
    overflow_regex = r"(\d+)\s([A-Z]-\d+\.\d\w)\s(\d+)"
    overflow_matches = re.compile(overflow_regex).findall(text)
    for match in overflow_matches:
        overflow_data = {}
        overflow_data["overflow_line_no"],overflow_data["overflow_sort_zn"],overflow_data["overflow_pkgs"] = match
        pdfData['packagedata']['overflow_data'].append(overflow_data)
    return pdfData

def create_df_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"TOTAL PAGES {total_pages}")
        for i in range(total_pages-1):
            page = pdf.pages[i]
            with open(f"pages/page{i}.text", "w", encoding="utf-8") as file:
                file.write(page.extract_text())
            if page.extract_text() != '':
                tabular_data = extract_table(page)
                if tabular_data:
                    adf = create_df(tabular_data)
                    FINAL_DFs.append(adf)
                    final_combined_df = pd.concat(FINAL_DFs, ignore_index=True)
                    # final_combined_df.to_csv("output_combined.csv", index=False)
                else:
                    continue
        return final_combined_df


if __name__ == '__main__':
    folder_path = input(r'Enter file or folder name : ')
    csv_dir = 'csvs'
    xls_dir = 'xlsfiles'
    pages_dir = 'pages'

    # Check if the directories exist, and create them if necessary
    if not os.path.exists(csv_dir) or not os.path.exists(xls_dir) or not os.path.exists(pages_dir):
        os.makedirs(csv_dir, exist_ok=True)
        os.makedirs(xls_dir, exist_ok=True)
        os.makedirs(pages_dir,exist_ok=True)
    else:
        pass
    if os.path.exists(folder_path):
        if os.path.isfile(folder_path):
            # files =  [os.path.join(folder_path)]
            files = [folder_path]  # Use a list with the single file
        elif os.path.isdir(folder_path):
            # files =  [filename for filename in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, filename))]
            files = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if
                     os.path.isfile(os.path.join(folder_path, filename))]
    else:
        files = ''
        print('incorrect path, please enter correct path without quotes')
    print("List of files:", files)
    if 'files' in locals():
        # check only for pdf files
        pdfs = [x for x in files if x.endswith('.pdf')]
    for pdf_path in pdfs:
        try:
            # print('file name', pdf_path)
            filename = pdf_path
            dframe = create_df_from_pdf(pdf_path)
            newfile = filename[0:len(filename) - 4]
            output_filename = os.path.splitext(os.path.basename(pdf_path))[0]
            csv_path = os.getcwd() + '/csvs/' + output_filename + '.csv'
            excelpath = os.getcwd() + '/xlsfiles/' + output_filename + '.xlsx'
            print(f"csv_path : {csv_path}")
            print(f"excelpath : {excelpath}")
            dframe.to_excel(excelpath, index=False)
            dframe.to_csv(csv_path, index=False)
            print("Save the file ", excelpath)
            print("Save the file ", csv_path)
        except Exception as e:
            print(e)

