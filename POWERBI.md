# Power BI dashboard steps

1. Get Data → Text/CSV → `outputs/customer_segments.csv` and `outputs/segment_summary.csv`.
2. Visuals:
   - Card: total customers, total revenue (sum of `Monetary`)
   - Donut: revenue by `Segment` (from segment_summary → `total_revenue`)
   - Bar: customers by `Segment`
   - Scatter: X = Frequency, Y = Monetary, Legend = Segment, Details = CustomerID (log axes)
   - Map/Bar: revenue by `Country`
   - Table: top 20 customers by Monetary
3. Add a Segment slicer so the whole page filters together.
4. Save as `dashboard.pbix` and add a screenshot to `docs/`.
