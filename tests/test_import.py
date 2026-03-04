from src.frontend.import_parser import ImportMixin

app = type('A', (ImportMixin,), {})()

discord_text = """# Friday Night Beats VOL.3
# <t:1772596800:F> (<t:1772596800:R>)
## House // Techno // Trance
### LINEUP
<t:1772596800:t> | **DJ Alpha** (House)
<t:1772600400:t> | **DJ Beta** (Techno)
<t:1772604000:t> | **DJ Gamma** (Trance)
### OPEN DECKS
<t:1772607600:t> | Slot 1: [Available]
<t:1772609400:t> | Slot 2: [Available]
"""

r = app._parse_event_text(discord_text)
assert r is not None, "Parse returned None"
print("title:", r["title"])
print("vol:", r["vol"])
print("timestamp:", r["timestamp"])
print("genres:", r["genres"])
print("slots:", len(r["slots"]))
for s in r["slots"]:
    print(f"  {s['name']} ({s['genre']}) - {s['duration']}min")
print(f"od: {r['include_od']} count={r['od_count']} dur={r['od_duration']}")

assert r["title"] == "Friday Night Beats", f"title={r['title']}"
assert r["vol"] == "3"
assert len(r["genres"]) == 3
assert len(r["slots"]) == 3
for s in r["slots"]:
    assert s["duration"] == "60", f"dur={s['duration']}"
assert r["include_od"] is True
assert r["od_count"] == "2"
assert r["od_duration"] == "30"

print("\nALL TESTS PASSED")
