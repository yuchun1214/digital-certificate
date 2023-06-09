from pdfrw import PdfReader, PdfWriter, IndirectPdfDict
import sqlite3
import hashlib
import shutil
import os
import datetime

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def set_pdf_info(input_pdf_path, output_pdf_path, information:IndirectPdfDict):
    with open(input_pdf_path, 'rb') as input_pdf_file:
        reader = PdfReader(input_pdf_file)

        # 設定 PDF 的信息
        reader.Info = information
        reader.Info.IssuedTime = str(datetime.datetime.now())


        PdfWriter(output_pdf_path, trailer=reader).write()


def set_pdfs_info(input_pdf_directory, output_pdf_directory, information:dict):
    for file in os.listdir(input_pdf_directory):
        if file.endswith('.pdf'):
            set_pdf_info(os.path.join(input_pdf_directory, file), os.path.join(output_pdf_directory, file), information)



def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as file:
        # Read the file in chunks to support large files
        for chunk in iter(lambda: file.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def insert_hash_value_into_db(hash_value):
    cursor.execute("INSERT INTO hash_table (hash_value) VALUES ('%s')" % hash_value)
    conn.commit()
    pass

def insert_pdfs_info(directory):
    for file in os.listdir(directory):
        if file.endswith('.pdf'):
            hash_value = calculate_file_hash(os.path.join(directory, file))
            try:
                insert_hash_value_into_db(hash_value)
            except sqlite3.IntegrityError:
                print('File name: %s' % file)
                print('Hash value already exists in database: %s' % hash_value)

if __name__ == '__main__':
    # generate test
    for i in range(100):
        shutil.copy('test.pdf', os.path.join('test_data', 'test%d.pdf' % i))


    output_directory = os.path.join('files', '20230610')
    os.makedirs(output_directory, exist_ok=True)

    set_pdfs_info('test_data', output_directory, IndirectPdfDict(IssueDate='2023/06/10', IssuedBy='Eugene Y. Lin'))

    insert_pdfs_info(output_directory)


