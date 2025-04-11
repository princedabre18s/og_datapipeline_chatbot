# import psycopg2
# from flask import Flask, request, render_template, jsonify
# from datetime import datetime, timedelta
# import pandas as pd
# import re

# # Database connection
# def get_db_connection():
#     try:
#         conn = psycopg2.connect(
#             host="ep-steep-smoke-a8y63192-pooler.eastus2.azure.neon.tech",
#             database="neondb",
#             user="neondb_owner",
#             password="npg_KB7gQX9tyron",
#             port="5432"
#         )
#         return conn
#     except Exception as e:
#         print(f"Error: {e}")
#         return None

# # Helper function for sell-out days
# def calculate_days_to_sell_out(sales_qty, purchase_qty, days_since):
#     if sales_qty == 0 or purchase_qty == 0:
#         return "N/A"
#     remaining = purchase_qty - sales_qty
#     if remaining <= 0:
#         return "Sold out"
#     daily_rate = sales_qty / days_since
#     return round(remaining / daily_rate) if daily_rate > 0 else "N/A"

# # Helper function to extract category from question
# def extract_category(question):
#     words = question.lower().split()
#     try:
#         if "in" in words:
#             idx = words.index("in") + 1
#             category_words = []
#             for i in range(idx, len(words)):
#                 if words[i] in ["daily", "historical", "trend"]:
#                     break
#                 category_words.append(words[i])
#             return " ".join(category_words).capitalize()
#         elif "for" in words:
#             idx = words.index("for") + 1
#             category_words = []
#             for i in range(idx, len(words)):
#                 if words[i] in ["daily", "historical", "trend"]:
#                     break
#                 category_words.append(words[i])
#             return " ".join(category_words).capitalize()
#     except IndexError:
#         pass
#     return None

# # Retrieve and generate response
# def retrieve_data(question):
#     conn = get_db_connection()
#     if not conn:
#         return "Database connection failed."
    
#     cursor = conn.cursor()
#     question_lower = question.lower()
#     question_lower = ' '.join(question_lower.split())  # Normalize spaces
#     print(f"Processing question: {question_lower}")

#     try:
#         # Question 8: Recommend products for online sales
#         if "online sales" in question_lower and ("prioritize" in question_lower or "recommend" in question_lower):
#             print("Question 8 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE purchase_qty > sales_qty
#                 ORDER BY (purchase_qty - sales_qty) DESC
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             print(f"Query results: {len(results)} rows")
#             if not results:
#                 return "No products with excess inventory found for online sales prioritization."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             df['inventory'] = df['purchase_qty'] - df['sales_qty']
#             return f"<h3>Products Recommended for Online Sales</h3>" + df[['brand', 'category', 'size', 'color', 'inventory']].to_html(index=False, classes="data-table")

#         # Question 1: Notify when items reach 75% and 50% sold
#         elif "reach 75% and 50% sold" in question_lower:
#             print("Question 1 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE purchase_qty > 0 AND LOWER(brand) != 'grand total'
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['percent_sold'] = (df['sales_qty'] / df['purchase_qty']) * 100
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['days_to_sell_out'] = df.apply(lambda row: calculate_days_to_sell_out(row['sales_qty'], row['purchase_qty'], row['days_since']), axis=1)
#             filtered = df[(df['percent_sold'] >= 50) & (df['percent_sold'] <= 75)]
#             if filtered.empty:
#                 return "No items between 50% and 75% sold."
#             return filtered[['brand', 'category', 'size', 'color', 'percent_sold', 'days_to_sell_out']].to_html(index=False, classes="data-table")

#         # Question 2: Best-selling items by specific period(s)
#         elif "best-selling items" in question_lower:
#             print("Question 2 triggered")
#             periods = {"weekly": 7, "monthly": 30, "quarterly": 90}
#             requested_periods = [p for p in periods if p in question_lower]
#             if not requested_periods:
#                 return "Please specify a period (weekly, monthly, or quarterly) for best-selling items."
#             output = ""
#             for period_name in requested_periods:
#                 days = periods[period_name]
#                 query = """
#                     SELECT brand, category, size, color, SUM(sales_qty) as total_sales
#                     FROM sales_data
#                     WHERE created_at >= %s AND LOWER(brand) != 'grand total'
#                     GROUP BY brand, category, size, color
#                     ORDER BY total_sales DESC
#                     LIMIT 5
#                 """
#                 cursor.execute(query, (datetime.now() - timedelta(days=days),))
#                 results = cursor.fetchall()
#                 if results:
#                     df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
#                     output += f"<h3>Top 5 Best-Selling Items ({period_name.capitalize()})</h3>"
#                     output += df.to_html(index=False, classes="data-table")
#                 else:
#                     output += f"<h3>No best-selling items found for {period_name.capitalize()} period.</h3>"
#             return output if output else "No best-selling items found for the specified period(s)."

#         # Question 3: Track non-moving products
#         elif "non-moving products" in question_lower:
#             print("Question 3 triggered")
#             query = """
#                 SELECT brand, category, size, color, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE sales_qty = 0 AND created_at >= %s AND LOWER(brand) != 'grand total'
#             """
#             one_month_ago = datetime.now() - timedelta(days=30)
#             cursor.execute(query, (one_month_ago,))
#             results = cursor.fetchall()
#             if not results:
#                 return "No non-moving products found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "purchase_qty", "created_at"])
#             df['age_days'] = (datetime.now() - df['created_at']).dt.days
#             return df[['brand', 'category', 'size', 'color', 'purchase_qty', 'age_days']].to_html(index=False, classes="data-table")

#         # Question 4: Identify slow-moving sizes within specific categories
#         elif "slow-moving sizes" in question_lower:
#             print("Question 4 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE LOWER(brand) != 'grand total'
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for slow-moving sizes."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['sales_velocity'] = df['sales_qty'] / df['days_since'].replace(0, 1)
#             category = extract_category(question)
#             if not category:
#                 df_grouped = df.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
#                 df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
#                 return f"<h3>Top 5 Slow-Moving Sizes Across All Categories</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")
#             else:
#                 df_category = df[df['category'].str.lower() == category.lower()]
#                 if df_category.empty:
#                     available_categories = df['category'].unique().tolist()
#                     return f"No data found for category '{category}'. Available categories: {', '.join(available_categories)}"
#                 df_grouped = df_category.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
#                 df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
#                 return f"<h3>Slow-Moving Sizes in {category}</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")

#         # Question 5: Provide insights on variances and suggest strategies
#         elif re.search(r"\b(variances|strategies)\b", question_lower):
#             print("Question 5 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for variance analysis."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             df['sales_ratio'] = df['sales_qty'] / df['purchase_qty'].replace(0, 1)
#             low_sales = df[df['sales_ratio'] < 0.5]
#             if low_sales.empty:
#                 return "No products with significant variances found."
#             strategies = "Consider the following strategies for improvement:\n<ul>"
#             strategies += "<li>Offer discounts or promotions on low-selling items.</li>"
#             strategies += "<li>Bundle low-selling items with popular products.</li>"
#             strategies += "<li>Analyze customer feedback to understand why certain items are not selling.</li>"
#             strategies += "<li>Consider discontinuing items with consistently low sales.</li></ul>"
#             insights = low_sales[['brand', 'category', 'size', 'color', 'sales_ratio']].to_html(index=False, classes="data-table")
#             return f"<h3>Products with Low Sales Relative to Purchase</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

#         # Question 6: Analyze turnaround time (proxy solution)
#         elif "turnaround time for exchanges and returns" in question_lower:
#             print("Question 6 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE purchase_qty > sales_qty
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for turnaround analysis."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['unsold_qty'] = df['purchase_qty'] - df['sales_qty']
#             df_sorted = df.sort_values(by='days_since', ascending=False).head(10)
#             note = "<p>Note: No return data available. Showing items with high unsold stock and time since purchase as a proxy for potential returns/exchanges.</p>"
#             return f"<h3>Potential Turnaround Issues</h3>{df_sorted[['brand', 'category', 'size', 'color', 'unsold_qty', 'days_since']].to_html(index=False, classes='data-table')}<br>{note}"

#         # Question 7: Reports on rejected goods and returns (proxy solution)
#         elif "reports on rejected goods and returns" in question_lower:
#             print("Question 7 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE sales_qty = 0 AND purchase_qty > 0
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No potential rejected goods found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             note = "<p>Note: No rejection data available. Showing non-moving items as potential rejections for vendor feedback.</p>"
#             return f"<h3>Potential Rejected Goods</h3>{df[['brand', 'category', 'size', 'color', 'purchase_qty']].to_html(index=False, classes='data-table')}<br>{note}"

#         # Question 9: Identify unique products
#         elif "unique products" in question_lower:
#             print("Question 9 triggered")
#             query = """
#                 SELECT DISTINCT brand, category, size, color
#                 FROM sales_data
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No unique products found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color"])
#             return df.to_html(index=False, classes="data-table")

#         # Question 10: Identify products contributing to X% of sales (dynamic percentage)
#         elif "products contributing to" in question_lower and "% of sales" in question_lower:
#             match = re.search(r'contributing to (\d+)% of sales', question_lower)
#             if match:
#                 percentage = int(match.group(1))
#             else:
#                 return "Please specify a percentage of sales in your query (e.g., 'products contributing to 80% of sales')."
#             query = """
#                 SELECT brand, category, size, color, SUM(sales_qty) as total_sales
#                 FROM sales_data
#                 WHERE LOWER(brand) != 'grand total'
#                 GROUP BY brand, category, size, color
#                 ORDER BY total_sales DESC
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No sales data found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
#             total_sales = df['total_sales'].sum()
#             df['cumulative_sales'] = df['total_sales'].cumsum()
#             df['cumulative_percent'] = df['cumulative_sales'] / total_sales * 100
#             if not df.empty:
#                 k = (df['cumulative_percent'] >= percentage).idxmax()
#                 if df['cumulative_percent'].iloc[k] >= percentage:
#                     top_products = df.iloc[:k+1]
#                 else:
#                     top_products = df
#             else:
#                 top_products = pd.DataFrame()
#             if top_products.empty:
#                 return f"No products found contributing to {percentage}% of sales."
#             return f"<h3>Products contributing to at least {percentage}% of sales</h3>" + top_products[['brand', 'category', 'size', 'color', 'total_sales']].to_html(index=False, classes="data-table")

#         # Question 11: Suggest strategies to reduce inventory of low-performing items
#         elif re.search(r"\b(reduce inventory)\b.*\b(low-performing|strategies)\b", question_lower) or re.search(r"\b(strategies)\b.*\b(reduce inventory)\b", question_lower):
#             print("Question 11 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE sales_qty < 0.1 * purchase_qty
#                 ORDER BY purchase_qty DESC
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No low-performing items found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             strategies = "Strategies to reduce inventory of low-performing items:\n<ul>"
#             strategies += "<li>Implement clearance sales or discounts.</li>"
#             strategies += "<li>Use low-performing items in promotional bundles.</li>"
#             strategies += "<li>Donate or liquidate excess stock.</li>"
#             strategies += "<li>Adjust future purchasing based on sales data.</li></ul>"
#             insights = df.to_html(index=False, classes="data-table")
#             return f"<h3>Low-Performing Items</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

#         # Default response
#         else:
#             print("Default response triggered")
#             return "Please ask a question I can answer with sales data."

#     except Exception as e:
#         print(f"Exception: {e}")
#         return f"Error: {e}"
#     finally:
#         cursor.close()
#         conn.close()

# # Flask app
# app = Flask(__name__)

# # Serve the chat interface
# @app.route("/", methods=["GET"])
# def index():
#     return render_template("other.html")

# # Handle chat requests from the UI
# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     question = data.get("question")
#     if not question:
#         return jsonify({"text": "Please provide a question."})
#     answer = retrieve_data(question)
#     return jsonify({"text": answer})

# if __name__ == "__main__":
#     app.run(debug=True)
  #OG one



# import pandas as pd
# from datetime import datetime, timedelta
# import re

# # Helper function for sell-out days with zero handling
# def calculate_days_to_sell_out(sales_qty, purchase_qty, days_since):
#     if sales_qty == 0 or purchase_qty == 0 or days_since == 0:
#         return "N/A"
#     remaining = purchase_qty - sales_qty
#     if remaining <= 0:
#         return "Sold out"
#     daily_rate = sales_qty / days_since
#     if daily_rate <= 0:
#         return "N/A"
#     return round(remaining / daily_rate)

# # Helper function to extract category from question
# def extract_category(question):
#     words = question.lower().split()
#     try:
#         if "in" in words:
#             idx = words.index("in") + 1
#             category_words = []
#             for i in range(idx, len(words)):
#                 if words[i] in ["daily", "historical", "trend"]:
#                     break
#                 category_words.append(words[i])
#             return " ".join(category_words).capitalize()
#         elif "for" in words:
#             idx = words.index("for") + 1
#             category_words = []
#             for i in range(idx, len(words)):
#                 if words[i] in ["daily", "historical", "trend"]:
#                     break
#                 category_words.append(words[i])
#             return " ".join(category_words).capitalize()
#     except IndexError:
#         pass
#     return None

# # Retrieve and generate response for chatbot
# def retrieve_data(question, logger):
#     # Note: get_db_connection will be passed from data.py
#     from data import get_db_connection  # Import here to avoid circular imports
#     conn = get_db_connection()
#     if not conn:
#         return "Database connection failed."
    
#     cursor = conn.cursor()
#     question_lower = ' '.join(question.lower().split())  # Normalize spaces
#     logger.info(f"Processing chatbot question: {question_lower}")

#     try:
#         # Question 8: Recommend products for online sales
#         if "online sales" in question_lower and ("prioritize" in question_lower or "recommend" in question_lower):
#             logger.info("Question 8 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE purchase_qty > sales_qty
#                 ORDER BY (purchase_qty - sales_qty) DESC
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             logger.info(f"Query results: {len(results)} rows")
#             if not results:
#                 return "No products with excess inventory found for online sales prioritization."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             df['inventory'] = df['purchase_qty'] - df['sales_qty']
#             return f"<h3>Products Recommended for Online Sales</h3>" + df[['brand', 'category', 'size', 'color', 'inventory']].to_html(index=False, classes="data-table")

#         # Question 1: Notify when items reach 75% and 50% sold
#         elif "reach 75% and 50% sold" in question_lower:
#             logger.info("Question 1 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE purchase_qty > 0 AND LOWER(brand) != 'grand total'
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['created_at'] = pd.to_datetime(df['created_at'])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['percent_sold'] = (df['sales_qty'] / df['purchase_qty']) * 100
#             df['days_to_sell_out'] = df.apply(lambda row: calculate_days_to_sell_out(row['sales_qty'], row['purchase_qty'], row['days_since']), axis=1)
#             filtered = df[(df['percent_sold'] >= 50) & (df['percent_sold'] <= 75)]
#             if filtered.empty:
#                 return "No items between 50% and 75% sold."
#             return filtered[['brand', 'category', 'size', 'color', 'percent_sold', 'days_to_sell_out']].to_html(index=False, classes="data-table")

#         # Question 2: Best-selling items by specific period(s)
#         elif "best-selling items" in question_lower:
#             logger.info("Question 2 triggered")
#             periods = {"weekly": 7, "monthly": 30, "quarterly": 90}
#             requested_periods = [p for p in periods if p in question_lower]
#             if not requested_periods:
#                 return "Please specify a period (weekly, monthly, or quarterly) for best-selling items."
#             output = ""
#             for period_name in requested_periods:
#                 days = periods[period_name]
#                 query = """
#                     SELECT brand, category, size, color, SUM(sales_qty) as total_sales
#                     FROM sales_data
#                     WHERE created_at >= %s AND LOWER(brand) != 'grand total'
#                     GROUP BY brand, category, size, color
#                     ORDER BY total_sales DESC
#                     LIMIT 5
#                 """
#                 cursor.execute(query, (datetime.now() - timedelta(days=days),))
#                 results = cursor.fetchall()
#                 if results:
#                     df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
#                     output += f"<h3>Top 5 Best-Selling Items ({period_name.capitalize()})</h3>"
#                     output += df.to_html(index=False, classes="data-table")
#                 else:
#                     output += f"<h3>No best-selling items found for {period_name.capitalize()} period.</h3>"
#             return output if output else "No best-selling items found for the specified period(s)."

#         # Question 3: Track non-moving products
#         elif "non-moving products" in question_lower:
#             logger.info("Question 3 triggered")
#             query = """
#                 SELECT brand, category, size, color, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE sales_qty = 0 AND created_at >= %s AND LOWER(brand) != 'grand total'
#             """
#             one_month_ago = datetime.now() - timedelta(days=30)
#             cursor.execute(query, (one_month_ago,))
#             results = cursor.fetchall()
#             if not results:
#                 return "No non-moving products found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "purchase_qty", "created_at"])
#             df['created_at'] = pd.to_datetime(df['created_at'])
#             df['age_days'] = (datetime.now() - df['created_at']).dt.days
#             return df[['brand', 'category', 'size', 'color', 'purchase_qty', 'age_days']].to_html(index=False, classes="data-table")

#         # Question 4: Identify slow-moving sizes within specific categories
#         elif "slow-moving sizes" in question_lower:
#             logger.info("Question 4 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE LOWER(brand) != 'grand total'
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for slow-moving sizes."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['created_at'] = pd.to_datetime(df['created_at'])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['sales_velocity'] = df['sales_qty'] / df['days_since'].replace(0, 1)
#             category = extract_category(question)
#             if not category:
#                 df_grouped = df.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
#                 df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
#                 return f"<h3>Top 5 Slow-Moving Sizes Across All Categories</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")
#             else:
#                 df_category = df[df['category'].str.lower() == category.lower()]
#                 if df_category.empty:
#                     available_categories = df['category'].unique().tolist()
#                     return f"No data found for category '{category}'. Available categories: {', '.join(available_categories)}"
#                 df_grouped = df_category.groupby('size').agg({'sales_qty': 'sum', 'purchase_qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
#                 df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
#                 return f"<h3>Slow-Moving Sizes in {category}</h3>" + df_sorted[['size', 'sales_qty', 'purchase_qty', 'sales_velocity']].to_html(index=False, classes="data-table")

#         # Question 5: Provide insights on variances and suggest strategies
#         elif re.search(r"\b(variances|strategies)\b", question_lower):
#             logger.info("Question 5 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for variance analysis."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             df['sales_ratio'] = df['sales_qty'] / df['purchase_qty'].replace(0, 1)
#             low_sales = df[df['sales_ratio'] < 0.5]
#             if low_sales.empty:
#                 return "No products with significant variances found."
#             strategies = "Consider the following strategies for improvement:\n<ul>"
#             strategies += "<li>Offer discounts or promotions on low-selling items.</li>"
#             strategies += "<li>Bundle low-selling items with popular products.</li>"
#             strategies += "<li>Analyze customer feedback to understand why certain items are not selling.</li>"
#             strategies += "<li>Consider discontinuing items with consistently low sales.</li></ul>"
#             insights = low_sales[['brand', 'category', 'size', 'color', 'sales_ratio']].to_html(index=False, classes="data-table")
#             return f"<h3>Products with Low Sales Relative to Purchase</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

#         # Question 6: Analyze turnaround time (proxy solution)
#         elif "turnaround time for exchanges and returns" in question_lower:
#             logger.info("Question 6 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
#                 FROM sales_data
#                 WHERE purchase_qty > sales_qty
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No data found for turnaround analysis."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty", "created_at"])
#             df['created_at'] = pd.to_datetime(df['created_at'])
#             df['days_since'] = (datetime.now() - df['created_at']).dt.days
#             df['unsold_qty'] = df['purchase_qty'] - df['sales_qty']
#             df_sorted = df.sort_values(by='days_since', ascending=False).head(10)
#             note = "<p>Note: No return data available. Showing items with high unsold stock and time since purchase as a proxy for potential returns/exchanges.</p>"
#             return f"<h3>Potential Turnaround Issues</h3>{df_sorted[['brand', 'category', 'size', 'color', 'unsold_qty', 'days_since']].to_html(index=False, classes='data-table')}<br>{note}"

#         # Question 7: Reports on rejected goods and returns (proxy solution)
#         elif "reports on rejected goods and returns" in question_lower:
#             logger.info("Question 7 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE sales_qty = 0 AND purchase_qty > 0
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No potential rejected goods found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             note = "<p>Note: No rejection data available. Showing non-moving items as potential rejections for vendor feedback.</p>"
#             return f"<h3>Potential Rejected Goods</h3>{df[['brand', 'category', 'size', 'color', 'purchase_qty']].to_html(index=False, classes='data-table')}<br>{note}"

#         # Question 9: Identify unique products
#         elif "unique products" in question_lower:
#             logger.info("Question 9 triggered")
#             query = """
#                 SELECT DISTINCT brand, category, size, color
#                 FROM sales_data
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No unique products found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color"])
#             return df.to_html(index=False, classes="data-table")

#         # Question 10: Identify products contributing to X% of sales (dynamic percentage)
#         elif "products contributing to" in question_lower and "% of sales" in question_lower:
#             match = re.search(r'contributing to (\d+)% of sales', question_lower)
#             if match:
#                 percentage = int(match.group(1))
#             else:
#                 return "Please specify a percentage of sales in your query (e.g., 'products contributing to 80% of sales')."
#             query = """
#                 SELECT brand, category, size, color, SUM(sales_qty) as total_sales
#                 FROM sales_data
#                 WHERE LOWER(brand) != 'grand total'
#                 GROUP BY brand, category, size, color
#                 ORDER BY total_sales DESC
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No sales data found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "total_sales"])
#             total_sales = df['total_sales'].sum()
#             df['cumulative_sales'] = df['total_sales'].cumsum()
#             df['cumulative_percent'] = df['cumulative_sales'] / total_sales * 100
#             if not df.empty:
#                 k = (df['cumulative_percent'] >= percentage).idxmax()
#                 if df['cumulative_percent'].iloc[k] >= percentage:
#                     top_products = df.iloc[:k+1]
#                 else:
#                     top_products = df
#             else:
#                 top_products = pd.DataFrame()
#             if top_products.empty:
#                 return f"No products found contributing to {percentage}% of sales."
#             return f"<h3>Products contributing to at least {percentage}% of sales</h3>" + top_products[['brand', 'category', 'size', 'color', 'total_sales']].to_html(index=False, classes="data-table")

#         # Question 11: Suggest strategies to reduce inventory of low-performing items
#         elif re.search(r"\b(reduce inventory)\b.*\b(low-performing|strategies)\b", question_lower) or re.search(r"\b(strategies)\b.*\b(reduce inventory)\b", question_lower):
#             logger.info("Question 11 triggered")
#             query = """
#                 SELECT brand, category, size, color, sales_qty, purchase_qty
#                 FROM sales_data
#                 WHERE sales_qty < 0.1 * purchase_qty
#                 ORDER BY purchase_qty DESC
#                 LIMIT 10
#             """
#             cursor.execute(query)
#             results = cursor.fetchall()
#             if not results:
#                 return "No low-performing items found."
#             df = pd.DataFrame(results, columns=["brand", "category", "size", "color", "sales_qty", "purchase_qty"])
#             strategies = "Strategies to reduce inventory of low-performing items:\n<ul>"
#             strategies += "<li>Implement clearance sales or discounts.</li>"
#             strategies += "<li>Use low-performing items in promotional bundles.</li>"
#             strategies += "<li>Donate or liquidate excess stock.</li>"
#             strategies += "<li>Adjust future purchasing based on sales data.</li></ul>"
#             insights = df.to_html(index=False, classes="data-table")
#             return f"<h3>Low-Performing Items</h3>{insights}<br><h3>Suggested Strategies</h3><p>{strategies}</p>"

#         # Default response
#         else:
#             logger.info("Default response triggered")
#             return "Please ask a question I can answer with sales data."

#     except Exception as e:
#         logger.error(f"Exception in retrieve_data: {e}")
#         return f"Error: {e}"
#     finally:
#         cursor.close()
#         conn.close()

# # Chatbot route handler (to be registered in data.py)
# def chat():
#     from flask import request, jsonify
#     from data import FlaskLogger  # Import FlaskLogger from data.py
#     log_output = FlaskLogger()
#     data = request.get_json(silent=True)
#     if data is None:
#         log_output.error("Received non-JSON request")
#         return jsonify({"text": "Invalid request format. Please send JSON data.", "logs": log_output.get_logs()}), 400
#     question = data.get("question", "")
#     log_output.info(f"Received chatbot question: {question}")
#     if not question:
#         log_output.error("No question provided")
#         return jsonify({"text": "Please provide a question.", "logs": log_output.get_logs()}), 400
#     answer = retrieve_data(question, log_output)
#     return jsonify({"text": answer, "logs": log_output.get_logs()})

# the actual one above


# the gemini one below


import pandas as pd
from datetime import datetime, timedelta
import re
import google.generativeai as genai
import os

GOOGLE_API_KEY = "AIzaSyBavRghc9aiYkpeh2i18PM4vMluCUNqg4k"  # WARNING: Hardcoding API key!
if not GOOGLE_API_KEY:
    raise ValueError("Please set the GOOGLE_API_KEY.")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Path to the master summary file
MASTER_SUMMARY_PATH = "processed_data/master_summary.xlsx"

# Helper function for sell-out days with zero handling
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

# Function to load master summary with better error handling
def load_master_summary(logger):
    try:
        summary_df = pd.read_excel(MASTER_SUMMARY_PATH)
        summary_text = summary_df.to_string(index=False)
        logger.info(f"Master summary loaded successfully with {len(summary_df)} rows.")
        return summary_text
    except FileNotFoundError:
        logger.warning(f"Master summary file not found at: {MASTER_SUMMARY_PATH}")
        return None
    except Exception as e:
        logger.error(f"Error loading master summary from {MASTER_SUMMARY_PATH}: {e}")
        return None

# Function to generate a refined answer using Gemini Pro
def generate_refined_response(question, data_context, summary_context=None):
    prompt_parts = [
        "You are a helpful chatbot providing sales data in a structured format.",
        f"The user asked: \"{question}\"",
    ]

    if "best-selling items" in question.lower():
        prompt_parts.append("Here are the top 5 best-selling items for the requested periods, formatted as Markdown tables:")
        prompt_parts.append(f"{data_context}")
    elif "reduce inventory" in question.lower():
        prompt_parts.append("Here are some low-performing items and suggested strategies to reduce their inventory:")
        prompt_parts.append(f"{data_context}")
    elif "variances" in question.lower():
        prompt_parts.append("Here's an analysis of sales and purchase variances and some strategies for improvement:")
        prompt_parts.append(f"{data_context}")
    else:
        prompt_parts.append("Here is the relevant sales data in Markdown table format:")
        prompt_parts.append(f"{data_context}")
        if summary_context:
            prompt_parts.append("\nHere is a relevant master summary:")
            prompt_parts.append(f"```\n{summary_context}\n```")
        prompt_parts.append("Present this information concisely to the user.")

    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating refined response: {e}"

# Retrieve and generate response for chatbot
def retrieve_data(question, logger):
    from data import get_db_connection  # Import here to avoid circular imports
    conn = get_db_connection()
    if not conn:
        return "Database connection failed."

    cursor = conn.cursor()
    logger.info(f"Raw question received: '{question}'")  # Log the raw question
    question_lower = ' '.join(question.lower().split())  # Normalize spaces
    logger.info(f"Processing chatbot question: {question_lower}")
    logger.info(f"Lowercased question: '{question_lower}'")  # Log the lowercased version
    rag_answer = None
    data_for_context = None
    master_summary = load_master_summary(logger)

    try:
        # Question 1: Notify when items reach certain percentage sold.
        if any(keyword in question_lower for keyword in ["reach", "notify", "items"]) and \
             any(keyword in question_lower for keyword in ["50%", "75%"]) and \
             "sold" in question_lower and \
             any(keyword in question_lower for keyword in ["estimated days", "sell out", "time to sell"]):
            logger.info("Question 1 triggered (flexible)")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE purchase_qty > 0 AND LOWER(brand) != 'grand total'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No data found."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Sales Qty", "Purchase Qty", "Created At"])
                df['Created At'] = pd.to_datetime(df['Created At'])
                df['days_since'] = (datetime.now() - df['Created At']).dt.days
                df['percent_sold'] = (df['Sales Qty'] / df['Purchase Qty']) * 100
                df['days_to_sell_out'] = df.apply(lambda row: calculate_days_to_sell_out(row['Sales Qty'], row['Purchase Qty'], row['days_since']), axis=1)

                response_parts = []
                if "75%" in question_lower and "50%" in question_lower:
                    reaching_50 = df[(df['percent_sold'] >= 49) & (df['percent_sold'] <= 51)]
                    if not reaching_50.empty:
                        reaching_50_table = reaching_50[['Brand', 'Category', 'Size', 'Color', 'days_to_sell_out']].head().to_markdown(index=False)
                        response_parts.append(f"Reaching 50% Sold:\n{reaching_50_table}")
                    else:
                        response_parts.append("No items nearing 50% sold.")

                    nearing_75 = df[(df['percent_sold'] >= 74) & (df['percent_sold'] <= 76)]
                    if not nearing_75.empty:
                        nearing_75_table = nearing_75[['Brand', 'Category', 'Size', 'Color', 'percent_sold', 'days_to_sell_out']].head().to_markdown(index=False)
                        response_parts.append(f"Nearing 75% Sold:\n{nearing_75_table}")
                    else:
                        response_parts.append("No items nearing 75% sold.")
                elif "50%" in question_lower:
                    reaching_50 = df[(df['percent_sold'] >= 49) & (df['percent_sold'] <= 51)]
                    if not reaching_50.empty:
                        reaching_50_table = reaching_50[['Brand', 'Category', 'Size', 'Color', 'days_to_sell_out']].head().to_markdown(index=False)
                        response_parts.append(f"Reaching 50% Sold:\n{reaching_50_table}")
                    else:
                        response_parts.append("No items nearing 50% sold.")
                elif "75%" in question_lower:
                    nearing_75 = df[(df['percent_sold'] >= 74) & (df['percent_sold'] <= 76)]
                    if not nearing_75.empty:
                        nearing_75_table = nearing_75[['Brand', 'Category', 'Size', 'Color', 'percent_sold', 'days_to_sell_out']].head().to_markdown(index=False)
                        response_parts.append(f"Nearing 75% Sold:\n{nearing_75_table}")
                    else:
                        response_parts.append("No items nearing 75% sold.")

                if response_parts:
                    rag_answer = "\n".join(response_parts)
                    data_for_context = rag_answer
                else:
                    rag_answer = "No items found matching the specified sales percentages."

        # Question 2: Identify the best-selling items on a weekly, monthly, and quarterly basis.
        elif "best-selling items" in question_lower:
            logger.info("Question 2 triggered")
            periods = {"weekly": 7, "monthly": 30, "quarterly": 90}
            requested_periods = [p for p in periods if p in question_lower]
            if not requested_periods:
                rag_answer = "Please specify a period (weekly, monthly, or quarterly) for best-selling items."
            else:
                output_markdown = []
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
                        df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Total Sales"])
                        markdown_table = f"**Top 5 Best-Selling Items ({period_name.capitalize()}):**\n{df.to_markdown(index=False)}\n"
                        output_markdown.append(markdown_table)
                    else:
                        output_markdown.append(f"**Top 5 Best-Selling Items ({period_name.capitalize()}):**\nNo data found for this period.\n")

                rag_answer_text = "\n".join(output_markdown)
                rag_answer = rag_answer_text
                data_for_context = rag_answer_text

        # Question 3: Track non-moving products and their aging quantities.
        elif "non-moving products" in question_lower:
            logger.info("Question 3 triggered")
            query = """
                SELECT brand, category, size, color, purchase_qty, created_at
                FROM sales_data
                WHERE sales_qty = 0 AND created_at >= %s AND LOWER(brand) != 'grand total'
            """
            one_month_ago = datetime.now() - timedelta(30)
            cursor.execute(query, (one_month_ago,))
            results = cursor.fetchall()
            if not results:
                rag_answer = "No non-moving products found."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Purchase Qty", "Created At"])
                df['Created At'] = pd.to_datetime(df['Created At'])
                df['age_days'] = (datetime.now() - df['Created At']).dt.days
                rag_answer_table = df[['Brand', 'Category', 'Size', 'Color', 'Purchase Qty', 'age_days']].to_markdown(index=False)
                rag_answer = f"Non-Moving Products (older than 30 days):\n{rag_answer_table}"
                data_for_context = rag_answer_table

        # Question 4: Identify slow-moving sizes within specific categories.
        elif "slow-moving sizes" in question_lower:
            logger.info("Question 4 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE LOWER(brand) != 'grand total'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No data found for slow-moving sizes."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Sales Qty", "Purchase Qty", "Created At"])
                df['Created At'] = pd.to_datetime(df['Created At'])
                df['days_since'] = (datetime.now() - df['Created At']).dt.days
                df['sales_velocity'] = df['Sales Qty'] / df['days_since'].replace(0, 1)
                category = extract_category(question)
                if not category:
                    df_grouped = df.groupby('Size').agg({'Sales Qty': 'sum', 'Purchase Qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
                    df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
                    rag_answer_table = df_sorted[['Size', 'Sales Qty', 'Purchase Qty', 'sales_velocity']].to_markdown(index=False)
                    rag_answer = f"Top 5 Slow-Moving Sizes Across All Categories:\n{rag_answer_table}"
                    data_for_context = rag_answer_table
                else:
                    df_category = df[df['Category'].str.lower() == category.lower()]
                    if df_category.empty:
                        available_categories = df['Category'].unique().tolist()
                        rag_answer = f"No data found for category '{category}'. Available categories: {', '.join(available_categories)}"
                    else:
                        df_grouped = df_category.groupby('Size').agg({'Sales Qty': 'sum', 'Purchase Qty': 'sum', 'sales_velocity': 'mean'}).reset_index()
                        df_sorted = df_grouped.sort_values(by='sales_velocity').head(5)
                        rag_answer_table = df_sorted[['Size', 'Sales Qty', 'Purchase Qty', 'sales_velocity']].to_markdown(index=False)
                        rag_answer = f"Slow-Moving Sizes in {category}:\n{rag_answer_table}"
                        data_for_context = rag_answer_table

        # Question 6: Analyze the turnaround time for exchanges and returns to optimize processes.
        elif "turnaround time for exchanges and returns" in question_lower:
            logger.info("Question 6 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty, created_at
                FROM sales_data
                WHERE purchase_qty > sales_qty
                ORDER BY created_at ASC
                LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No data found for turnaround analysis."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Sales Qty", "Purchase Qty", "Created At"])
                df['Created At'] = pd.to_datetime(df['Created At'])
                df['days_since_purchase'] = (datetime.now() - df['Created At']).dt.days
                potential_returns_table = df[['Brand', 'Category', 'Size', 'Color', 'days_since_purchase']].to_markdown(index=False)
                rag_answer = f"Potential Items for Exchange/Return (based on unsold and time):\n{potential_returns_table}\n\nNote: This is a proxy as actual return/exchange data is not available in the current sales data."
                data_for_context = f"Potential return/exchange items:\n{potential_returns_table}\nNote: Proxy data."

        # Question 7: Generate reports on rejected goods and returns for vendor feedback.
        elif "reports on rejected goods and returns" in question_lower:
            logger.info("Question 7 triggered")
            query = """
                SELECT brand, category, size, color, purchase_qty, created_at
                FROM sales_data
                WHERE sales_qty = 0 AND purchase_qty > 0
                ORDER BY created_at ASC
                LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No potential rejected goods found."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Purchase Qty", "Created At"])
                df['Created At'] = pd.to_datetime(df['Created At'])
                df['age_days'] = (datetime.now() - df['Created At']).dt.days
                potential_rejected_table = df[['Brand', 'Category', 'Size', 'Color', 'Purchase Qty', 'age_days']].to_markdown(index=False)
                rag_answer = f"Potential Rejected Goods (non-selling items):\n{potential_rejected_table}\n\nNote: This is a proxy as actual rejection data is not available."
                data_for_context = f"Potential rejected goods:\n{potential_rejected_table}\nNote: Proxy data."

        # Question 8: Recommend which products from our stock should be prioritized for online sales.
        elif "online sales" in question_lower and ("prioritize" in question_lower or "recommend" in question_lower):
            logger.info("Question 8 triggered")
            query = """
                SELECT brand, category, size, color, purchase_qty - sales_qty as unsold_qty
                FROM sales_data
                WHERE purchase_qty > sales_qty AND LOWER(brand) != 'grand total'
                ORDER BY unsold_qty DESC
                LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No products with significant unsold stock found."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Unsold Qty"])
                recommendation_table = df.to_markdown(index=False)
                rag_answer = f"Products Recommended for Online Sales (based on unsold stock):\n{recommendation_table}"
                data_for_context = recommendation_table

        # Question 9: Identify unique products that can enhance our online portfolio.
        elif "unique products" in question_lower:
            logger.info("Question 9 triggered")
            query_unique = """
                    SELECT DISTINCT brand, category, size, color
                    FROM sales_data
                    WHERE LOWER(brand) != 'grand total'
                """
            cursor.execute(query_unique)
            unique_results = cursor.fetchall()
            if not unique_results:
                rag_answer = "No unique products identified."
            else:
                unique_df = pd.DataFrame(unique_results, columns=["Brand", "Category", "Size", "Color"])
                # To suggest enhancement, we might look for products with high purchase but low sales                
                query_potential = """
                        SELECT brand, category, size, color, purchase_qty, sales_qty
                        FROM sales_data
                        WHERE purchase_qty > sales_qty * 2 AND purchase_qty > 5 AND LOWER(brand) != 'grand total'
                        ORDER BY purchase_qty DESC
                        LIMIT 5
                    """
                cursor.execute(query_potential)
                potential_results = cursor.fetchall()
                if potential_results:
                        potential_df = pd.DataFrame(potential_results, columns=["Brand", "Category", "Size", "Color", "Purchase Qty", "Sales Qty"])
                        unique_products_table = potential_df.to_markdown(index=False)
                        rag_answer = f"Potentially Unique Products to Enhance Portfolio (High Purchase, Low Sales):\n{unique_products_table}"
                        data_for_context = unique_products_table
                else:
                        unique_products_table = unique_df.to_markdown(index=False)
                        rag_answer = f"Identified Unique Products:\n{unique_products_table}"
                        data_for_context = unique_products_table

        # Question 10: Identify the top 20% of products contributing to 80% of sales.
        elif re.search(r"top \d+% of products contributing to \d+% of sales", question_lower):
            logger.info("Question 10 triggered")
            match_percent = re.search(r"top (\d+)% of products contributing to (\d+)% of sales", question_lower)
            if match_percent:
                top_percent = int(match_percent.group(1))
                sales_percent = int(match_percent.group(2))
                query = """
                    SELECT brand, category, size, color, SUM(sales_qty) as total_sales
                    FROM sales_data
                    WHERE LOWER(brand) != 'grand total'
                    GROUP BY brand, category, size, color
                    ORDER BY total_sales DESC
                """
                cursor.execute(query)
                results = cursor.fetchall()
                if not results:
                    rag_answer = "No sales data found."
                else:
                    df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Total Sales"])
                    total_sales_overall = df['Total Sales'].sum()
                    df['percent_contribution'] = (df['Total Sales'] / total_sales_overall) * 100
                    df_sorted = df.sort_values(by='percent_contribution', ascending=False)
                    cumulative_percent = 0
                    top_n_products = []
                    for index, row in df_sorted.iterrows():
                        cumulative_percent += row['percent_contribution']
                        top_n_products.append(row[['Brand', 'Category', 'Size', 'Color', 'percent_contribution']].to_dict())
                        if cumulative_percent >= sales_percent:
                            break

                    num_top_products = len(top_n_products)
                    total_products = len(df)
                    if total_products > 0:
                        target_num = int(total_products * (top_percent / 100))
                        top_products_reaching_target = top_n_products[:target_num]
                    else:
                        top_products_reaching_target = []

                    if top_products_reaching_target:
                        top_products_df = pd.DataFrame(top_products_reaching_target)
                        rag_answer_table = top_products_df.to_markdown(index=False)
                        rag_answer = f"Top {top_percent}% of Products Contributing to {sales_percent}% of Sales:\n{rag_answer_table}"
                        data_for_context = rag_answer_table
                    else:
                        rag_answer = f"Could not identify the top {top_percent}% of products contributing to {sales_percent}% of sales."
            else:
                rag_answer = "Invalid format for identifying top contributing products."

        # Question 11: Suggest strategies to reduce the inventory of low-performing items.
        elif "suggest strategies to reduce the inventory of low-performing items" in question_lower:
            logger.info("Question 11 triggered")
            query = """
                SELECT brand, category, size, color, sales_qty, purchase_qty
                FROM sales_data
                WHERE sales_qty < 0.2 * purchase_qty AND purchase_qty > 0
                ORDER BY purchase_qty DESC
                LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No low-performing items found."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Size", "Color", "Sales Qty", "Purchase Qty"])
                low_performing_table = df[['Brand', 'Category', 'Size', 'Color', 'Sales Qty', 'Purchase Qty']].to_markdown(index=False)
                strategies = "Consider clearance sales, promotional bundles, reducing future orders, or analyzing reasons for low performance."
                rag_answer = f"Low-Performing Items:\n{low_performing_table}\n\nSuggested Strategies: {strategies}"
                data_for_context = f"Low-performing items:\n{low_performing_table}\nStrategies: {strategies}"

        # Question 12: Provide insights on variances and suggest strategies for improvement.
        elif re.search(r"\b(insights on variances)\b.*\b(strategies for improvement)\b", question_lower) or re.search(r"\b(strategies for improvement)\b.*\b(insights on variances)\b", question_lower):
            logger.info("Question 12 triggered")
            query = """
                SELECT
                    brand,
                    category,
                    SUM(sales_qty) AS total_sales_qty,
                    SUM(purchase_qty) AS total_purchase_qty,
                    SUM(purchase_qty) - SUM(sales_qty) AS variance_qty
                FROM sales_data
                WHERE LOWER(brand) != 'grand total'
                GROUP BY brand, category
                ORDER BY variance_qty DESC
                LIMIT 5
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if not results:
                rag_answer = "No significant variances found."
            else:
                df = pd.DataFrame(results, columns=["Brand", "Category", "Total Sales Qty", "Total Purchase Qty", "Variance Qty"])
                variances_table = df.to_markdown(index=False)
                insights = "Significant positive variance (more purchased than sold) indicates potential overstocking. Negative variance (more sold than purchased) might suggest missed sales opportunities due to insufficient stock."
                strategies = "For high positive variance: consider reducing future orders, promotions, or exploring new sales channels. For negative variance: analyze demand and potentially increase order quantities."
                rag_answer = f"Sales and Purchase Variances:\n{variances_table}\n\nInsights: {insights}\n\nStrategies for Improvement: {strategies}"
                data_for_context = f"Sales and purchase variances:\n{variances_table}\nInsights: {insights}\nStrategies: {strategies}"

        # Default response
        else:
            logger.info("Default response triggered")
            rag_answer = "Please ask a question I can answer with sales data."

        # Refine the answer using Gemini if relevant data was found
        if rag_answer and data_for_context:
            refined_answer = generate_refined_response(question, data_for_context, master_summary)
            final_answer = refined_answer
        else:
            final_answer = rag_answer

        return final_answer

    except Exception as e:
        logger.error(f"Exception in retrieve_data: {e}")
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()

# Chatbot route handler (to be registered in data.py)
def chat():
    from flask import request, jsonify
    from data import FlaskLogger  # Import FlaskLogger from data.py
    log_output = FlaskLogger()
    data = request.get_json(silent=True)
    if data is None:
        log_output.error("Received non-JSON request")
        return jsonify({"text": "Invalid request format. Please send JSON data.", "logs": log_output.get_logs()}), 400
    question = data.get("question", "")
    log_output.info(f"Received chatbot question: {question}")
    if not question:
        log_output.error("No question provided")
        return jsonify({"text": "Please provide a question.", "logs": log_output.get_logs()}), 400
    answer = retrieve_data(question, log_output)
    return jsonify({"text": answer, "logs": log_output.get_logs()})