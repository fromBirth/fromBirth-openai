import json

# 기존 JSONL 파일을 읽고, 새 형식으로 변환
input_file = "C:/Users/bsm/Desktop/course/Python/files/fine-tuning-advice.jsonl"
output_file = "C:/Users/bsm/Desktop/course/Python/files/fine-tuning-chat-format.jsonl"

# with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
#     for line in infile:
#         entry = json.loads(line)
#         # 기존 형식에서 새로운 챗 형식으로 변환
#         chat_entry = {
#             "messages": [
#                 {"role": "user", "content": entry["prompt"]},
#                 {"role": "assistant", "content": entry["completion"]}
#             ]
#         }
#         json.dump(chat_entry, outfile, ensure_ascii=False)
#         outfile.write("\n")


