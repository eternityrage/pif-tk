"""
Daily Publisher - PiffTok Lens (Michelle Pfeiffer)
"""
import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def get_repost_counts():
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({"video_name": video_name, "metadata": metadata})
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))
    if specific_video:
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video
        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"Video {name} was already published ({post_count}x) - Re-publishing")
            return vid_path, name
        else:
            print(f"Error: Specific video {name} not found")
            return None, None
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]
    if unpublished:
        vid, name = unpublished[0]
        return vid, name
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)
        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name
    return None, None

def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Michelle Pfeiffer's Most Iconic Red Carpet Moments of All Time",
        "Michelle Pfeiffer's Best Fashion Looks That Defined Hollywood",
        "Michelle Pfeiffer Interview Moments That Proved She's a Legend",
        "Michelle Pfeiffer's Most Iconic Catwoman Moments",
        "Michelle Pfeiffer on the Red Carpet - Timeless Elegance",
        "Michelle Pfeiffer's Best Talk Show Appearances Compilation",
        "Michelle Pfeiffer's Most Glamorous Met Gala Looks",
        "The Rise of Michelle Pfeiffer - From Grease to Batman",
        "Michelle Pfeiffer's Best Acting Roles Ranked",
        "Michelle Pfeiffer Behind the Scenes - Pure Class",
        "Michelle Pfeiffer's Style Evolution Through the Decades",
        "Michelle Pfeiffer and Michael Keaton - Best On-Screen Duo",
        "Michelle Pfeiffer Talks New Projects - What We Know",
        "Michelle Pfeiffer's Most Unforgettable Movie Moments",
        "Michelle Pfeiffer - The Queen of Hollywood Glamour",
    ]

    fallback_descriptions = [
        "Michelle Pfeiffer doesn't just walk red carpets - she owns them. From her iconic Catwoman suit to that head-turning couture at the Met Gala, every look is a moment. The way she carries herself, the confidence, the elegance - it's unmatched. Drop a fire emoji if you think Michelle Pfeiffer is the most elegant actress of all time! #michellepfeiffer #michellepfeifferstyle #redcarpet #fashionicon #hollywood #catwoman #grease #actress #elegance #icon #glamour",
        "Michelle Pfeiffer's portrayal of Catwoman in Batman Returns is one of the most iconic performances in cinema history. The rawness, the power, the seduction - she brought something unforgettable to every single scene. Share this if you think Michelle Pfeiffer deserves ALL the recognition! #michellepfeiffer #catwoman #batmanreturns #iconic #hollywood #actress #timburton #dc #fashionicon",
        "When Michelle Pfeiffer sang 'Cool Rider' on screen, the world fell in love. Her voice, her presence, that incredible energy - it was pure movie magic. Like if you still get chills watching her perform! #michellepfeiffer #grease2 #cooloridge #musical #hollywood #actress #icon #singing",
        "Fashion has never seen a powerhouse quite like Michelle Pfeiffer. Each red carpet appearance is a masterclass in style. Comment which Michelle Pfeiffer look is your favorite! #michellepfeiffer #fashionicon #style #redcarpet #metgala #highfashion #celebritystyle #couture #michellepfeifferstyle #fashiongoals #iconic",
        "Michelle Pfeiffer's journey from small-town girl to Hollywood royalty is nothing short of inspirational. Her story proves that with talent, hard work, and authenticity, you can achieve anything. Share this if Michelle Pfeiffer inspires you! #michellepfeiffer #inspiration #hollywood #successstory #actress #rolemodel #motivation #michellepfeifferfan #journey",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "exciting and celebratory - hype up Michelle Pfeiffer's talent, style, and iconic moments",
        "fun and engaging - make it feel like you're talking about your favorite celebrity with a friend",
        "inspiring and uplifting - highlight how Michelle Pfeiffer's journey motivates her fans",
        "glamorous and stylish - focus on her incredible fashion and red carpet looks",
        "emotional and heartfelt - showcase her powerful acting and the moments that move us",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"about Michelle Pfeiffer for the Facebook page 'PiffTok Lens'. "
        f"The page posts the best Michelle Pfeiffer moments - red carpet looks, interviews, acting scenes, "
        f"fashion, behind-the-scenes, and everything that makes Michelle Pfeiffer a Hollywood icon. "
        f"Speak as a passionate Michelle Pfeiffer fan who loves celebrating her talent and style. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and fun. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Michelle Pfeiffer! "
        f"- Comment your favorite Michelle Pfeiffer movie or role! "
        f"- Share this with another Michelle Pfeiffer fan! "
        f"- Follow PiffTok Lens for the best Michelle Pfeiffer content! "
        f"Include relevant hashtags in ALL LOWERCASE such as #michellepfeiffer #hollywood #catwoman #grease #fashion #celebrity #redcarpet #michellepfeifferfan #actress #elegance #icon #glamour #batmanreturns. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.9, "seed": random.randint(1, 999999)}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("DAILY AUTOMATION STARTING - PIFFTOK LENS")
    print("=" * 60)
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("No new videos found to publish. Exiting.")
        return
    print(f"Selected Video: {video_name}")
    print("Generating caption via Pollination AI...")
    title, description = generate_caption()
    print(f"Title: {title}")
    print(f"Description:\n{description}")
    combined_caption = f"{title}\n\n{description}"
    success_flags = {"instagram_reel": False, "instagram_story": False, "facebook_reel": False, "facebook_story": False, "threads": False, "youtube": False}
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"Instagram Reel upload failed: {e}")
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"Instagram Story upload failed: {e}")
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"Facebook Reel upload failed: {e}")
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"Facebook Story upload failed: {e}")
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"Threads upload failed: {e}")
    try:
        upload_to_youtube(video_path, title, description, tags=["michellepfeiffer", "hollywood", "catwoman", "grease", "fashion", "celebrity", "redcarpet", "michellepfeifferfan", "actress", "elegance", "icon", "glamour", "batmanreturns", "pifftoklens"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"YouTube upload failed: {e}")
    print("\nMarking video as published.")
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    if is_recycled:
        print(f"   This is a recycled video (re-publishing)")
    mark_as_published(video_name, {"title": title, "description": description, "success_flags": success_flags, "recycled": is_recycled})
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"Moved published video to {dest_path}")
    except Exception as e:
        print(f"Failed to move published video: {e}")
    print("DAILY AUTOMATION COMPLETE - PIFFTOK LENS")

if __name__ == "__main__":
    main()
