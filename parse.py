import json
from bs4 import BeautifulSoup
import html

file_path = r"C:\Users\safu\.gemini\antigravity\brain\ed56ef69-78f2-479d-8f36-3f72acbdac26\.system_generated\steps\4\content.md"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == "<!DOCTYPE html>":
            start_idx = i
            break
    html_content = "".join(lines[start_idx:])

soup = BeautifulSoup(html_content, "html.parser")
results = []

timetables = soup.select(".timetables")
type_map = {
    "1": "平日",
    "2": "假日",
    "7": "颱風(豪雨)"
}

for tt in timetables:
    tt_id = tt.get("data-timetable-type-id")
    tt_type = type_map.get(tt_id, tt_id)

    for direction_class, direction_name in [("outbound-journey-schedules", "往高雄市立美術館"), ("return-journey-schedules", "往義大世界站")]:
        schedules_div = tt.select_one(f".{direction_class}")
        if not schedules_div:
            continue
            
        schedules = schedules_div.select(".schedule")
        for schedule in schedules:
            row_data = schedule.select_one(".row-data")
            if not row_data:
                continue
                
            cols = row_data.find_all("div", recursive=False)
            if len(cols) >= 4:
                start_time = cols[2].get_text(strip=True)
                end_time = cols[3].get_text(strip=True)
                
                collapse_div = schedule.select_one(".collapse")
                stops = []
                stops_at_isu = False
                isu_time = ""
                
                if collapse_div:
                    arrival_times = collapse_div.select(".arrival-time")
                    for arrival in arrival_times:
                        station_span = arrival.select_one(".station")
                        time_span = arrival.select_one(".time")
                        if station_span and time_span:
                            station_name = html.unescape(station_span.get_text(strip=True))
                            stop_time = html.unescape(time_span.get_text(strip=True))
                            stops.append((station_name, stop_time))
                            if "義守大學" in station_name:
                                stops_at_isu = True
                                isu_time = stop_time
                                
                if stops_at_isu:
                    results.append({
                        "type": tt_type,
                        "direction": direction_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "isu_time": isu_time
                    })

with open("results2.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
