"""prep_supermarkets.py — supermarket market share over time (Section 4).

Share of Australian supermarket, grocery AND liquor retail turnover taken by
the Woolworths and Coles businesses, financial years 1994-2025, with
everyone else (Franklins until 2001, ALDI from 2001, IGA and other
independents, Costco, independent liquor, convenience) as the remainder.

The perimeter is food plus liquor on both sides, for every year: for most
of this period neither company published supermarket sales without liquor.
Petrol, Coles Express, New Zealand and hotels are excluded wherever the
source separates them. Every figure below is $m and carries its source.

------------------------------------------------------------------- ABS ---
Retail Trade, Australia, June 2025 (cat. 8501.0), Table 11, Original,
July-June sums of A3349862V (Total (State); Supermarket and grocery stores)
+ A3349462J (Total (State); Liquor retailing). CC BY 4.0. The June 2025
release was the last; ABS has ceased the publication.

-------------------------------------------------------- the tax problem ---
ABS turnover includes the tax built into shelf prices in every year:
wholesale sales tax (WST) before July 2000, GST after. Company sales after
July 2000 exclude GST. Both companies restated their pre-2001 sales to
exclude WST so the years would compare across the change, and those
restated figures are used here. So the series is tax-exclusive company
sales over tax-inclusive market turnover throughout, and the bias (shares
read a few points low) runs the same way on both sides of 2000. The data
bears this out: there is no step in either company's share at FY2001.

Where only a WST-inclusive figure exists (Woolworths FY94-96, Coles FY94-96)
it is converted with that company's own published ratio of WST-exclusive to
WST-inclusive sales for the overlapping years (WST_W and WST_C below).

------------------------------------------------------------ WOOLWORTHS ---
Australian supermarkets + its liquor chains (BWS, Dan Murphy's).
  FY94-FY96  Annual Report 1995 (Supermarkets Group, FY91-95) and Annual
             Report 2000 five-year summary (Supermarkets, FY96-00), both
             WST-inclusive, x WST_W. Before FY97 there was no petrol.
  FY97       Concise Report 2001 five-year summary, Total supermarkets,
             WST-excluded (53 weeks; includes ~12 petrol canopies, <0.2%)
  FY98-FY04  Concise Report 2002 and Annual Report 2004 five-year summaries,
             "Food and Liquor" (petrol separate, WST-excluded). FY98 is
             published as equal to Total supermarkets (petrol not split;
             ~49 canopies, under 1%).
  FY05       Annual Report 2006 five-year summary, Food and Liquor
  FY06-FY08  Annual Report 2010 five-year summary, "Australian Food and
             Liquor" (from FY06 the older "Food and Liquor" line includes
             New Zealand after the Progressive acquisition; this one does not)
  FY09-FY11  Annual Report 2012 five-year summary: Australian Food and Liquor
  FY12-FY14  Annual Report 2016 five-year summary: Australian Food and
             Endeavour Drinks Group
  FY15       Annual Report 2016: Australian Food 34,880.5 + Endeavour 7,251.2
  FY16-FY20  Five-year summary 2020: Australian Food + Endeavour Drinks
  FY21-FY25  Five-year summary F25: Australian Food, plus Endeavour Group
             annual reports: Retail segment (Dan Murphy's + BWS). Endeavour
             was demerged in June 2021; it stays in this band so the business
             perimeter does not change mid-series. Endeavour's own FY20 Retail
             (9,286) matches Woolworths' FY20 Endeavour Drinks (9,275).

----------------------------------------------------------------- COLES ---
Supermarkets (Coles, Bi-Lo) + Coles liquor (Liquorland, Vintage Cellars,
1st Choice). Coles Myer's year ended in late July, one month after the ABS
year; the offset is left as is (about 0.4% of a year's growth).
  FY94-FY96  Coles Myer Annual Report 1998 statistical analysis, Food &
             Liquor sales, WST-inclusive, x WST_C. (Before FY94 Liquorland
             was reported in the Specialty group, so the series starts at
             FY94 rather than estimating it.)
  FY97-FY00  Coles Myer Annual Report 2001, "Sales - Adjusted for WST",
             Food and Liquor
  FY01-FY02  Coles Myer Annual Report 2002 historical summary, Food & Liquor
  FY03       Coles Myer Annual Report 2004: Food, Liquor & Fuel segment sales
             "after adjusting for sales relating to Coles Express" (FY03 was
             before Coles Express, and was restated to include Liquorland
             Direct)
  FY04-FY05  Coles Myer Annual Report 2005: segment sales excluding
             concessions, "Excluding Coles Express"
  FY06-FY07  Coles Group Annual Report 2007: Food & Liquor sales
  FY08       DERIVED. Wesfarmers bought Coles in November 2007, so no full
             FY08 accounts were published. Wesfarmers' 2009 Annual Report
             gives FY09 "food and liquor store sales growth ... 6.2 per cent";
             FY08 = FY09 / 1.062.
  FY09-FY12  Wesfarmers full-year reports: Coles division revenue minus
             Coles Express revenue (Express given rounded in the text, so
             these carry about +/-$50m, under 0.05 points)
  FY13-FY17  Wesfarmers results announcements: Coles "Food & Liquor Revenue"
  FY18-FY25  Coles Group: Supermarkets + Liquor sales revenue. FY18 is on both
             bases (Wesfarmers 33,627 vs Coles Group 33,199); the Coles Group
             basis is used from FY18, a step of ~0.3 share points.

Adjustments: 53-week years scaled to 52 weeks (weeks column below).

Output: data/supermarket_share.csv  (one row per year x retailer)
"""

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "supermarket_share.csv"

ABS_SUPERMARKET = {
    1994: 29163.9, 1995: 31377.8, 1996: 34220.8, 1997: 36077.5, 1998: 37665.6,
    1999: 40475.2, 2000: 42573.9, 2001: 45307.6, 2002: 48740.4, 2003: 51803.1,
    2004: 55225.4, 2005: 57332.0, 2006: 60515.9, 2007: 64502.1, 2008: 69968.2,
    2009: 75469.0, 2010: 78817.2, 2011: 81427.8, 2012: 84791.3, 2013: 88371.5,
    2014: 93042.4, 2015: 97654.0, 2016: 100891.8, 2017: 103722.9, 2018: 106899.1,
    2019: 111521.1, 2020: 118981.7, 2021: 124067.0, 2022: 128236.3, 2023: 136577.4,
    2024: 141288.2, 2025: 145401.0,
}
ABS_LIQUOR = {
    1994: 1913.3, 1995: 2081.0, 1996: 2228.9, 1997: 2454.3, 1998: 2662.3,
    1999: 3002.6, 2000: 3318.4, 2001: 3633.6, 2002: 3893.8, 2003: 4529.9,
    2004: 4918.3, 2005: 5298.0, 2006: 5883.7, 2007: 6852.2, 2008: 7339.9,
    2009: 8131.7, 2010: 8607.7, 2011: 9124.0, 2012: 9760.8, 2013: 9864.0,
    2014: 10136.6, 2015: 10647.8, 2016: 11050.0, 2017: 11490.0, 2018: 12058.4,
    2019: 12181.9, 2020: 14055.7, 2021: 16746.3, 2022: 17548.4, 2023: 17902.2,
    2024: 18021.9, 2025: 17834.8,
}

# WST-exclusive / WST-inclusive, from each company's own restatement.
# Woolworths: Total supermarkets, Concise Report 2001 (excl.) over Annual
# Report 2000 (incl.), FY97-FY00.
_W_PAIRS = [(12583.8, 13298.3), (13374.5, 14179.8), (14563.4, 15398.6), (15723.8, 16671.2)]
# Coles: Food and Liquor, Annual Report 2001, adjusted over unadjusted, FY97-FY00.
_C_PAIRS = [(9945.1, 10428.6), (11021.5, 11559.4), (12392.7, 12997.3), (13592.0, 14221.0)]
WST_W = sum(a / b for a, b in _W_PAIRS) / len(_W_PAIRS)
WST_C = sum(a / b for a, b in _C_PAIRS) / len(_C_PAIRS)

# fy: (food $m, liquor $m, weeks). Where only a combined figure is published,
# it is given as food with liquor 0.
WOOLWORTHS = {
    1994: (9829 * WST_W, 0, 52), 1995: (10959 * WST_W, 0, 52),
    1996: (11995.2 * WST_W, 0, 52), 1997: (12583.8, 0, 53),
    1998: (13374.5, 0, 52), 1999: (14247.0, 0, 52), 2000: (15251.3, 0, 52),
    2001: (16772.3, 0, 52), 2002: (19595.0, 0, 53), 2003: (21039.0, 0, 52),
    2004: (21997.6, 0, 52), 2005: (23569.6, 0, 52), 2006: (25602.8, 0, 52),
    2007: (27892.9, 0, 52), 2008: (30662.6, 0, 53),
    2009: (32977.2, 0, 52), 2010: (34675.4, 0, 52), 2011: (36176.1, 0, 52),
    2012: (37549.2, 0, 52), 2013: (40031.2, 0, 53), 2014: (41170.7, 0, 52),
    2015: (34880.5, 7251.2, 52), 2016: (34526, 7589, 52), 2017: (36003, 7882, 52),
    2018: (37589, 8244, 52), 2019: (39635, 8590, 53), 2020: (42151, 9275, 52),
    2021: (43509, 10178, 52), 2022: (45740, 10086, 52), 2023: (48047, 9905, 52),
    2024: (50823, 10246, 53), 2025: (51452, 9950, 52),
}
COLES = {
    1994: (7502.4 * WST_C, 0, 53), 1995: (8152.8 * WST_C, 0, 52),
    1996: (9328.7 * WST_C, 0, 52), 1997: (9945.1, 0, 52), 1998: (11021.5, 0, 52),
    1999: (12392.7, 0, 52), 2000: (13592.0, 0, 53), 2001: (14468.2, 0, 52),
    2002: (15892.4, 0, 52), 2003: (16557.6, 0, 52), 2004: (17969.9, 0, 52),
    2005: (19045.0, 0, 53), 2006: (19626, 0, 52), 2007: (20437, 0, 52),
    2008: ((28799 - 6300) / 1.062, 0, 52),
    2009: (28799 - 6300, 0, 52), 2010: (30002 - 6240, 0, 52),
    2011: (32073 - 6780, 0, 52), 2012: (34117 - 7560, 0, 52),
    2013: (27933, 0, 52), 2014: (29220, 0, 52), 2015: (30784, 0, 52),
    2016: (32564, 0, 52), 2017: (33084, 0, 52),
    2018: (30018.2, 3180.8, 52), 2019: (30992.6, 3204.8, 52),
    2020: (32993, 3308, 52), 2021: (33868, 3525, 52), 2022: (34624, 3613, 52),
    2023: (36746, 3610, 52), 2024: (39042, 3692, 53), 2025: (39987, 3667, 52),
}
# Years whose figure is estimated rather than read off a report; flagged in
# the CSV so the chart can say so in its tooltip.
ESTIMATED = {
    ("Woolworths", 1994), ("Woolworths", 1995), ("Woolworths", 1996),
    ("Coles", 1994), ("Coles", 1995), ("Coles", 1996), ("Coles", 2008),
}


def main():
    rows = []
    for fy in sorted(ABS_SUPERMARKET):
        total = ABS_SUPERMARKET[fy] + ABS_LIQUOR[fy]
        majors = 0.0
        for name, series in (("Coles", COLES), ("Woolworths", WOOLWORTHS)):
            food, liquor, weeks = series[fy]
            s52 = (food + liquor) * 52 / weeks
            majors += s52
            rows.append([fy, name, f"{food + liquor:.0f}", weeks, f"{s52:.0f}",
                         f"{total:.0f}", f"{s52 / total:.4f}",
                         "estimated" if (name, fy) in ESTIMATED else "reported"])
        rows.append([fy, "Everyone else", "", "", f"{total - majors:.0f}",
                     f"{total:.0f}", f"{(total - majors) / total:.4f}", "residual"])

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "retailer", "sales_m", "weeks", "sales_52w_m",
                    "abs_turnover_m", "share", "basis"])
        w.writerows(rows)

    print(f"WST factors: Woolworths {WST_W:.4f}, Coles {WST_C:.4f}")
    for fy in sorted(ABS_SUPERMARKET):
        s = {r[1]: float(r[6]) for r in rows if r[0] == fy}
        print(f"FY{fy}  Woolworths {s['Woolworths']:.1%}  Coles {s['Coles']:.1%}  "
              f"big two {s['Woolworths'] + s['Coles']:.1%}")


if __name__ == "__main__":
    main()
