
import psycopg2
from flask import Flask, request, render_template
from datetime import datetime, timedelta
import pandas as pd
import os

# Database connection (replace with your credentials)
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="ep-steep-smoke-a8y63192-pooler.eastus2.azure.neon.tech",
            database="neondb",
            user="neondb_owner",
            password="npg_KB7gQX9tyron",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Error: {e}")
        return None

# Helper function for sell-out days
def calculate_days_to_sell_out(sales_qty, purchase_qty, days_since):
    if sales_qty == 0 or purchase_qty == 0:
        return "N/A"
    remaining = purchase_qty - sales_qty
    if remaining <= 0:
        return "Sold out"
    daily_rate = sales_qty / days_since
    return round(remaining / daily_rate) if daily_rate > 0 else "N/A"

# Helper function to extract category from question
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

# Retrieve and generate response
def retrieve_data(question):
    conn = get_db_connection()
    if not conn:
        return "Database connection failed."
    
    cursor = conn.cursor()
    question_lower = question.lower()

    try:
        # Question 1: Notify when items reach 75% and 50% sold
        if "reach 75% and 50% sold" in question_lower:
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE purchase_qty > 0 AND LOWER(brand) != 'grand total'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                return "No data found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
            df['percent_sold'] = (df['sales_qty'] / df['purchase_qty']) * 100
            df['days_since'] = (datetime.now() - df['created_at']).dt.days
            df['days_to_sell_out'] = df.apply(lambda row: calculate_days_to_sell_out(row['sales_qty'], row['purchase_qty'], row['days_since']), axis=1)
            filtered = df[(df['percent_sold'] >= 50) & (df['percent_sold'] <= 75)]
            if filtered.empty:
                return "No items between 50% and 75% sold."
            return filtered[['brand', 'category', 'size', 'color', 'percent_sold', 'days_to_sell_out']].to_html(index=False, classes="data-table")

        # Question 2: Best-selling items by specific period(s)
        elif "best-selling items" in question_lower:
            periods = {
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90
            }
            requested_periods = []
            
            for period in periods.keys():
                if period in question_lower:
                    requested_periods.append(period)
            
            if not requested_periods:
                return "Please specify a period (weekly, monthly, or quarterly) for best-selling items."
            
            output = ""
            for period_name in requested_periods:
                days = periods[period_name]
                query = """
                    SELECT brand, category, size, color, SUM(sales_qty) as total_sales
                    FROM sales_data
                    WHERE created_at >= %s AND LOWER(brand) != 'grand total'
                    GROUP BY brand, category, size, color
                    ORDER BY total_sales DESC
                    LIMIT 5
                """
                cursor.execute(query, (datetime.now() - timedelta(days=days),))
                results = cursor.fetchall()
                if results:
                    df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
                    output += f"<h3>Top 5 Best-Selling Items ({period_name.capitalize()})</h3>"
                    output += df.to_html(index=False, classes="data-table")
                else:
                    output += f"<h3>No best-selling items found for {period_name.capitalize()} period.</h3>"
            
            return output if output else "No best-selling items found for the specified period(s)."

        # Question 3: Track non-moving products
        elif "non-moving products" in question_lower:
            query = """
                SELECT brand, category, size, color, purchase_qty, created_at
                FROM sales_data
                WHERE sales_qty = 0 AND created_at >= %s AND LOWER(brand) != 'grand total'
            """
            one_month_ago = datetime.now() - timedelta(days=30)
            cursor.execute(query, (one_month_ago,))
            results = cursor.fetchall()
            if not results:
                return "No non-moving products found."
            df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "purchase_qty", "created_at"])
            df['age_days'] = (datetime.now() - df['created_at']).dt.days
            return df[['brand', 'category', 'size', 'color', 'purchase_qty', 'age_days']].to_html(index=False, classes="data-table")

        # Question 4: Identify slow-moving sizes within specific categories
        elif "slow-moving sizes" in question_lower:
            if "daily" in question_lower:
                date_str = datetime.now().strftime("%y%m%d")
                try:
                    df = pd.read_excel(f"processed_data/salesninventory_{date_str}.xlsx")
                    df = df[df['Brand'].str.lower() != "grand total"]
                    date_col = "date"
                    sales_col = "SalesQty"
                    purchase_col = "PurchaseQty"
                    category_col = "Category"
                    size_col = "Size"
                except FileNotFoundError:
                    return "Daily data file not found."
            elif "historical" in question_lower or "trend" in question_lower:
                query = """
                    SELECT brand, category, size, color, sales_qty, purchase_qty, month
                    FROM sales_data
                    WHERE LOWER(brand) != 'grand total'
                """
                cursor.execute(query)
                results = cursor.fetchall()
                if not results:
                    return "No historical data found."
                df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "month"])
                date_col = "month"
                sales_col = "sales_qty"
                purchase_col = "purchase_qty"
                category_col = "category"
                size_col = "size"
            else:
                try:
                    df = pd.read_excel("processed_data/master_summary.xlsx")
                    df = df[df['Brand'].str.lower() != "grand total"]
                    date_col = "date"
                    sales_col = "SalesQty"
                    purchase_col = "PurchaseQty"
                    category_col = "Category"
                    size_col = "Size"
                except FileNotFoundError:
                    return "Master summary data not found."

            category = extract_category(question)
            if not category:
                return "Please specify a category using 'in' or 'for' (e.g., 'in Tops')."

            required_cols = [category_col, size_col, sales_col, purchase_col, date_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return f"Error: Missing columns {missing_cols} in data."

            if "historical" in question_lower or "trend" in question_lower:
                df_category = df[df[category_col].str.lower().isin([category.lower(), category.lower().replace(" ", "_")])]
            else:
                df_category = df[df[category_col].str.lower() == category.lower()]

            if df_category.empty:
                available_categories = df[category_col].unique().tolist()
                return f"No data found for category '{category}'. Available categories: {', '.join(available_categories)}"

            df_category = df_category.copy()
            if "historical" in question_lower or "trend" in question_lower:
                df_category.loc[:, 'days_since'] = (datetime.now() - pd.to_datetime(df_category[date_col] + "-01")).dt.days
            else:
                grand_total_date = df[date_col].max()
                df_category.loc[:, 'days_since'] = (datetime.now() - pd.to_datetime(grand_total_date)).days

            df_category.loc[:, 'sales_velocity'] = df_category[sales_col] / df_category['days_since'].replace(0, 1)

            df_grouped = df_category.groupby(size_col).agg({
                sales_col: 'sum',
                purchase_col: 'sum',
                'sales_velocity': 'mean'
            }).reset_index()

            df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
            return f"<h3>Slow-Moving Sizes in {category}</h3>" + df_sorted[[size_col, sales_col, purchase_col, 'sales_velocity']].to_html(index=False, classes="data-table")

        # Question 5: Provide insights on variances and suggest strategies for improvement
        elif "variances and strategies" in question_lower:
            return "Variance analysis requires expected sales data (e.g., forecasts or targets), which is not available in the current database schema. Please provide expected sales data to enable detailed variance insights and tailored improvement strategies."

        # Default response
        else:
            return "Please ask a question I can answer with sales data."

    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()

# Flask app
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def chatbot():
    if request.method == "POST":
        question = request.form["question"]
        answer = retrieve_data(question)
        return render_template("index.html", answer=answer, question=question)
    return render_template("index.html", answer=None, question=None)

if __name__ == "__main__":
    app.run(debug=True)