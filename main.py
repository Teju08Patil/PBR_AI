import os
from datetime import datetime
from db import init_db, get_connection
import httpx


from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

_host = os.environ.get("HOST", "127.0.0.1")
_port = int(os.environ.get("PORT", "8000"))

mcp = FastMCP(
    "simple-mcp",
    host=_host,
    port=_port,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

init_db()

@mcp.tool()
def ping() -> str:
    """Check if the server is alive."""
    return "pong"


@mcp.tool()
def  log_expense(amount: float, category: str, note: str = "") -> str:

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO expenses (amount, category, note)
        VALUES (?, ?, ?, ?)
        """,
        (amount, category, note),
    )

    conn.commit()
    conn.close()

    return f"Expense added: ₹{amount} for {category}"



@mcp.tool()
def summarise_spending():

    conn = get_connection()
    cursor = conn.cursor()

    # Get total spending by category
    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        GROUP BY category
    """)

    data = cursor.fetchall()

    conn.close()

    # If no data
    if len(data) == 0:
        return "No expenses found"

    message = "Spending Summary\n\n"

    total = 0

    # Loop through results
    for item in data:

        category = item[0]
        amount = item[1]

        message += category + ": ₹" + str(amount) + "\n"

        total = total + amount

    message += "\nTotal Spending: ₹" + str(total)

    return message

@mcp.tool()
def budget_alert(category: str, limit: float) -> str:
    """Check budget for category"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT SUM(amount)
        FROM expenses
        WHERE category = ?
        """,
        (category,),
    )

    spent = cursor.fetchone()[0]

    conn.close()

    if spent is None:
        spent = 0

    if spent > limit:
        return (
            f"Budget exceeded!\n"
            f"Spent: ₹{spent}\n"
            f"Limit: ₹{limit}"
        )

    return (
        f"Budget OK\n"
        f"Spent: ₹{spent}\n"
        f"Remaining: ₹{limit - spent}"
    )



def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
