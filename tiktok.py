import argparse
import os
import re
import json
import requests

def parse_arguments():
    parser = argparse.ArgumentParser(description="Unified TikTok Text Profiler Worker")
    parser.add_argument(
        "--mode", 
        choices=["weekly", "monthly"], 
        required=True, 
        help="Execution mode: 'weekly' for an isolated 7-day wipe/rewrite, 'monthly' for cumulative incremental tracking."
    )
    return parser.parse_args()

def load_existing_data(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for video in data:
                video["tags"] = set(video.get("tags", []))
            return {video["video_id"]: video for video in data}
    except (json.JSONDecodeError, FileNotFoundError):
        print("⚠️ Existing JSON file was empty or corrupted. Starting fresh tracking frame.")
        return {}

def extract_indicators(combined_text, viral_markers, menu_markers):
    found_viral = [m for m in viral_markers if m in combined_text]
    found_menu = [m for m in menu_markers if m in combined_text]
    return found_viral, found_menu

def extract_shops(title):
    shop_matches = re.findall(r'@(\w+)|📍\s*([\w\s&]+)', title)
    return [match[0] if match[0] else match[1].strip() for match in shop_matches]

def get_tiktok_trends(mode):
    api_key = os.environ.get("TIKTOK_SCRAPER_API_KEY")
    if not api_key:
        raise ValueError("Missing TIKTOK_SCRAPER_API_KEY secret.")

    url = os.environ.get("TIKTOK_SCRAPER_API_URL")
    api_host = os.environ.get("TIKTOK_SCRAPER_API_HOST")
    if not url or not api_host:
        raise ValueError("Missing TIKTOK_SCRAPER_API_URL or TIKTOK_SCRAPER_API_HOST secrets.")
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
        "Content-Type": "application/json"
    }

    queries = {
        "matcha": "soho london matcha",
        "bubble_tea": "soho london bubble tea",
        "coffee": "soho coffee shops",
        "bakery": "soho bakeries london"
    }

    if mode == "weekly":
        publish_time = "7"
        file_path = "public/tiktok_week.json"
        queries.update({
            "specials": "soho london cafe new menu",
            "bakery_specials": "london bakery limited drop soho",
            "matcha_specials": "soho matcha special menu",
            "coffee_specials": "soho london coffee new menu specials",
            "bubble_tea_specials": "soho london bubble tea boba specials menu",
            "new_openings": "soho london new cafe opening"
        })
        print(f"🚀 Running WEEKLY extraction mode (Time window: 7 days). Targeted destination: '{file_path}' (Wipe & Rewrite strategy).")
    else:
        publish_time = "0"
        file_path = "public/tiktok_spots.json"
        print(f"📚 Running monthly aggregation mode (Time window: All Time). Targeted destination: '{file_path}' (Incremental merge strategy).")
    
    viral_markers = ["viral", "hype", "trend", "hidden gem", "must try", "secret spot", "best coffee", "famous"]
    menu_markers = ["new item", "limited drop", "special menu", "seasonal", "ube", "matcha", "boba", "pastry", "menu update"]

    all_videos = load_existing_data(file_path) if mode == "monthly" else {}
    if all_videos:
        print(f"📦 Loaded {len(all_videos)} existing videos from monthly history map.")

    for tag, query in queries.items():
        payload = {
            "keywords": query,
            "region": "GB",
            "count": "30",
            "cursor": "0",
            "publish_time": publish_time,
            "sort_type": "0"
        }

        try:
            response = requests.get(url, params=payload, headers=headers)
            if response.status_code != 200:
                print(f"❌ HTTP Mismatch for '{query}' | Status: {response.status_code}")
                response.raise_for_status()

            data = response.json()
            if data.get("msg") != "success":
                print(f"❌ API Error for '{query}': {data.get('msg')}")
                continue

            for video in data.get("data", {}).get("videos", []):
                v_id = video["video_id"]
                title = video.get("title", "")
                
                caption_text = title.lower()
                desc_text = " ".join(video.get("content_desc", [])).lower()
                hashtag_text = " ".join([c.get("title", "") for c in video.get("challenges", [])]).lower()
                combined_text = f"{caption_text} {desc_text} {hashtag_text}"
                
                found_viral, found_menu = extract_indicators(combined_text, viral_markers, menu_markers)
                detected_shops = extract_shops(title)
                
                if v_id not in all_videos:
                    all_videos[v_id] = {
                        "video_id": v_id,
                        "raw_caption": title,
                        "author_username": video.get("author", {}).get("unique_id", ""),
                        "author_nickname": video.get("author", {}).get("nickname", ""),
                        "detected_shops": list(set(detected_shops)),
                        "viral_indicators": list(set(found_viral)),
                        "menu_indicators": list(set(found_menu)),
                        "metrics": {
                            "play_count": video.get("play_count", 0),
                            "digg_count": video.get("digg_count", 0),
                            "collect_count": video.get("collect_count", 0),
                            "share_count": video.get("share_count", 0)
                        },
                        "tags": {tag}
                    }
                else:
                    record = all_videos[v_id]
                    record["tags"].add(tag)
                    record["metrics"] = {
                        "play_count": video.get("play_count", 0),
                        "digg_count": video.get("digg_count", 0),
                        "collect_count": video.get("collect_count", 0),
                        "share_count": video.get("share_count", 0)
                    }
                    record["viral_indicators"] = list(set(record["viral_indicators"] + found_viral))
                    record["menu_indicators"] = list(set(record["menu_indicators"] + found_menu))
                    record["detected_shops"] = list(set(record["detected_shops"] + detected_shops))
                        
        except requests.exceptions.HTTPError as err:
            print(f"Skipping parameter set loop for '{query}': {err}")
            continue

    for video in all_videos.values():
        video["tags"] = list(video["tags"])

    unique_records = list(all_videos.values())
    print(f"✅ Success! Flattened text profile dataset contains {len(unique_records)} parsed items.")

    os.makedirs("public", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(unique_records, f, indent=2)

if __name__ == "__main__":
    args = parse_arguments()
    get_tiktok_trends(args.mode)