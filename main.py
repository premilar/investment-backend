from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ValidationError
from fastapi.middleware.cors import CORSMiddleware
import openai
from openai import OpenAI
import os
import logging
from io import BytesIO
import PyPDF2
import json




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Question(BaseModel):
    query: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str


@app.post("/api/ask-with-pdf")
async def ask_with_pdf(question: str = Form(...), file: UploadFile = File(...)):
    try:
        # Convert the question from JSON string to a dictionary
        question_dict = json.loads(question)
        # Parse the dictionary into a Pydantic model
        question_data = Question.parse_obj(question_dict)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding failed: {str(e)}")
        raise HTTPException(status_code=400, detail="JSON decode error: " + str(e))
    except ValidationError as e:
        logging.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=422, detail="Invalid question format: " + str(e))

    try:
        # Read PDF file
        content = await file.read()
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Combine extracted text with the user's query
        full_query = f"This is a PDF with data and information relevant to the query:\n{text}\nAnd here is the user query that's asking a question about the PDF:\n{question_data.query}"

        # Query OpenAI with the combined text
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_query}]
        )
        answer = response.choices[0].message.content
        return {"answer": answer}
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask-with-pdf")
async def ask_with_pdf_oldworks(question: str = Form(...), file: UploadFile = File(...)):
    try:
        # Convert the question from JSON string to a dictionary
        question_dict = json.loads(question)
        # Parse the dictionary into a Pydantic model
        question_data = Question.parse_obj(question_dict)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding failed: {str(e)}")
        raise HTTPException(status_code=400, detail="JSON decode error: " + str(e))
    except ValidationError as e:
        logging.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=422, detail="Invalid question format: " + str(e))

    try:
        # Read PDF file
        content = await file.read()
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print("text")
        # Combine extracted text with the user's query
        full_query = f"This is a PDF with data and information relevant to the query:\n{text}\nAnd here is the user query that's asking a question about the PDF:\n{question_data.query}"

        print("full quuery")
        # Query OpenAI with the combined text
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_query}]
        )
        answer = response.choices[0].message.content
        return {"answer": answer}
    except Exception as e:
        print("Error:", str(e))  # Debug: Print the error message
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/openai", response_model=ChatResponse)
async def chat_with_gpt(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message}
            ]
        )
        # print(response)
        # return response.choices[0].message.content
        return ChatResponse(response=response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error processing request: {e}")  # Log the error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


