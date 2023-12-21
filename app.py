import os
import pdfplumber
import pandas as pd
import re
previous_text = ""
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

extracted_text_dict = []

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:

        totallength = len(pdf.pages)
        finalcsvbags = []
        for i in range(totallength): # totallength
            page = pdf.pages[i]  # Adjust as needed
            with open(f"pages/page{i}.text", "w", encoding="utf-8") as file:
                file.write(page.extract_text())
            if page.extract_text() != '':
                totaldata = extract_table(page)
                if totaldata == "EmptyPage":
                    continue
                mainobject = totaldata.copy()
                del mainobject["packagedata"]
                for bag in totaldata['packagedata']:
                    bagobj = mainobject.copy()
                    bagobj['bag_line_no'] = bag['bag_line_no']
                    bagobj['bag_sort_zn'] = bag['bag_sort_zn']
                    bagobj['bag_id'] = bag['bag_id']
                    bagobj['bag_pkgs'] = bag['bag_pkgs']
                    bagobj['overflow_line_no'] = bag['overflow_line_no']
                    bagobj['overflow_sort_zn'] = bag['overflow_sort_zn']
                    bagobj['overflow_pkgs'] = bag['overflow_pkgs']
                    finalcsvbags.append(bagobj)
        print(f"final csv bag is : {finalcsvbags}")

        return finalcsvbags


def extract_table(page):
    flag = False
    pdfData = {
        "stage_cd": '',
        "route_cd": '',
        "dsp_cd": '',
        "van_type": '',
        "station_cd": '',
        "route_dt": '',
        "cycle_cd": '',
        "loadout_tm": '',
        "bags_tot": '',
        "overflow_tot": '',
        "packages_tot": '',
        "commercial_packages_tot": '',
        "packagedata": [],
    }
    bagspackages = {
        "bag_line_no": '',
        "bag_sort_zn": '',
        "bag_id": '',
        "bag_pkgs": '',
        "overflow_line_no": '',
        "overflow_sort_zn": '',
        "overflow_pkgs": '',
    }

    text = page.extract_text()

    if "bags" not in text:
        global previous_text, table
        previous_text = text
        previous_text = [line.split(' ') for line in previous_text.split('\n') if line.strip() != '']
        return "EmptyPage"
    if "STG" not in text :
        text = [line.split(' ') for line in text.split('\n') if line.strip() != '']
        flag = True

    if not flag :
        table = [line.split(' ') for line in text.split('\n') if line.strip() != '']
    elif flag :
        table = list(previous_text) +text
        previous_text = ""
        flag = False


    counter = 0
    bagfound = False
    istitle = False
    for ind in range(2,len(table)-1):
        tablejoin = ' '.join(table[ind])
        """        
        the for loop will iterate the first three indices of table list ,
        coz the first three column contains the header data.
        and the instance sub lists are: 
        
            ['STG.B.2']
            ['CX198', 'LDCD', '·', 'Standard', 'Parcel', '-', 'Extra', 'Large', 'Van', '-', 'US']
            ['DPP7', '·', 'THU,', 'DEC', '7,', '2023', '·', 'CYCLE_1', '·11:40AM']
            
        Here, the tablejoin will contain the following strings : -
        
            STG.B.2
            CX198 LDCD · Standard Parcel - Extra Large Van - US
            DPP7 · THU, DEC 7, 2023 · CYCLE_1 ·11:40AM
        and its type is off course "string"
        
        """
        # Patterns
        bags_pattern = "\d\sbags"
        over_pattern = "\d\sover"
        total_packages = "Total\sPackages\s\d+"
        commercial_packages = "Commercial\sPackages\s\d+"

        bags = re.findall(bags_pattern,tablejoin)
        if bags :
            int_pattern = "\d+"
            print(bags)
            num_bag = re.findall(int_pattern,bags[0])
            pdfData['bags_tot'] = num_bag[0]
            bagfound = True

        overflow = re.findall(over_pattern,tablejoin)
        if overflow :
            int_pattern = "\d+"
            num_overflow = re.findall(int_pattern, overflow[0])
            pdfData['overflow_tot'] = num_overflow[0]

        package_tot = re.findall(total_packages,tablejoin)
        if package_tot :
            int_pattern = "\d+"
            num_package = re.findall(int_pattern,package_tot[0])
            pdfData["packages_tot"] = num_package[0]

        comm_pack = re.findall(commercial_packages, tablejoin)
        if comm_pack :
            int_pattern = "\d+"
            num_comm = re.findall(int_pattern, comm_pack[0])
            pdfData["commercial_packages_tot"] = num_comm[0]

        if bagfound == True:
            if len(table[ind]) == 8:
                copydata = bagspackages.copy()
                overflowdata = {}
                copydata["bag_line_no"] = table[ind][0]
                copydata["bag_sort_zn"] = table[ind][1]
                copydata["bag_id"] = ''.join(table[ind][2:4])
                copydata["bag_pkgs"] = table[ind][4]
                copydata["overflow_line_no"] = table[ind][5]
                copydata["overflow_sort_zn"] = table[ind][6]
                copydata["overflow_pkgs"] = table[ind][7]
                pdfData['packagedata'].append(copydata)

            if len(table[ind]) == 5:
                copydata = bagspackages.copy()
                copydata["bag_line_no"] = table[ind][0]
                copydata["bag_sort_zn"] = table[ind][1]
                copydata["bag_id"] = ''.join(table[ind][2:4])
                copydata["bag_pkgs"] = table[ind][4]
                copydata["overflow_line_no"] = ''
                copydata["overflow_sort_zn"] = ''
                copydata["overflow_pkgs"] = ''
                pdfData['packagedata'].append(copydata)



    # For Header Data only

    for ind in range(3):
        tablejoin = ' '.join(table[ind])
        stg_pattern = "STG\.[A-Z]\.\d+"  #STG.G.97
        route_pattern = "CX\d+"          #CX454
        dsp_cd = "[A-Z]{4}"              #LDCD
        station_cd = "[A-Z]{3}\d+"
        route_date_pattern = r"\b([A-Za-z]+, [A-Za-z]+ \d+, \d{4})\b"
        loadout_time_pattern = r"\b(\d{2}:\d{2} [APMapm]+)\b"

        stg = re.findall(stg_pattern,tablejoin)
        if stg :
            pdfData["stage_cd"] = stg[0]

        route = re.findall(route_pattern,tablejoin)
        if route:
            pdfData["route_cd"] = route[0]

        dsp = re.findall(dsp_cd,tablejoin)
        if dsp :
            if dsp != ['CYCL'] :
                if dsp != ['MEDI'] and  dsp != 'MEDI':
                    if dsp != []:
                        pdfData["dsp_cd"] = dsp[0]
                        van_ind = int(tablejoin.index(dsp[0])) + 7
                        pdfData["van_type"] = tablejoin[van_ind:]

        station = re.findall(station_cd,tablejoin)
        if station :
            pdfData["station_cd"] = station[0]

        routedt = re.search(route_date_pattern, tablejoin)
        # Check if a match is found
        if routedt:
            # Get the matched date value
            matched_date = routedt.group(1)
            pdfData["route_dt"] = matched_date

        loadout_tm_match = re.search(loadout_time_pattern, tablejoin)

        if loadout_tm_match:
            matched_time = loadout_tm_match.group(1)
            pdfData["loadout_tm"] = matched_time

        cycle = r'\b\w*cycle\w*\b'

        # Use re.findall with the re.IGNORECASE flag to find all matches in the input string
        cycle_cd = re.findall(cycle, tablejoin, flags=re.IGNORECASE)
        if cycle_cd :
            pdfData["cycle_cd"] = cycle_cd[0]

        if pdfData["overflow_tot"] == "":
            if 'over' in tablejoin:
                if any("over" in element for element in table[ind]):
                    over_index = next((index for index, element in enumerate(table[ind]) if "over" in element), None)
                    pdfData['overflow_tot'] = table[ind][over_index-1]

    print(pdfData)
    return pdfData


if __name__ == '__main__':
    folder_path = input(r'Enter file or folder name : ')
    if os.path.exists(folder_path):
        if os.path.isfile(folder_path):
            files = [folder_path]  # Use a list with the single file
        elif os.path.isdir(folder_path):
            files = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if
                     os.path.isfile(os.path.join(folder_path, filename))]

    else:
        files = ''
        print('incorrect path, please enter correct path without quotes')
    print("List of files:", files)

    #  create folder for pages storage
    path = os.getcwd()
    folder_path = path + "/extract"
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    if 'files' in locals():
        # check only for pdf files
        pdfs = [x for x in files if x.endswith('.pdf')]

    for pdf_path in pdfs:

        filename = pdf_path

        extracted_text = extract_text_from_pdf(pdf_path)
        output_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        csv_path = os.getcwd() + '/csvs/' + output_filename + '.csv'
        excelpath = os.getcwd() + '/xlsfiles/' + output_filename + '.xlsx'
        print(f"csv_path : {csv_path}")
        print(f"excelpath : {excelpath}")
        df = pd.DataFrame(extracted_text)
        # Remove rows where 'Sort,' 'Zone,' and 'Pkgs' columns contain the specified values
        if "overflw_line_no" in df.columns:
            if (df['overflow_line_no'] == "Sort").any():
                df = df[~((df['overflow_line_no'] == 'Sort') & (df['overflow_sort_zn'] == 'Zone') & (df['overflow_pkgs'] == 'Pkgs'))]

        if "dsp_cd" in df.columns:
            df["dsp_cd"] = df["dsp_cd"].str.replace('.','')
            print(f"removed empty spaces {df['dsp_cd']}")

        df.to_excel(excelpath, index=False)
        df.to_csv(csv_path, index=False)
        print("Save the file ", excelpath)
        print("Save the file ", csv_path)

    # leasypridictor
