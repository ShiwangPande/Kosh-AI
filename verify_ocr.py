
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://kosh:kosh_secret@db:5432/kosh_ai')
    cur = conn.cursor()
    # Get latest invoice
    cur.execute("SELECT id, ocr_status, total_amount, invoice_date, supplier_id, ocr_raw_text FROM invoices WHERE id = 'bdb96301-535c-4efd-85fc-68d7c2f3b759'")
    row = cur.fetchone()
    
    if row:
        print(f"ID: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"Total: {row[2]}")
        print(f"Date: {row[3]}")
        print(f"Supplier ID: {row[4]}")
        print("--- RAW TEXT START ---")
        print(row[5])
        print("--- RAW TEXT END ---")
        
        if row[4]:
            cur.execute("SELECT name FROM suppliers WHERE id = %s", (row[4],))
            res = cur.fetchone()
            if res:
                print(f"Supplier Name: {res[0]}")
            else:
                print("Supplier Name: Not Found (integrity error?)")
        else:
            print("Supplier Name: [MISSING]")
        
        # Check items
        cur.execute("SELECT count(*) FROM invoice_items WHERE invoice_id = %s", (row[0],))
        cnt = cur.fetchone()[0]
        print(f"Items Count: {cnt}")
        
        # Print items details
        cur.execute("SELECT raw_description, unit_price, quantity, total_price FROM invoice_items WHERE invoice_id = %s", (row[0],))
        items = cur.fetchall()
        print("--- ITEMS ---")
        for item in items:
            desc, price, qty, total = item
            print(f"{desc} | Price: {price} | Qty: {qty} | Total: {total}")
            
    else:
        print("No invoices found")

except Exception as e:
    print(f"Error: {e}")
