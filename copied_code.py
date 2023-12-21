import os

# from flask_uploads import UploadSet, configure_uploads, ALL
import pdfplumber
import pdb
import copy
import pandas as pd
previous_text = ""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

extracted_text_dict = []

def extract_text_from_pdf(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        # pdb.set_trace()
        oveflowcsv = []
        bagcsv = []
        totallength = len(pdf.pages)
        finalcsvbags = []
        for i in range(totallength): # totallength
            page = pdf.pages[i]  # Adjust as needed
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
        global previous_text
        previous_text = text
        previous_text = [line.split(' ') for line in previous_text.split('\n') if line.strip() != '']
        return "EmptyPage"
    if "STG" not in text :
        text = [line.split(' ') for line in text.split('\n') if line.strip() != '']
        flag = True

    if not flag :
        table = [line.split(' ') for line in text.split('\n') if line.strip() != '']
    if flag :
        table = previous_text +text
        previous_text = ""
        flag = False
    counter = 0

    # print(f"table is {table}")
    istitle = False
    for lineindex in range(0, 3):
        tablejoin = ' '.join(table[lineindex])
        # print(f"table join is {tablejoin}")
        if table[lineindex][0].count('.') == 2 or table[lineindex][0].count('·') == 2:
            pdfData['stage_cd'] = table[lineindex][0]
            # print("Title:",tablejoin)
            istitle = True
            print(f"table join is : {tablejoin}")

        if table[lineindex][0].count('.') != 2 or table[lineindex][0].count('·') != 2:
            if 'bags' in tablejoin:
                print(f"table join is : {tablejoin}")
                break
            if 'CYCLE' in tablejoin:
                pdfData['station_cd'] = table[lineindex][0]
                pdfData['route_dt'] = ' '.join(table[lineindex][2:6])
                pdfData['cycle_cd'] = ''.join(table[lineindex][7])
                print(f"table join is : {tablejoin}")
                if ':' in tablejoin:
                    print(f"table join is : {tablejoin}")
                    pdfData['loadout_tm'] = ' '.join(table[lineindex][len(table[lineindex]) - 2:])

            if '·' in tablejoin and 'CYCLE' not in tablejoin:

                if '·' in table[lineindex][0]:

                    pdfData['dsp_cd'] = table[lineindex][0]
                    pdfData['van_type'] = ' '.join(table[lineindex][2:])
                    print(f"table join is : {tablejoin}")
                else:

                    pdfData['route_cd'] = table[lineindex][0]
                    pdfData['dsp_cd'] = table[lineindex][1]
                    pdfData['van_type'] = ' '.join(table[lineindex][3:])
                    print(f"table join is : {tablejoin}")
            if "·" not in tablejoin:
                pdfData['route_cd'] = table[lineindex][0]

        if 'bags' in tablejoin:
            pdfData['bags_tot'] = table[lineindex][0]
            pdfData['overflow_tot'] = table[lineindex][2]
            print(f"table join is : {tablejoin}")


    bagfound = False
    for lineindex in range(1, len(table)):
        # print(f"table is :{table}")
        # print(f"pdfData is :{pdfData}")
        # print(f"{pdfData['route_cd']} is {len(table)}")
        tablejoin = ' '.join(table[lineindex])
        # print(f"{pdfData['route_cd']} data : {table}")
        if 'bags' in tablejoin and 'over' in tablejoin:
            # print("bag found in ",pdfData['route_cd'])
            bagfound = True
            pdfData['bags_tot'] = table[lineindex][0]
            pdfData['overflow_tot'] = table[lineindex][2]
            print(f"table join is : {tablejoin}")
            # print(f"pdfData is {pdfData}")
        if "Total" in tablejoin:
            pdfData['packages_tot'] = table[lineindex][2]
            print(f"table join is : {tablejoin}")
            # print("package_tot in ", pdfData['route_cd'])
        if "Commercial" in tablejoin:
            pdfData['commercial_packages_tot'] = table[lineindex][2]
            print(f"table join is : {tablejoin}")
            # print("commercial_package_tot in ", pdfData['route_cd'])

        if pdfData["bags_tot"] == "":
            if 'bags' in tablejoin:
                pdfData['bags_tot'] = table[lineindex][0]
                bagfound = True

        if pdfData["overflow_tot"]:
            if 'over' in tablejoin:
                print(f"value os  pdfData['overflow_tot'] is {pdfData['overflow_tot']}")
                print(f"In if pdfData['overflow_tot'] == '': statement table join is : {tablejoin}")
                pdfData['overflow_tot'] = table[lineindex][2]
                print(f"the value {table[lineindex][2]} is gonna save in pdfData['overflow_tot']")

        if bagfound == True:
            if len(table[lineindex]) == 8:
                copydata = bagspackages.copy()
                overflowdata = {}
                copydata["bag_line_no"] = table[lineindex][0]
                copydata["bag_sort_zn"] = table[lineindex][1]
                copydata["bag_id"] = ''.join(table[lineindex][2:4])
                copydata["bag_pkgs"] = table[lineindex][4]
                copydata["overflow_line_no"] = table[lineindex][5]
                copydata["overflow_sort_zn"] = table[lineindex][6]
                copydata["overflow_pkgs"] = table[lineindex][7]
                pdfData['packagedata'].append(copydata)

            if len(table[lineindex]) == 5:
                copydata = bagspackages.copy()
                copydata["bag_line_no"] = table[lineindex][0]
                copydata["bag_sort_zn"] = table[lineindex][1]
                copydata["bag_id"] = ''.join(table[lineindex][2:4])
                copydata["bag_pkgs"] = table[lineindex][4]
                copydata["overflow_line_no"] = ''
                copydata["overflow_sort_zn"] = ''
                copydata["overflow_pkgs"] = ''
                pdfData['packagedata'].append(copydata)

    print(table)
    print(pdfData)
    return pdfData


if __name__ == '__main__':
    folder_path = input(r'Enter file or folder name : ')
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

            extracted_text = extract_text_from_pdf(pdf_path)
            newfile = filename[0:len(filename) - 4]
            output_filename = os.path.splitext(os.path.basename(pdf_path))[0]
            csv_path = os.getcwd() + '/csvs/' + output_filename + '.csv'
            excelpath = os.getcwd() + '/xlsfiles/' + output_filename + '.xlsx'
            print(f"csv_path : {csv_path}")
            print(f"excelpath : {excelpath}")
            df = pd.DataFrame(extracted_text)
            # Remove rows where 'Sort,' 'Zone,' and 'Pkgs' columns contain the specified values
            df = df[~((df['overflow_line_no'] == 'Sort') & (df['overflow_sort_zn'] == 'Zone') & (df['overflow_pkgs'] == 'Pkgs'))]
            df.to_excel(excelpath, index=False)
            df.to_csv(csv_path, index=False)
            print("Save the file ", excelpath)
            print("Save the file ", csv_path)
        except Exception as e:
            print(e)
    # leasypridictor
