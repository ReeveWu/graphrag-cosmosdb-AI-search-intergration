import PyPDF2

def pdf_to_text(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text

# Example usage:
file_path = "./data/source/employee_handbook.pdf"
extracted_text = pdf_to_text(file_path)

file_name = file_path.split("/")[-1].split(".")[0]

with open(f"./data/input/{file_name}.txt", "w") as file:
    file.write(extracted_text)
