# app/evaluation/judges.py

import re


def extract_score(text):
    match = re.search(r"\d*\.?\d+", text)

    if match:
        return float(match.group())

    return 0.0


def evaluate_faithfulness(
    llm,
    question,
    context,
    answer
):
    
    prompt = f"""
You are a RAG evaluator.

Question:
{question}

Retrieved Context:
{context}

Generated Answer:
{answer}

Task:
Check whether the answer is supported by the retrieved context.

Scoring:
Return ONLY the score between 0.0 and 1.0.
"""

    response = llm.invoke(prompt)
    print("Faithfulness Evaluation Response:", response.content)
    return extract_score(response.content)

def evaluate_answer_relevance(
    llm,
    question,
    answer
):

    prompt = f"""
You are an evaluator.

Question:
{question}

Answer:
{answer}

Task:
Check how well the answer addresses the question.
Scoring:
Return ONLY the score between 0.0 and 1.0.
"""

    response = llm.invoke(prompt)
    print("Answer Relevance Evaluation Response:", response.content)
    return extract_score(response.content)