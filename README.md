# ערכת ניתוח השקעות נדל"ן — ישראל 2026

ניתוח רכישה והשקעה בדירות: מס רכישה, מימון ומשכנתא, תשואות, לוח סילוקין,
תחזית מכירה עם מס שבח, ומנוע למשיכת נתוני עסקאות שנמכרו מהמאגר הממשלתי.

## התקנה

```bash
pip install -r requirements.txt
```

## שימוש

```bash
# בדיקות
python -m pytest

# משיכת נתוני שוק לפי אזור (פלט ל-Excel + CSV)
python scripts/market.py "רמת גן"
python scripts/market.py "פלורנטין תל אביב" --pages 5 --out data/

# מחשבון אינטראקטיבי
open web/index.html        # פתח בדפדפן
```

### שימוש בחבילה מקוד

```python
from realestate import DealInputs, analyze_deal, project_sale

deal = DealInputs(price=2_000_000, buyer_type="single",
                  ltv_wanted=0.75, interest_rate=0.048, monthly_rent=6000)
r = analyze_deal(deal)
print(r.monthly_payment, r.equity_required, r.gross_yield)

sale = project_sale(deal, hold_years=10)
print(sale.annualized_return)
```

## עבודה עם Claude Code

הפרויקט מוכן לעבודה מקצועית עם Claude Code. קובץ `CLAUDE.md` מכיל את כל ההקשר
התחומי והאילוצים ונטען אוטומטית.

### התקנת Claude Code (Mac)

דרוש חשבון Anthropic בתשלום (Pro / Max / Team / Enterprise / Console).
שתי דרכים — ההתקנה הנייטיבית היא המומלצת והנתמכת הראשית:

```bash
# מומלץ — מתקין נייטיבי, ללא תלות ב-Node, מתעדכן אוטומטית
curl -fsSL https://claude.ai/install.sh | bash

# או דרך npm (דורש Node.js 18+, מומלץ 22 LTS). אל תשתמש ב-sudo.
npm install -g @anthropic-ai/claude-code@latest
```

אימות והפעלה:

```bash
claude --version
cd realestate-toolkit
claude
```

תיעוד רשמי: https://code.claude.com/docs/en/setup

### פרומפטים טובים להתחלה

- "קרא את CLAUDE.md ואת מבנה הפרויקט, ואז הרץ את הבדיקות."
- "חבר את פלט scripts/market.py כגיליון חדש בתוך קובץ ה-Excel הראשי."
- "הוסף חישוב נקודת איזון לחבילת finance, עם בדיקות."
- "הוסף השוואת תמהילי משכנתא (פריים/קל\"צ/צמודה)."

## מבנה

```
src/realestate/
  config.py    קבועי 2026 (מס, LTV, מע"מ) — מקור אמת יחיד
  tax.py       מס רכישה ומס שבח
  finance.py   משכנתא, ניתוח עסקה, סילוקין, תחזית מכירה
  parser.py    פירוק טקסט מודעה
  nadlan.py    מנוע נתוני שוק (אתר הנדל"ן הממשלתי)
scripts/market.py   CLI למשיכת נתונים
web/index.html      מחשבון דפדפן
tests/              בדיקות pytest
```

## הערות חוקיות

מקור נתוני העסקאות הוא **nadlan.gov.il** — מאגר ממשלתי פתוח. הכלי **אינו**
מבצע scraping של יד2/מדלן (אסור בתנאי השימוש שלהם). למודעות חיות יש להשתמש
בפיד מורשה (מעמד תיווך) או בהדבקה ידנית.

**דיסקליימר:** להמחשה בלבד. אינו ייעוץ פיננסי, מיסויי או משכנתאי.
