from flask import Flask, request
from datetime import datetime
import config
import json

app = Flask(__name__)


# FRAUD DETECTION FUNCTION
def check_risk(amount, channel, transaction_type):
    if amount <= 0 or amount >= 50000:
        return "Fraud"

    if channel.strip().lower() not in ["mobile", "web", "atm", "branch"]:
        return "Fraud"

    if transaction_type.strip().lower() not in ["credit", "debit", "transfer"]:
        return "Fraud"

    return "Normal"


# HOME PAGE
@app.route("/")
def home():
    db = config.connect()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN fraud_status = 'Fraud' THEN 1 ELSE 0 END) AS fraud,
            SUM(CASE WHEN fraud_status = 'Normal' THEN 1 ELSE 0 END) AS normal,
            COALESCE(SUM(amount), 0) AS total_amount
        FROM transaction
    """)
    stats = cur.fetchone()

    cur.execute("""
        SELECT fraud_status, COUNT(*) AS total
        FROM transaction
        GROUP BY fraud_status
    """)
    status_rows = cur.fetchall()

    cur.execute("""
        SELECT channel, COUNT(*) AS total
        FROM transaction
        GROUP BY channel
    """)
    channel_rows = cur.fetchall()

    cur.close()
    db.close()

    total = stats["total"] or 0
    fraud = stats["fraud"] or 0
    normal = stats["normal"] or 0
    total_amount = stats["total_amount"] or 0
    fraud_percentage = fraud * 100 / total if total else 0

    status_labels = [r["fraud_status"] for r in status_rows]
    status_values = [int(r["total"]) for r in status_rows]

    channel_labels = [r["channel"] or "Unknown" for r in channel_rows]
    channel_values = [int(r["total"]) for r in channel_rows]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial Risk Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
            }

            body {
                background: #f1f5f9;
                color: #1e293b;
            }

            .layout {
                display: flex;
                min-height: 100vh;
            }

            .sidebar {
                width: 245px;
                background: #111827;
                color: white;
                padding: 28px 18px;
                flex-shrink: 0;
            }

            .brand {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 35px;
                line-height: 1.5;
            }

            .brand span {
                color: #60a5fa;
            }

            .menu-title {
                color: #94a3b8;
                font-size: 12px;
                margin: 22px 10px 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .sidebar a {
                display: block;
                padding: 12px;
                color: #cbd5e1;
                text-decoration: none;
                border-radius: 8px;
                margin: 5px 0;
                font-size: 14px;
            }

            .sidebar a:hover {
                background: #334155;
                color: white;
            }

            .main {
                flex: 1;
                min-width: 0;
                padding: 30px;
            }

            .topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 15px;
                flex-wrap: wrap;
                margin-bottom: 28px;
            }

            .topbar h1 {
                font-size: 28px;
                margin-bottom: 8px;
            }

            .muted {
                color: #64748b;
                font-size: 14px;
            }

            .live {
                background: #dcfce7;
                color: #166534;
                padding: 9px 14px;
                border-radius: 20px;
                font-size: 13px;
            }

            .cards {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 18px;
                margin-bottom: 25px;
            }

            .card {
                background: white;
                border-radius: 14px;
                padding: 22px;
                box-shadow: 0 3px 12px #0f172a0a;
                border: 1px solid #e2e8f0;
            }

            .card-label {
                color: #64748b;
                font-size: 14px;
                margin-bottom: 15px;
            }

            .card-value {
                font-size: 29px;
                font-weight: bold;
                margin-bottom: 10px;
                overflow-wrap: anywhere;
            }

            .card-note {
                font-size: 12px;
                color: #64748b;
            }

            .blue { border-top: 4px solid #3b82f6; }
            .red { border-top: 4px solid #ef4444; }
            .green { border-top: 4px solid #22c55e; }
            .purple { border-top: 4px solid #8b5cf6; }

            .charts {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 20px;
                margin-bottom: 25px;
            }

            .chart-box {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                padding: 22px;
                min-width: 0;
            }

            .chart-box h3 {
                margin-bottom: 20px;
                font-size: 17px;
            }

            .chart-area {
                position: relative;
                height: 280px;
            }

            .actions {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 15px;
            }

            .action {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
                text-decoration: none;
                color: #1e293b;
                transition: 0.2s;
            }

            .action:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
            }

            .action h3 {
                font-size: 15px;
                margin-bottom: 8px;
            }

            .action p {
                font-size: 12px;
                color: #64748b;
                line-height: 1.5;
            }

            .section-title {
                margin: 30px 0 17px;
                font-size: 20px;
            }

            footer {
                color: #64748b;
                font-size: 12px;
                margin-top: 30px;
                text-align: center;
            }

            @media (max-width: 1100px) {
                .cards, .actions {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }

            @media (max-width: 750px) {
                .layout {
                    flex-direction: column;
                }

                .sidebar {
                    width: 100%;
                }

                .sidebar nav {
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 4px;
                }

                .menu-title {
                    grid-column: 1 / -1;
                }

                .main {
                    padding: 18px;
                }

                .charts {
                    grid-template-columns: 1fr;
                }

                .topbar h1 {
                    font-size: 23px;
                }
            }

            @media (max-width: 420px) {
                .cards, .actions {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>

    <body>
    <div class="layout">

        <aside class="sidebar">
            <div class="brand">
                Financial<br><span>Risk Analysis</span>
            </div>

            <nav>
                <div class="menu-title">Main Menu</div>
                <a href="/">&#9632; Dashboard</a>
                <a href="/overview">&#9632; Overview</a>
                <a href="/transactions">&#9632; Transactions</a>
                <a href="/flagged">&#9632; Fraud Records</a>

                <div class="menu-title">Manage Transactions</div>
                <a href="/add">+ Add Transaction</a>
                <a href="/update">&#9998; Update Transaction</a>
                <a href="/search">&#9906; Search Transaction</a>
                <a href="/delete">&#10005; Delete Transaction</a>

                <div class="menu-title">Reports</div>
                <a href="/all-summaries">&#9776; Summaries</a>
            </nav>
        </aside>

        <main class="main">
            <div class="topbar">
                <div>
                    <h1>Dashboard</h1>
                    <p class="muted">
                        Financial Risk Analysis and Rule-Based Fraud Detection System
                    </p>
                </div>
                <div class="live">● Dashboard Connected</div>
            </div>

            <div class="cards">
                <div class="card blue">
                    <div class="card-label">Total Transactions</div>
                    <div class="card-value">TOTAL_VALUE</div>
                    <div class="card-note">All recorded transactions</div>
                </div>

                <div class="card red">
                    <div class="card-label">Fraud Transactions</div>
                    <div class="card-value">FRAUD_VALUE</div>
                    <div class="card-note">Transactions flagged as fraud</div>
                </div>

                <div class="card green">
                    <div class="card-label">Normal Transactions</div>
                    <div class="card-value">NORMAL_VALUE</div>
                    <div class="card-note">Transactions passing the rules</div>
                </div>

                <div class="card purple">
                    <div class="card-label">Fraud Percentage</div>
                    <div class="card-value">PERCENT_VALUE%</div>
                    <div class="card-note">Fraud out of all transactions</div>
                </div>
            </div>

            <div class="charts">
                <div class="chart-box">
                    <h3>Fraud vs Normal Transactions</h3>
                    <div class="chart-area">
                        <canvas id="statusChart"></canvas>
                    </div>
                </div>

                <div class="chart-box">
                    <h3>Transactions by Channel</h3>
                    <div class="chart-area">
                        <canvas id="channelChart"></canvas>
                    </div>
                </div>
            </div>

            <h2 class="section-title">Quick Actions</h2>

            <div class="actions">
                <a class="action" href="/add">
                    <h3>+ Add Transaction</h3>
                    <p>Record a transaction and calculate its fraud status.</p>
                </a>

                <a class="action" href="/transactions">
                    <h3>View Transactions</h3>
                    <p>View the complete transaction table.</p>
                </a>

                <a class="action" href="/search">
                    <h3>Search Transaction</h3>
                    <p>Find a transaction by its ID.</p>
                </a>

                <a class="action" href="/update">
                    <h3>Update Transaction</h3>
                    <p>Modify a transaction and recalculate its status.</p>
                </a>

                <a class="action" href="/delete">
                    <h3>Delete Transaction</h3>
                    <p>Remove a transaction from the database.</p>
                </a>

                <a class="action" href="/flagged">
                    <h3>Fraud Records</h3>
                    <p>Review transactions flagged by your rules.</p>
                </a>

                <a class="action" href="/overview">
                    <h3>Financial Overview</h3>
                    <p>Review minimum, maximum, total and average amounts.</p>
                </a>

                <a class="action" href="/all-summaries">
                    <h3>Reports & Summaries</h3>
                    <p>View counts by transaction type, channel and status.</p>
                </a>
            </div>

            <footer>
                Financial Risk Analysis System | Flask and MySQL
            </footer>
        </main>
    </div>

    <script>
        const statusLabels = STATUS_LABELS;
        const statusValues = STATUS_VALUES;
        const channelLabels = CHANNEL_LABELS;
        const channelValues = CHANNEL_VALUES;

        new Chart(document.getElementById("statusChart"), {
            type: "doughnut",
            data: {
                labels: statusLabels,
                datasets: [{
                    data: statusValues,
                    backgroundColor: ["#ef4444", "#22c55e", "#94a3b8"],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                }
            }
        });

        new Chart(document.getElementById("channelChart"), {
            type: "bar",
            data: {
                labels: channelLabels,
                datasets: [{
                    label: "Transactions",
                    data: channelValues,
                    backgroundColor: "#3b82f6",
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    </script>
    </body>
    </html>
    """

    replacements = {
        "TOTAL_VALUE": str(total),
        "FRAUD_VALUE": str(fraud),
        "NORMAL_VALUE": str(normal),
        "PERCENT_VALUE": f"{fraud_percentage:.2f}",
        "STATUS_LABELS": json.dumps(status_labels),
        "STATUS_VALUES": json.dumps(status_values),
        "CHANNEL_LABELS": json.dumps(channel_labels),
        "CHANNEL_VALUES": json.dumps(channel_values)
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    return html


# FINANCIAL OVERVIEW
@app.route("/overview")
def overview():
    db = config.connect()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN fraud_status = 'Fraud' THEN 1 ELSE 0 END) AS fraud_count,
            SUM(CASE WHEN fraud_status = 'Normal' THEN 1 ELSE 0 END) AS normal_count,
            MIN(amount) AS minimum,
            MAX(amount) AS maximum,
            SUM(amount) AS total_amount,
            AVG(amount) AS average_amount
        FROM transaction
    """)

    row = cur.fetchone()

    total_count = row["total_count"] or 0
    fraud_count = row["fraud_count"] or 0
    normal_count = row["normal_count"] or 0

    fraud_percentage = (
        fraud_count / total_count * 100 if total_count > 0 else 0
    )

    minimum = row["minimum"] if row["minimum"] is not None else 0
    maximum = row["maximum"] if row["maximum"] is not None else 0
    total_amount = row["total_amount"] or 0
    average_amount = row["average_amount"] or 0

    cur.close()
    db.close()

    return f"""
    <center>
        <h2>Financial Overview</h2>
        <table border="1" cellpadding="8">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Transactions</td><td>{total_count}</td></tr>
            <tr><td>Fraud Transactions</td><td>{fraud_count}</td></tr>
            <tr><td>Normal Transactions</td><td>{normal_count}</td></tr>
            <tr><td>Minimum Amount</td><td>{minimum:.0f}</td></tr>
            <tr><td>Maximum Amount</td><td>{maximum:.0f}</td></tr>
            <tr><td>Total Amount</td><td>{total_amount:.0f}</td></tr>
            <tr><td>Average Amount</td><td>{average_amount:.0f}</td></tr>
            <tr><td>Fraud Percentage</td><td>{fraud_percentage:.2f}%</td></tr>
        </table>
    </center>
    """
@app.route("/transactions")
def transactions():
    con = config.connect()
    cursor = con.cursor(dictionary=True)

    cursor.execute("""
        SELECT Transaction_ID, Account_ID, Transaction_datetime,
               amount, Transaction_Type, channel, region, fraud_status
        FROM `transaction`
        ORDER BY Transaction_datetime DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    con.close()

    table_rows = ""

    for row in rows:
        status = str(row.get("fraud_status") or "Normal")
        status_class = "fraud" if status.lower() == "fraud" else "normal"

        table_rows += f"""
        <tr>
            <td>{row.get('Transaction_ID', '')}</td>
            <td>{row.get('Account_ID', '')}</td>
            <td>{row.get('Transaction_datetime', '')}</td>
            <td>₹{row.get('amount', 0)}</td>
            <td>{row.get('Transaction_Type', '')}</td>
            <td>{row.get('channel', '')}</td>
            <td>{row.get('region', '')}</td>
            <td><span class="{status_class}">{status}</span></td>
        </tr>
        """

    if not table_rows:
        table_rows = """
        <tr>
            <td colspan="8">No transactions found.</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial Transactions</title>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }}

            header {{
                background: #172554;
                color: white;
                padding: 22px 30px;
            }}

            header h2 {{
                margin: 0;
            }}

            .container {{
                padding: 25px;
            }}

            .card {{
                background: white;
                padding: 22px;
                border-radius: 12px;
                box-shadow: 0 3px 12px #00000012;
            }}

            .top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 15px;
                flex-wrap: wrap;
                margin-bottom: 20px;
            }}

            input {{
                padding: 11px;
                width: 280px;
                max-width: 100%;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
            }}

            .count {{
                background: #dbeafe;
                color: #1d4ed8;
                padding: 10px 14px;
                border-radius: 8px;
                font-weight: bold;
            }}

            .table-box {{
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 950px;
            }}

            th {{
                background: #e2e8f0;
                padding: 13px;
                text-align: left;
                white-space: nowrap;
            }}

            td {{
                padding: 13px;
                border-bottom: 1px solid #e2e8f0;
                white-space: nowrap;
            }}

            tr:hover {{
                background: #f8fafc;
            }}

            .fraud {{
                background: #fee2e2;
                color: #b91c1c;
                padding: 6px 10px;
                border-radius: 6px;
                font-weight: bold;
            }}

            .normal {{
                background: #dcfce7;
                color: #166534;
                padding: 6px 10px;
                border-radius: 6px;
                font-weight: bold;
            }}

            .back {{
                display: inline-block;
                margin-bottom: 18px;
                color: #1d4ed8;
                text-decoration: none;
                font-weight: bold;
            }}
        </style>
    </head>

    <body>
        <header>
            <h2>Financial Transactions</h2>
            <p>View and search all transaction records</p>
        </header>

        <div class="container">
            <a class="back" href="/">← Back to Dashboard</a>

            <div class="card">
                <div class="top">
                    <h3>Transaction Records</h3>
                    <span class="count">Total Records: {len(rows)}</span>
                    <input
                        type="text"
                        id="searchBox"
                        placeholder="Search transactions..."
                        onkeyup="searchTable()"
                    >
                </div>

                <div class="table-box">
                    <table id="transactionTable">
                        <thead>
                            <tr>
                                <th>Transaction ID</th>
                                <th>Account ID</th>
                                <th>Date & Time</th>
                                <th>Amount</th>
                                <th>Type</th>
                                <th>Channel</th>
                                <th>Region</th>
                                <th>Status</th>
                            </tr>
                        </thead>

                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            function searchTable() {{
                let input = document.getElementById("searchBox");
                let filter = input.value.toLowerCase();
                let table = document.getElementById("transactionTable");
                let rows = table.getElementsByTagName("tr");

                for (let i = 1; i < rows.length; i++) {{
                    let text = rows[i].innerText.toLowerCase();
                    rows[i].style.display =
                        text.includes(filter) ? "" : "none";
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.route("/add", methods=["GET", "POST"])
def add():
    message = ""
    status = ""

    if request.method == "POST":
        tid = request.form["transaction_id"].strip()
        aid = request.form["account_id"].strip()
        amount = int(request.form["amount"])
        typ = request.form["transaction_type"].strip()
        channel = request.form["channel"].strip()
        region = request.form["region"].strip()

        transaction_datetime = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        status = check_risk(amount, channel, typ)

        db = config.connect()
        cur = db.cursor()

        sql = """
        INSERT INTO transaction
        (Transaction_ID, Account_ID, Transaction_datetime,
         amount, Transaction_Type, channel, region, fraud_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            tid, aid, transaction_datetime, amount,
            typ, channel, region, status
        )

        try:
            cur.execute(sql, values)
            db.commit()
            message = f"Transaction added successfully. Status: {status}"
        except Exception as e:
            db.rollback()
            message = "Unable to add transaction. Check the Transaction ID and Account ID."
        finally:
            cur.close()
            db.close()

    result_class = "success" if status == "Normal" else "warning"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Transaction</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }}

            body {{
                margin: 0;
                background: #f1f5f9;
                color: #1e293b;
            }}

            .header {{
                background: #111827;
                color: white;
                padding: 22px 35px;
            }}

            .header h2 {{
                margin: 0;
            }}

            .header p {{
                color: #cbd5e1;
                margin-bottom: 0;
            }}

            .container {{
                max-width: 760px;
                margin: 35px auto;
                padding: 0 18px;
            }}

            .form-card {{
                background: white;
                padding: 30px;
                border-radius: 14px;
                box-shadow: 0 4px 18px #0f172a12;
            }}

            .form-card h2 {{
                margin-top: 0;
                color: #1d4ed8;
            }}

            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}

            .field {{
                margin-bottom: 18px;
            }}

            label {{
                display: block;
                margin-bottom: 8px;
                font-size: 14px;
                font-weight: bold;
            }}

            input {{
                width: 100%;
                padding: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                font-size: 15px;
            }}

            input:focus {{
                outline: 2px solid #93c5fd;
                border-color: #2563eb;
            }}

            button {{
                width: 100%;
                padding: 13px;
                border: none;
                border-radius: 7px;
                background: #2563eb;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }}

            button:hover {{
                background: #1d4ed8;
            }}

            .message {{
                padding: 14px;
                border-radius: 7px;
                margin-bottom: 20px;
            }}

            .success {{
                background: #dcfce7;
                color: #166534;
            }}

            .warning {{
                background: #fee2e2;
                color: #991b1b;
            }}

            .links {{
                display: flex;
                gap: 18px;
                flex-wrap: wrap;
                margin-top: 22px;
            }}

            .links a {{
                color: #2563eb;
                text-decoration: none;
                font-size: 14px;
            }}

            @media (max-width: 550px) {{
                .grid {{
                    grid-template-columns: 1fr;
                    gap: 0;
                }}

                .form-card {{
                    padding: 20px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="header">
            <h2>Financial Risk Analysis</h2>
            <p>Add a new financial transaction</p>
        </div>

        <div class="container">
            <div class="form-card">
                <h2>Add Transaction</h2>
                <p>Enter the transaction details below.</p>

                {"<div class='message " + result_class + "'>" + message + "</div>" if message else ""}

                <form method="POST">
                    <div class="grid">
                        <div class="field">
                            <label>Transaction ID</label>
                            <input name="transaction_id" required>
                        </div>

                        <div class="field">
                            <label>Account ID</label>
                            <input name="account_id" required>
                        </div>

                        <div class="field">
                            <label>Amount</label>
                            <input name="amount" type="number" step="1" required>
                        </div>

                        <div class="field">
                            <label>Transaction Type</label>
                            <input name="transaction_type"
                                   placeholder="Credit / Debit / Transfer"
                                   required>
                        </div>

                        <div class="field">
                            <label>Channel</label>
                            <input name="channel"
                                   placeholder="Mobile / Web / ATM"
                                   required>
                        </div>

                        <div class="field">
                            <label>Region</label>
                            <input name="region" required>
                        </div>
                    </div>

                    <button type="submit">Add Transaction</button>
                </form>

                <div class="links">
                    <a href="/">Dashboard</a>
                    <a href="/transactions">All Transactions</a>
                    <a href="/overview">Financial Overview</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
@app.route("/update", methods=["GET", "POST"])
def update():
    message = ""

    if request.method == "POST":
        transaction_id = request.form.get("transaction_id", "").strip()
        field = request.form.get("field", "").strip()
        value = request.form.get("value", "").strip()

        allowed_fields = {
            "Account_ID": "Account ID",
            "Transaction_datetime": "Transaction Date & Time",
            "amount": "Amount",
            "Transaction_Type": "Transaction Type",
            "channel": "Channel",
            "region": "Region"
        }

        if not transaction_id or not value:
            message = "Please fill in all fields."
        elif field not in allowed_fields:
            message = "Please select a valid field."
        else:
            con = config.connect()
            cursor = con.cursor(dictionary=True)

            try:
                cursor.execute(
                    "SELECT * FROM `transaction` WHERE Transaction_ID = %s",
                    (transaction_id,)
                )
                record = cursor.fetchone()

                if not record:
                    message = "Transaction ID not found."
                else:
                    if field == "amount":
                        try:
                            value = int(value)
                        except ValueError:
                            message = "Amount must be a whole number."

                    if not message:
                        updated = dict(record)
                        updated[field] = value

                        new_status = check_risk(
                            float(updated["amount"]),
                            str(updated["channel"]),
                            str(updated["Transaction_Type"])
                        )

                        cursor.execute(
                            f"""
                            UPDATE `transaction`
                            SET `{field}` = %s, fraud_status = %s
                            WHERE Transaction_ID = %s
                            """,
                            (value, new_status, transaction_id)
                        )

                        con.commit()
                        message = (
                            "Transaction updated successfully. "
                            f"Fraud Status: {new_status}"
                        )

            except Exception as e:
                con.rollback()
                message = f"Update failed: {e}"

            finally:
                cursor.close()
                con.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Update Transaction</title>
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }}

            header {{
                background: #172554;
                color: white;
                padding: 22px 30px;
            }}

            header h2 {{ margin: 0; }}

            .container {{
                max-width: 750px;
                margin: 30px auto;
                padding: 20px;
            }}

            .back {{
                display: inline-block;
                margin-bottom: 18px;
                color: #1d4ed8;
                text-decoration: none;
                font-weight: bold;
            }}

            .card {{
                background: white;
                padding: 28px;
                border-radius: 12px;
                box-shadow: 0 3px 12px #00000012;
            }}

            label {{
                display: block;
                margin: 18px 0 8px;
                font-weight: bold;
            }}

            input, select {{
                width: 100%;
                padding: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                font-size: 15px;
            }}

            button {{
                width: 100%;
                margin-top: 24px;
                padding: 13px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 16px;
                cursor: pointer;
            }}

            button:hover {{ background: #1d4ed8; }}

            .message {{
                margin-top: 18px;
                padding: 13px;
                background: #dbeafe;
                border-radius: 7px;
                overflow-wrap: anywhere;
            }}

            .note {{
                color: #64748b;
                font-size: 14px;
                margin-top: 12px;
            }}
        </style>
    </head>

    <body>
        <header>
            <h2>Update Transaction</h2>
            <p>Modify a transaction record</p>
        </header>

        <div class="container">
            <a class="back" href="/">← Back to Dashboard</a>

            <div class="card">
                <h3>Transaction Details</h3>

                <form method="POST">
                    <label>Transaction ID</label>
                    <input
                        type="text"
                        name="transaction_id"
                        placeholder="Enter Transaction ID"
                        required
                    >

                    <label>Field to Update</label>
                    <select name="field" required>
                        <option value="">Select a field</option>
                        <option value="Account_ID">Account ID</option>
                        <option value="Transaction_datetime">Transaction Date & Time</option>
                        <option value="amount">Amount</option>
                        <option value="Transaction_Type">Transaction Type</option>
                        <option value="channel">Channel</option>
                        <option value="region">Region</option>
                    </select>

                    <label>New Value</label>
                    <input
                        type="text"
                        name="value"
                        placeholder="Enter new value"
                        required
                    >

                    <p class="note">
                        Fraud status is recalculated automatically after updating.
                    </p>

                    <button type="submit">Update Transaction</button>
                </form>

                {"<div class='message'>" + message + "</div>" if message else ""}
            </div>
        </div>
    </body>
    </html>
    """
@app.route("/search", methods=["GET", "POST"])
def search():
    result = ""
    message = ""

    if request.method == "POST":
        transaction_id = request.form.get("transaction_id", "").strip()

        if transaction_id:
            con = config.connect()
            cursor = con.cursor(dictionary=True)

            try:
                cursor.execute(
                    """
                    SELECT Transaction_ID, Account_ID, Transaction_datetime,
                           amount, Transaction_Type, channel, region, fraud_status
                    FROM `transaction`
                    WHERE Transaction_ID = %s
                    """,
                    (transaction_id,)
                )

                row = cursor.fetchone()

                if row:
                    result = "<table><tr><th>Field</th><th>Details</th></tr>"

                    for key, value in row.items():
                        if key == "fraud_status":
                            status = str(value or "Normal")
                            css_class = (
                                "fraud" if status.lower() == "fraud"
                                else "normal"
                            )
                            value = (
                                f'<span class="{css_class}">{status}</span>'
                            )

                        result += (
                            f"<tr><td>{key}</td><td>{value}</td></tr>"
                        )

                    result += "</table>"
                else:
                    message = "No transaction found with that ID."

            except Exception:
                message = "Unable to search. Please check your database connection."

            finally:
                cursor.close()
                con.close()
        else:
            message = "Please enter a Transaction ID."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Transaction</title>
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }}

            header {{
                background: #172554;
                color: white;
                padding: 22px 30px;
            }}

            header h2 {{ margin: 0; }}

            .container {{
                max-width: 850px;
                margin: 30px auto;
                padding: 20px;
            }}

            .back {{
                display: inline-block;
                margin-bottom: 18px;
                color: #1d4ed8;
                text-decoration: none;
                font-weight: bold;
            }}

            .card {{
                background: white;
                padding: 28px;
                border-radius: 12px;
                box-shadow: 0 3px 12px #00000012;
            }}

            form {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-bottom: 22px;
            }}

            input {{
                flex: 1;
                min-width: 200px;
                padding: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
            }}

            button {{
                padding: 12px 22px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                cursor: pointer;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 18px;
                overflow-wrap: anywhere;
            }}

            th, td {{
                text-align: left;
                padding: 13px;
                border-bottom: 1px solid #e2e8f0;
            }}

            th {{ background: #e2e8f0; }}

            .fraud {{
                background: #fee2e2;
                color: #b91c1c;
                padding: 6px 10px;
                border-radius: 6px;
                font-weight: bold;
            }}

            .normal {{
                background: #dcfce7;
                color: #166534;
                padding: 6px 10px;
                border-radius: 6px;
                font-weight: bold;
            }}

            .message {{
                padding: 13px;
                background: #dbeafe;
                border-radius: 7px;
            }}

            @media (max-width: 600px) {{
                .container {{ padding: 12px; }}
                .card {{ padding: 18px; }}
            }}
        </style>
    </head>

    <body>
        <header>
            <h2>Search Transaction</h2>
            <p>Find transaction details by ID</p>
        </header>

        <div class="container">
            <a class="back" href="/">← Back to Dashboard</a>

            <div class="card">
                <h3>Find a Transaction</h3>

                <form method="POST">
                    <input
                        type="text"
                        name="transaction_id"
                        placeholder="Enter Transaction ID"
                        required
                    >
                    <button type="submit">Search</button>
                </form>

                {result}
                {"<div class='message'>" + message + "</div>" if message else ""}
            </div>
        </div>
    </body>
    </html>
    """
@app.route("/delete", methods=["GET", "POST"])
def delete():
    message = ""
    message_class = ""

    if request.method == "POST":
        transaction_id = request.form.get("transaction_id", "").strip()

        if not transaction_id:
            message = "Please enter a Transaction ID."
            message_class = "error"
        else:
            con = config.connect()
            cursor = con.cursor()

            try:
                cursor.execute(
                    "SELECT Transaction_ID FROM `transaction` WHERE Transaction_ID = %s",
                    (transaction_id,)
                )

                record = cursor.fetchone()

                if record:
                    cursor.execute(
                        "DELETE FROM `transaction` WHERE Transaction_ID = %s",
                        (transaction_id,)
                    )
                    con.commit()
                    message = "Transaction deleted successfully."
                    message_class = "success"
                else:
                    message = "Transaction ID not found."
                    message_class = "error"

            except Exception:
                con.rollback()
                message = "Unable to delete this transaction."
                message_class = "error"

            finally:
                cursor.close()
                con.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delete Transaction</title>
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }}

            header {{
                background: #172554;
                color: white;
                padding: 22px 30px;
            }}

            header h2 {{ margin: 0; }}

            .container {{
                max-width: 650px;
                margin: 35px auto;
                padding: 20px;
            }}

            .back {{
                display: inline-block;
                margin-bottom: 18px;
                color: #1d4ed8;
                text-decoration: none;
                font-weight: bold;
            }}

            .card {{
                background: white;
                padding: 28px;
                border-radius: 12px;
                box-shadow: 0 3px 12px #00000012;
            }}

            label {{
                display: block;
                margin: 20px 0 8px;
                font-weight: bold;
            }}

            input {{
                width: 100%;
                padding: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                font-size: 15px;
            }}

            button {{
                width: 100%;
                margin-top: 22px;
                padding: 13px;
                background: #dc2626;
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 16px;
                cursor: pointer;
            }}

            button:hover {{ background: #b91c1c; }}

            .success, .error {{
                margin-top: 20px;
                padding: 13px;
                border-radius: 7px;
                overflow-wrap: anywhere;
            }}

            .success {{
                background: #dcfce7;
                color: #166534;
            }}

            .error {{
                background: #fee2e2;
                color: #b91c1c;
            }}

            .note {{
                color: #64748b;
                font-size: 14px;
                margin-top: 12px;
            }}
        </style>
    </head>

    <body>
        <header>
            <h2>Delete Transaction</h2>
            <p>Remove a transaction record</p>
        </header>

        <div class="container">
            <a class="back" href="/">← Back to Dashboard</a>

            <div class="card">
                <h3>Transaction Details</h3>
                <p>Enter the ID of the transaction you want to delete.</p>

                <form method="POST"
                      onsubmit="return confirm('Are you sure you want to delete this transaction?');">

                    <label>Transaction ID</label>
                    <input
                        type="text"
                        name="transaction_id"
                        placeholder="Enter Transaction ID"
                        required
                    >

                    <p class="note">
                        Deleting a transaction cannot be undone.
                    </p>

                    <button type="submit">Delete Transaction</button>
                </form>

                {"<div class='" + message_class + "'>" + message + "</div>" if message else ""}
            </div>
        </div>
    </body>
    </html>
    """
@app.route("/flagged")
def flagged():
    con = config.connect()
    cursor = con.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT Transaction_ID, Account_ID, Transaction_datetime,
                   amount, Transaction_Type, channel, region, fraud_status
            FROM `transaction`
            WHERE LOWER(fraud_status) = 'fraud'
            ORDER BY Transaction_datetime DESC
        """)

        rows = cursor.fetchall()

    finally:
        cursor.close()
        con.close()

    table_rows = ""

    for row in rows:
        table_rows += f"""
        <tr>
            <td>{row.get('Transaction_ID', '')}</td>
            <td>{row.get('Account_ID', '')}</td>
            <td>{row.get('Transaction_datetime', '')}</td>
            <td>₹{row.get('amount', 0)}</td>
            <td>{row.get('Transaction_Type', '')}</td>
            <td>{row.get('channel', '')}</td>
            <td>{row.get('region', '')}</td>
            <td><span class="fraud">Fraud</span></td>
        </tr>
        """

    if not table_rows:
        table_rows = """
        <tr>
            <td colspan="8">No flagged transactions found.</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flagged Transactions</title>
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }}

            header {{
                background: #172554;
                color: white;
                padding: 22px 30px;
            }}

            header h2 {{ margin: 0; }}

            .container {{ padding: 25px; }}

            .back {{
                display: inline-block;
                margin-bottom: 18px;
                color: #1d4ed8;
                text-decoration: none;
                font-weight: bold;
            }}

            .card {{
                background: white;
                padding: 22px;
                border-radius: 12px;
                box-shadow: 0 3px 12px #00000012;
            }}

            .top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 15px;
                flex-wrap: wrap;
                margin-bottom: 20px;
            }}

            .count {{
                background: #fee2e2;
                color: #b91c1c;
                padding: 10px 14px;
                border-radius: 8px;
                font-weight: bold;
            }}

            input {{
                padding: 11px;
                width: 280px;
                max-width: 100%;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
            }}

            .table-box {{ overflow-x: auto; }}

            table {{
                width: 100%;
                min-width: 950px;
                border-collapse: collapse;
            }}

            th {{
                background: #e2e8f0;
                padding: 13px;
                text-align: left;
            }}

            td {{
                padding: 13px;
                border-bottom: 1px solid #e2e8f0;
                white-space: nowrap;
            }}

            tr:hover {{ background: #f8fafc; }}

            .fraud {{
                background: #fee2e2;
                color: #b91c1c;
                padding: 6px 10px;
                border-radius: 6px;
                font-weight: bold;
            }}
        </style>
    </head>

    <body>
        <header>
            <h2>Flagged Transactions</h2>
            <p>Transactions identified as potentially fraudulent by your rules</p>
        </header>

        <div class="container">
            <a class="back" href="/">← Back to Dashboard</a>

            <div class="card">
                <div class="top">
                    <h3>Fraud Records</h3>
                    <span class="count">Flagged: {len(rows)}</span>

                    <input
                        type="text"
                        id="searchBox"
                        placeholder="Search flagged records..."
                        onkeyup="searchTable()"
                    >
                </div>

                <div class="table-box">
                    <table id="fraudTable">
                        <thead>
                            <tr>
                                <th>Transaction ID</th>
                                <th>Account ID</th>
                                <th>Date & Time</th>
                                <th>Amount</th>
                                <th>Type</th>
                                <th>Channel</th>
                                <th>Region</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            function searchTable() {{
                let filter = document.getElementById("searchBox")
                    .value.toLowerCase();

                let rows = document.getElementById("fraudTable")
                    .getElementsByTagName("tr");

                for (let i = 1; i < rows.length; i++) {{
                    rows[i].style.display =
                        rows[i].innerText.toLowerCase().includes(filter)
                        ? "" : "none";
                }}
            }}
        </script>
    </body>
    </html>
    """
@app.route("/all-summaries")
def all_summaries():
    import json

    connection = config.connect()
    cursor = connection.cursor(dictionary=True)

    # 1. TRANSACTIONS BY TYPE
    cursor.execute("""
        SELECT
            CASE
                WHEN LOWER(TRIM(Transaction_Type)) = 'credit'
                    THEN 'Credit'
                WHEN LOWER(TRIM(Transaction_Type)) = 'debit'
                    THEN 'Debit'
                WHEN LOWER(TRIM(Transaction_Type)) = 'bank transfer'
                    THEN 'Bank Transfer'
                WHEN LOWER(TRIM(Transaction_Type)) = 'upi'
                    THEN 'UPI'
            END AS category,
            COUNT(*) AS total
        FROM `transaction`
        WHERE LOWER(TRIM(Transaction_Type))
              IN ('credit', 'debit', 'bank transfer', 'upi')
        GROUP BY
            CASE
                WHEN LOWER(TRIM(Transaction_Type)) = 'credit'
                    THEN 'Credit'
                WHEN LOWER(TRIM(Transaction_Type)) = 'debit'
                    THEN 'Debit'
                WHEN LOWER(TRIM(Transaction_Type)) = 'bank transfer'
                    THEN 'Bank Transfer'
                WHEN LOWER(TRIM(Transaction_Type)) = 'upi'
                    THEN 'UPI'
            END
        ORDER BY total DESC
    """)
    type_rows = cursor.fetchall()

    # 2. TRANSACTIONS BY CHANNEL
    cursor.execute("""
        SELECT
            CASE
                WHEN LOWER(TRIM(channel)) = 'branch'
                    THEN 'Branch'
                WHEN LOWER(TRIM(channel)) = 'bank transfer'
                    THEN 'Bank Transfer'
                WHEN LOWER(TRIM(channel)) = 'online'
                    THEN 'Online'
                WHEN LOWER(TRIM(channel)) = 'atm'
                    THEN 'ATM'
                WHEN LOWER(TRIM(channel)) = 'web'
                    THEN 'Web'
            END AS category,
            COUNT(*) AS total
        FROM `transaction`
        WHERE LOWER(TRIM(channel))
              IN ('branch', 'bank transfer', 'online', 'atm', 'web')
        GROUP BY
            CASE
                WHEN LOWER(TRIM(channel)) = 'branch'
                    THEN 'Branch'
                WHEN LOWER(TRIM(channel)) = 'bank transfer'
                    THEN 'Bank Transfer'
                WHEN LOWER(TRIM(channel)) = 'online'
                    THEN 'Online'
                WHEN LOWER(TRIM(channel)) = 'atm'
                    THEN 'ATM'
                WHEN LOWER(TRIM(channel)) = 'web'
                    THEN 'Web'
            END
        ORDER BY total DESC
    """)
    channel_rows = cursor.fetchall()

    # 3. TRANSACTIONS BY FRAUD STATUS
    cursor.execute("""
        SELECT
            CASE
                WHEN LOWER(TRIM(fraud_status)) = 'fraud'
                    THEN 'Fraud'
                ELSE 'Normal'
            END AS category,
            COUNT(*) AS total
        FROM `transaction`
        GROUP BY
            CASE
                WHEN LOWER(TRIM(fraud_status)) = 'fraud'
                    THEN 'Fraud'
                ELSE 'Normal'
            END
    """)
    status_rows = cursor.fetchall()

    # 4. TRANSACTIONS BY AMOUNT RANGE
    cursor.execute("""
        SELECT
            CASE
                WHEN amount <= 0 THEN 'Zero/Negative'
                WHEN amount < 10000 THEN '1 - 9,999'
                WHEN amount < 25000 THEN '10,000 - 24,999'
                WHEN amount < 50000 THEN '25,000 - 49,999'
                ELSE '50,000 and above'
            END AS category,
            COUNT(*) AS total
        FROM `transaction`
        GROUP BY category
        ORDER BY MIN(amount)
    """)
    amount_rows = cursor.fetchall()

    cursor.close()

    def make_table(rows):
        html = """
        <table>
            <tr>
                <th>Category</th>
                <th>Total Transactions</th>
            </tr>
        """

        for row in rows:
            html += f"""
            <tr>
                <td>{row['category']}</td>
                <td>{row['total']}</td>
            </tr>
            """

        html += "</table>"
        return html

    def chart_data(rows):
        return {
            "labels": [
                str(row["category"])
                for row in rows
            ],
            "values": [
                int(row["total"] or 0)
                for row in rows
            ]
        }

    type_data = chart_data(type_rows)
    channel_data = chart_data(channel_rows)
    status_data = chart_data(status_rows)
    amount_data = chart_data(amount_rows)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>All Transaction Summaries</title>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 25px;
                background: #f4f6f9;
            }}

            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}

            .summary-box {{
                background: white;
                padding: 22px;
                margin: 25px auto;
                max-width: 1000px;
                border-radius: 10px;
                box-shadow: 0 2px 8px #cccccc;
            }}

            .summary-content {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 25px;
                align-items: center;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th, td {{
                border: 1px solid #cccccc;
                padding: 12px;
                text-align: center;
            }}

            th {{
                background: #e8edf5;
            }}

            canvas {{
                max-height: 300px;
                width: 100%;
            }}

            a {{
                display: inline-block;
                margin-bottom: 15px;
                text-decoration: none;
                color: #2456a6;
            }}

            @media (max-width: 700px) {{
                .summary-content {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>

    <body>

        <a href="/">&#8592; Back to Dashboard</a>

        <h1>All Transaction Summaries</h1>

        <div class="summary-box">
            <h2>Transactions by Type</h2>
            <div class="summary-content">
                <div>{make_table(type_rows)}</div>
                <div><canvas id="typeChart"></canvas></div>
            </div>
        </div>

        <div class="summary-box">
            <h2>Transactions by Channel</h2>
            <div class="summary-content">
                <div>{make_table(channel_rows)}</div>
                <div><canvas id="channelChart"></canvas></div>
            </div>
        </div>

        <div class="summary-box">
            <h2>Transactions by Fraud Status</h2>
            <div class="summary-content">
                <div>{make_table(status_rows)}</div>
                <div><canvas id="statusChart"></canvas></div>
            </div>
        </div>

        <div class="summary-box">
            <h2>Transactions by Amount Range</h2>
            <div class="summary-content">
                <div>{make_table(amount_rows)}</div>
                <div><canvas id="amountChart"></canvas></div>
            </div>
        </div>

        <script>
            const typeData = {json.dumps(type_data)};
            const channelData = {json.dumps(channel_data)};
            const statusData = {json.dumps(status_data)};
            const amountData = {json.dumps(amount_data)};

            function createBarChart(elementId, data, title) {{
                new Chart(document.getElementById(elementId), {{
                    type: 'bar',
                    data: {{
                        labels: data.labels,
                        datasets: [{{
                            label: 'Total Transactions',
                            data: data.values,
                            backgroundColor: '#4776c5'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: title
                            }},
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    precision: 0
                                }}
                            }}
                        }}
                    }}
                }});
            }}

            createBarChart(
                'typeChart',
                typeData,
                'Transactions by Type'
            );

            createBarChart(
                'channelChart',
                channelData,
                'Transactions by Channel'
            );

            new Chart(document.getElementById('statusChart'), {{
                type: 'doughnut',
                data: {{
                    labels: statusData.labels,
                    datasets: [{{
                        data: statusData.values,
                        backgroundColor: ['#2ecc71', '#e74c3c']
                    }}]
                }},
                options: {{
                    responsive: true
                }}
            }});

            createBarChart(
                'amountChart',
                amountData,
                'Transactions by Amount Range'
            );
        </script>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)