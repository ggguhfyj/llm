from openai import OpenAI
from dotenv import load_dotenv
import pymupdf
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def pdf_to_text(pdf_file_path: str):
    doc = pymupdf.open(pdf_file_path)
    header_height = 80
    footer_height = 80

    full_text = ''
    for page in doc:
        rect = page.rect
        header = page.get_text(clip=(0,0,rect.width,header_height))
        footer = page.get_text(clip=(0,rect.height - footer_height,rect.width,rect.height))
        text = page.get_text(clip=(0,header_height,rect.width,rect.height-footer_height))

        full_text += text + '\n--------------------------------------------------------------\n'

    pdf_file_name = os.path.basename(pdf_file_path)
    pdf_file_name = os.path.splitext(pdf_file_name)[0]


    txt_file_path = f"data/{pdf_file_name}_with_preprocessing.txt"
    with open(txt_file_path,'w',encoding='utf-8') as f:
        f.write(full_text)
    return txt_file_path
def summarize_txt(file_path: str):
    with open(file_path,'r',encoding='utf-8') as f:
        txt = f.read()
    system_prompt = f'''
        넌 다음 글을 요약하는 봇이다. 저자의 문제인식과 주장을 파악하고 주요ㅕ내용을 요약하라

        작성 포맷:

        #재목

        ##저자의 문제 인식과 주장(15문장 이내)

        ##저자 소개

        ==============이하 택스트==================

        {txt}
    '''
    print(system_prompt)
    print('---------------------------')

    response = client.chat.completions.create(
        model= "gpt-4o",
        temperature=0.1,
        messages=[{"role":"system","content":system_prompt}],    
        )
    return response.choices[0].message.content

pdf_file_path = r"C:\llm\data\과정기반 작물모형을 이용한 웹 기반 밀 재배관리 의사결정 지원시스템 설계 및 구축.pdf"

txt_file_path = pdf_to_text(pdf_file_path);

summary = summarize_txt(txt_file_path);

print(summary)