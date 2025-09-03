from config import Settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

def review_with_llm(diff: str):
    # Initialize Gemini chat model
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # or gemini-1.5-pro for stronger analysis
        google_api_key=Settings.GEMINI_API_KEY,
        temperature=0.3,
    )

    # Build a structured prompt
    template = """
    You are a senior code reviewer.
    Review the following PR diff and provide feedback on:
    - Code bugs
    - Security issues
    - Readability and style
    - Suggestions for improvement

    Diff:
    {diff}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # Run chain
    chain = prompt | llm
    response = chain.invoke({"diff": diff})

    return response.content
