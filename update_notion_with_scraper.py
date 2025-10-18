# update_notion_with_scraper.py
import os, time, random, re
from dotenv import load_dotenv
from notion_client import Client
from scraper_x_metrics import get_metrics


PROP_LINK  = "x.com Link"    # URL 컬럼명
PROP_VIEWS = "Views on X"    # Number 컬럼명
PROP_LIKES = "Likes"         # Number 컬럼명


SLEEP_MIN, SLEEP_MAX = 2.5, 4.5

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DB_ID        = os.getenv("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not DB_ID:
    raise SystemExit("[ERR] .env의 NOTION_TOKEN / NOTION_DATABASE_ID가 비어있음")

notion = Client(auth=NOTION_TOKEN)

def query_db():
    start = None
    while True:
        resp = notion.databases.query(
            **({"database_id": DB_ID, "start_cursor": start} if start else {"database_id": DB_ID})
        )
        for row in resp.get("results", []):
            yield row
        if not resp.get("has_more"):
            break
        start = resp.get("next_cursor")

def get_url(page):
    try:
        return page["properties"][PROP_LINK]["url"]
    except Exception:
        return None

def get_current_numbers(page):
    v = page["properties"].get(PROP_VIEWS, {}).get("number")
    l = page["properties"].get(PROP_LIKES, {}).get("number")
    return v, l

def update_page(page_id, views=None, likes=None):
    props = {}
    if views is not None:
        props[PROP_VIEWS] = {"number": int(views)}
    if likes is not None:
        props[PROP_LIKES] = {"number": int(likes)}
    if props:
        notion.pages.update(page_id=page_id, properties=props)

def main():
    total = upd = skip = 0
    for page in query_db():
        total += 1
        url = get_url(page)
        if not url:
            skip += 1
            continue


        cur_v, cur_l = get_current_numbers(page)

        try:
            views, likes = get_metrics(url, debug=False)
            will_update = False
            new_props = {}
            if views is not None and views != cur_v:
                new_props["views"] = views
                will_update = True
            if likes is not None and likes != cur_l:
                new_props["likes"] = likes
                will_update = True

            if will_update:
                update_page(page["id"], new_props.get("views"), new_props.get("likes"))
                upd += 1
                print(f"[OK] {url} -> V:{new_props.get('views', cur_v)}  L:{new_props.get('likes', cur_l)}")
            else:
                skip += 1

            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
        except Exception as e:
            print(f"[WARN] fail {url}: {e}")

    print(f"[DONE] rows={total}, updated={upd}, skipped={skip}")

if __name__ == "__main__":
    main()

