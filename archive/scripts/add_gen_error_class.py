with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    text = f.read()

target = "from fastapi import FastAPI, Request, HTTPException, UploadFile, File"
replacement = """from fastapi import FastAPI, Request, HTTPException, UploadFile, File

class GenerationValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open("web_ec2/main.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added GenerationValidationError class!")
else:
    print("target not found")
