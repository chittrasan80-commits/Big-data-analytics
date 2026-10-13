"""Create report-ready charts from the pipeline outputs (also usable beside Power BI)."""
import argparse, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="outputs")
a = ap.parse_args()
seg = pd.read_csv(os.path.join(a.out, "customer_segments.csv"))
summ = pd.read_csv(os.path.join(a.out, "segment_summary.csv"))
ks = pd.read_csv(os.path.join(a.out, "k_selection.csv"))

fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
ax[0].plot(ks.k, ks.wssse, "o-"); ax[0].set(title="Elbow (WSSSE)", xlabel="k")
ax[1].plot(ks.k, ks.silhouette, "o-", color="tab:green"); ax[1].set(title="Silhouette score", xlabel="k")
plt.tight_layout(); plt.savefig(os.path.join(a.out, "k_selection.png"), dpi=130); plt.close()

plt.figure(figsize=(6.5, 4)); plt.bar(summ.Segment, summ.customers, color="tab:blue")
plt.title("Customers per segment"); plt.xticks(rotation=20, ha="right"); plt.tight_layout()
plt.savefig(os.path.join(a.out, "segment_sizes.png"), dpi=130); plt.close()

plt.figure(figsize=(5.5, 5.5)); plt.pie(summ.total_revenue, labels=summ.Segment, autopct="%1.0f%%", startangle=90)
plt.title("Revenue share by segment"); plt.tight_layout()
plt.savefig(os.path.join(a.out, "revenue_share.png"), dpi=130); plt.close()

plt.figure(figsize=(6.5, 4.5))
for name, g in seg.groupby("Segment"):
    plt.scatter(g.Frequency, g.Monetary, s=10, alpha=.6, label=name)
plt.xscale("log"); plt.yscale("log"); plt.xlabel("Frequency (orders)"); plt.ylabel("Monetary (spend)")
plt.title("Segments in Frequency-Monetary space"); plt.legend(fontsize=7); plt.tight_layout()
plt.savefig(os.path.join(a.out, "segments_scatter.png"), dpi=130); plt.close()
print("Charts saved to", a.out)
