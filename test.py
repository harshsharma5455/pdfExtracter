# if len(extracted_text_dict) < 4 :
#     if len(extracted_text_dict) == 0 :
#         if pdfData["stage_cd"] != "" :
#             extracted_text_dict.append(pdfData)
#     else :
#         if len(extracted_text_dict) == 3:
#             if pdfData["stage_cd"] != "" :
#                 extracted_text_dict.pop(0)
#                 extracted_text_dict.append(pdfData)
#         else :
#             if len(extracted_text_dict) < 3:
#                 if pdfData["stage_cd"] != "" :
#                     extracted_text_dict.append(pdfData)
# if len(extracted_text_dict) == 3:
#     print(f"sequence of text extracted: {extracted_text_dict[0]['route_cd'],extracted_text_dict[1]['route_cd'],extracted_text_dict[2]['route_cd']}")
#
# try:
#
#     if pdfData["stage_cd"] == "" or pdfData["packagedata"][0]["bag_line_no"] == "":
#             if pdfData["stage_cd"] == "" :
# print("-"*33)
# print(f"pdfData is {pdfData}")
# print("-" * 33)
# print(f"previous data is : {extracted_text_dict[2]}")
# print(f"previous data is : {extracted_text_dict[1]}")
# print(f"previous data is : {extracted_text_dict[0]}")
# pdfData = extracted_text_dict[1].update(pdfData)
# print(f"merged pdf is : {pdfData}")
#     return "EmptyPage"
# print(f"next data is {pdfData['packagedata'][0]['bag_sort_zn']}")
# if pdfData["packagedata"][0]["bag_sort_zn"] == "":
#     print(f"pdfData is :{pdfData}")
#     data = extracted_text_dict[1].update(pdfData)
#     print(f"returned pdfData after merging is :{data}")
#     return data

# except Exception as e:
#     print(f"error is {e}")