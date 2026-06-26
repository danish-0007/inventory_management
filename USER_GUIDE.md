# Your Shop System — How To Use It

A simple guide for running your shop on the computer. No computer knowledge needed — just follow the steps.

---

## Table of Contents

1. [Logging In](#1-logging-in)
2. [The Main Screen](#2-the-main-screen)
3. [Making a Sale](#3-making-a-sale)
4. [Receiving Stock From a Supplier](#4-receiving-stock-from-a-supplier)
5. [Selling on Credit — How It Works](#5-selling-on-credit--how-it-works)
6. [Receiving Payment From a Customer](#6-receiving-payment-from-a-customer)
7. [Checking Who Owes You Money](#7-checking-who-owes-you-money)
8. [Seeing All Your Customers At a Glance](#8-seeing-all-your-customers-at-a-glance)
9. [Adding a New Customer](#9-adding-a-new-customer)
10. [Writing Notes About a Customer](#10-writing-notes-about-a-customer)
11. [Checking Your Stock](#11-checking-your-stock)
12. [Batches and Expiry Dates](#12-batches-and-expiry-dates)
13. [Shop Settings](#13-shop-settings)
14. [Common Questions](#14-common-questions)

---

## 1. Logging In

1. Open the browser on your computer.
2. Go to the address your computer person gave you.
3. Type your username and password.
4. Click the login button.

You will land on your shop's screen automatically.

---

## 2. The Main Screen

Across the top, you will see a row of words — these are your sections:

| What you see | What it's for |
|---|---|
| **New Sale** | Sell something to a customer |
| **Receive Stock** | Stock arrived from a supplier |
| **Products** | See/manage what you sell |
| **Batches** | See your stock by batch and expiry date |
| **History** | Look back at old sales and purchases |
| **Overdue Bills** | See who hasn't paid you and is late |
| **Top Customers** | See all your customers in one list |
| **Configuration** | Shop settings — name, address, etc. |

You don't need to remember all of these right now. Most days, you will only use **New Sale**, **Receive Stock**, and once in a while **Overdue Bills**.

---

## 3. Making a Sale

This is what you'll do most often — someone walks in to buy something.

**Steps:**

1. Click **New Sale**. A form opens.
2. **Customer**: if it's a regular customer, type their name and pick them from the list. If you don't pick anyone, it automatically uses "Walk-in Customer" — fine for someone you don't know.
3. **Payment Method**: tap one —
   - **Cash** — they're paying you cash right now
   - **UPI** — they paid you by phone/UPI right now
   - **Credit** — they're taking the goods now and will pay you later (see [Section 5](#5-selling-on-credit--how-it-works))
   - **Other** — any other instant payment
4. Click **Add a line** to add what they're buying.
5. Type the product name and pick it from the list.
6. The system automatically picks the oldest stock first (so nothing expires sitting in your store).
7. Type how much they're buying (the quantity).
8. The price fills in automatically — change it if you're giving a special price.
9. If you're giving a discount, type the percentage in the **Discount %** box.
10. Add more lines if they're buying more than one item.
11. Check the **Total Amount** at the bottom right — that's what to collect.
12. Click **Confirm & Print Receipt**.

That's it. Your stock goes down automatically, and a receipt opens that you can print and hand to the customer.

**Why it works this way:** You don't have to think about which batch to sell or do any maths — the system does the stock and the totals for you. You just need to know what's being bought and how it's being paid for.

---

## 4. Receiving Stock From a Supplier

When new stock arrives at your shop:

1. Click **Receive Stock**.
2. Pick the **Supplier** you bought from.
3. Click **Add a line**.
4. Type the product name and pick it.
5. A batch number is created automatically — you can change it if you want to use your own numbering.
6. Type how many units arrived (**Qty**) and what you paid per unit (**Cost Price**).
7. If the product has an expiry date, type it in **Expiry Date**.
8. Click **Receive**.

Your stock goes up immediately, and a new batch is created so you can track its expiry later.

**Why it works this way:** Every purchase becomes its own "batch" with its own expiry date, so the system always knows exactly which stock is oldest and which is about to expire — and always sells the oldest first.

---

## 5. Selling on Credit — How It Works

Some customers (especially regular farmers) will want to "put it on their account" and pay you later. This is what **Credit** payment method is for.

**What happens when you sell on Credit:**

- The sale goes through immediately, stock goes down, receipt prints — exactly the same as a cash sale.
- But the system marks that bill as **unpaid**, and remembers it.
- Every customer has a **Credit Period** — normally 30 days (you can change this per customer, see [Section 9](#9-adding-a-new-customer)). The bill becomes **overdue** if it isn't paid within that many days.
- The printed receipt for a Credit sale shows in red: **"Amount Due: ₹X by [date]"** — so the customer themselves has a reminder of when they need to pay you.

**Why it works this way:** This way you never have to remember in your head who owes you what, or by when — the system keeps the running total for every customer, and tells you exactly when a bill is overdue (see [Section 7](#7-checking-who-owes-you-money)).

**Cash, UPI, and Other are different:** these are treated as paid in full the moment you confirm the sale — there's nothing to chase later, because the money's already in hand.

---

## 6. Receiving Payment From a Customer

When a credit customer comes to pay you back (in full or in part):

1. Find the customer — either through **Top Customers** or by searching Contacts.
2. Open their record.
3. Click the **Receive Payment** button (it's near their name, with the village and crops information).
4. Type how much they're paying you.
5. Pick how they're paying (Cash / UPI / Other).
6. Save.

**What happens automatically:** if this customer has more than one unpaid bill, the payment is applied to their **oldest** unpaid bill first. If there's money left over after that bill is fully paid, it automatically rolls onto their next-oldest bill, and so on.

**Example:** Suppose a customer owes you ₹2,000 from three weeks ago and ₹3,000 from last week. They come in and pay you ₹4,000.
- ₹2,000 pays off the three-weeks-ago bill completely.
- The remaining ₹2,000 goes toward the ₹3,000 bill, leaving ₹1,000 still owed on that one.

You don't have to work this out yourself or decide which bill the money goes to — the system always pays the oldest debt first, which is the fair and simple way to do it.

**Made a mistake?** If you entered the wrong amount, open that payment from the customer's **Payments** button (top of their screen) and delete it — the bills it was applied to go back to being owed, exactly as before. Then enter the correct payment again.

---

## 7. Checking Who Owes You Money

Click **Overdue Bills** at the top.

You'll see a list of every bill that is **currently late** — sorted so you can see at a glance:

| Column | Meaning |
|---|---|
| Customer | Who owes the money |
| Products | What they bought |
| Order Date | When they bought it |
| Due Date | When they were supposed to pay |
| Days Overdue | How many days late they are |
| Amount Outstanding | How much they still owe |

Rows in **red** are more than 60 days late — these need your attention first.

If a bill isn't overdue yet, it won't show up here at all — this list is only for bills that need chasing right now.

**Why it works this way:** Instead of going through your old receipts trying to remember who hasn't paid, this list does that work for you, automatically, every day.

---

## 8. Seeing All Your Customers At a Glance

Click **Top Customers**.

This single list shows every customer who has ever bought from you, with:

- **Village** — where they're from
- **Credit Period** — how many days they're given to pay
- **Risk** — a colored badge:
  - 🟢 **Green** — no overdue bills, no concern
  - 🟡 **Yellow** — one bill currently overdue
  - 🔴 **Red** — either a bill more than 60 days late, or two or more bills overdue at once — needs your attention
- **Total Purchased** — everything they've ever bought from you, in total
- **Total Outstanding** — how much they currently owe you

**To sort:** click any column heading — for example, click "Total Outstanding" to see your biggest debtors at the top.

**To group by village:** click **Group By** near the top, then **Village**. This bunches all customers from the same village together, and shows you the total for that whole village.

**Why it works this way:** Instead of separate reports for "biggest customers," "who's from which village," and "who's risky," it's all one list — just click the column you care about.

---

## 9. Adding a New Customer

1. Go to **Contacts** (you can reach this from the apps menu, or it opens automatically when you type a new name while making a sale).
2. Click **New**.
3. Type their name.
4. Scroll down to **Credit & Crops** and fill in:
   - **Village** — type the name; if it doesn't exist yet, you can create it right there
   - **Credit Period (Days)** — defaults to 30, change it if this customer needs longer or shorter
   - **Crops Grown** — tap to add one or more crops they grow
5. Save.

That's it — this customer is now ready to be picked in **New Sale**, and their bills/payments will track automatically from now on.

---

## 10. Writing Notes About a Customer

Useful for remembering things like "asked about fertilizer for cotton" or "field had a pest problem."

1. Open the customer's record.
2. Scroll to **Notes & Field History**.
3. You'll see their most recent 3 notes there already.
4. Click **View All Notes** to see everything, or to add a new one.
5. Click **New**, type your note, and save — the date and your name are filled in automatically.

---

## 11. Checking Your Stock

Click **Products → Stock Overview** to see every product and how much you have, with a simple status:

- **OK** — plenty of stock
- **Low** — getting close to your reorder point
- **Out of Stock** — none left

Click **Products → Low Stock** to see only the ones you need to reorder soon.

---

## 12. Batches and Expiry Dates

Every time you receive stock, it becomes its own "batch" with its own expiry date. This lets the shop:

- Always sell the **oldest** stock first when you make a sale (so nothing goes to waste sitting at the back)
- Warn you ahead of time when something is about to expire

Click **Batches → Expiring Soon** to see what needs to be sold or dealt with first.

---

## 13. Shop Settings

Click **Configuration → Shop Settings** to set up (once, when you start using the system):

| Setting | What it does |
|---|---|
| Shop Name, Address, Phone | Printed at the top of every receipt |
| Logo | Your shop logo, printed on receipts |
| GST Number | Printed on receipts if you have one |
| Receipt Footer | A thank-you message at the bottom of every receipt |
| Expiry Warning (days) | How many days before expiry a batch should be flagged "Expiring Soon" |
| Default Credit Period (days) | The credit period given to a brand-new customer, unless you change it for them individually |
| Walk-in Customer | The customer automatically picked for sales when you don't choose anyone |

This screen can only be changed by the shop Manager — staff with a Cashier login can see it but not change it, so daily settings stay safe.

---

## 14. Common Questions

**Q: I sold something on Credit by mistake — it should have been Cash.**
A: Open the sale from **History → Sales**, but note that the amount/date/items on a confirmed sale can't be edited (this protects your receipt records from accidental changes). The cleanest fix is to record a payment for the full amount right away through **Receive Payment** — that settles it immediately, the same as if it had been a cash sale from the start.

**Q: A customer paid me extra by mistake / I want to record an advance.**
A: You can still enter the payment — if they have no unpaid bills (or you pay more than they owe), the extra amount is simply recorded as paid, ready to apply against their next bill.

**Q: Why did a bill suddenly turn red overnight?**
A: The system checks every bill once a day automatically, and updates a bill to "overdue" the moment it crosses its due date — even if nobody touched the computer that day.

**Q: Can I trust the totals?**
A: Yes — every total (stock, money owed, money paid) is calculated by the system itself from your actual sales and payments. You never need to do this maths by hand.

**Q: What if I'm not sure about something?**
A: Nothing in this system deletes your sales history. If you're ever unsure, it's safe to look around — the worst that can happen is you click into a screen you didn't mean to. Just click **Agro Inventory** at the top-left to go back to the main menu.
