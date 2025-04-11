import pandas as pd
from datetime import datetime, timedelta
import re
import requests
from flask import request, jsonify

# Assuming these are imported from a separate data.py file
from data import get_db_connection, FlaskLogger

# Gemini API configuration (using the free tier model: gemini-2.0-flash)
GEMINI_API_URL = "https://api.gemini.com/v1/models/gemini-2.0-flash/generate"  # Adjust URL based on actual Gemini API docs
GEMINI_API_KEY = "AIzaSyBavRghc9aiYkpeh2i18PM4vMluCUNqg4k"  # Replace with your actual Gemini API key

# Helper function to call Gemini API and generate SQL query
def generate_sql_query(question):
    """
    Calls the Gemini API to generate an SQL query based on the user's question.
    Assumes the database table is 'sales_data' with columns: brand, category, size, color, sales_qty, purchase_qty, created_at.
    """
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": (
            "Generate a valid SQL query to answer the following question based on the 'sales_data' table. "
            "The table has columns: brand, category, size, color, sales_qty (integer), purchase_qty (integer), created_at (timestamp). "
            "Do not include 'grand total' in brand. Return the query in plain text without explanations or markdown: "
            f"{question}"
        ),
        "max_tokens": 200,  # Adjust based on API limits and query complexity
        "temperature": 0.5  # Lower temperature for more deterministic output
    }
    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            generated_text = response.json().get("generated_text", "").strip()
            if generated_text:
                # Basic validation to ensure it looks like an SQL query
                if "SELECT" in generated_text.upper() and "FROM" in generated_text.upper():
                    return generated_text
                else:
                    return None
            return None
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return None

# Retrieve and generate response for chatbot
def retrieve_data(question, logger):
    """
    Retrieves data by generating an SQL query via Gemini API and executing it.
    Returns a formatted HTML response or an error message.
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection failed")
        return "Database connection failed."

    cursor = conn.cursor()
    question_lower = ' '.join(question.lower().split())  # Normalize spaces
    logger.info(f"Processing chatbot question: {question_lower}")

    try:
        # Generate SQL query using Gemini API
        sql_query = generate_sql_query(question_lower)
        if not sql_query:
            logger.warning(f"Failed to generate a valid SQL query for: {question_lower}")
            return "Sorry, I couldn't generate a valid query for your question. Please try rephrasing it."

        logger.info(f"Generated SQL query: {sql_query}")

        # Execute the generated SQL query
        try:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            if not results:
                logger.info("No data found for the query")
                return f"No data found for your question: '{question}'."
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return f"Error executing query: {e}. Please refine your question."

        # Dynamically handle the query results
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(results, columns=columns)

        # Basic data cleaning
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

        # Format the response as an HTML table
        response = f"<h3>Results for: {question}</h3>"
        response += df.to_html(index=False, classes="data-table", na_rep="N/A")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in retrieve_data: {e}")
        return f"An unexpected error occurred: {e}"
    finally:
        cursor.close()
        conn.close()

# Chatbot route handler
def chat():
    """
    Flask route handler for chatbot requests.
    Accepts JSON input with a 'question' field and returns a JSON response with the answer.
    """
    log_output = FlaskLogger()
    data = request.get_json(silent=True)
    if data is None:
        log_output.error("Received non-JSON request")
        return jsonify({"text": "Invalid request format. Please send JSON data.", "logs": log_output.get_logs()}), 400

    question = data.get("question", "").strip()
    log_output.info(f"Received chatbot question: {question}")
    if not question:
        log_output.error("No question provided")
        return jsonify({"text": "Please provide a question.", "logs": log_output.get_logs()}), 400

    answer = retrieve_data(question, log_output)
    return jsonify({"text": answer, "logs": log_output.get_logs()})

# Helper function for sell-out days (kept for potential future use, though not directly used now)
def calculate_days_to_sell_out(sales_qty, purchase_qty, days_since):
    if sales_qty == 0 or purchase_qty == 0 or days_since == 0:
        return "N/A"
    remaining = purchase_qty - sales_qty
    if remaining <= 0:
        return "Sold out"
    daily_rate = sales_qty / days_since
    if daily_rate <= 0:
        return "N/A"
    return round(remaining / daily_rate)

# Helper function to extract category (kept for potential future use, though not directly used now)
def extract_category(question):
    words = question.lower().split()
    try:
        if "in" in words:
            idx = words.index("in") + 1
            category_words = []
            for i in range(idx, len(words)):
                if words[i] in ["daily", "historical", "trend"]:
                    break
                category_words.append(words[i])
            return " ".join(category_words).capitalize()
        elif "for" in words:
            idx = words.index("for") + 1
            category_words = []
            for i in range(idx, len(words)):
                if words[i] in ["daily", "historical", "trend"]:
                    break
                category_words.append(words[i])
            return " ".join(category_words).capitalize()
    except IndexError:
        pass
    return None