import requests
from bs4 import BeautifulSoup
import html
import json
import time
import urllib3

# 關閉 SSL 憑證警告 (有些台灣的網站憑證設定不完整)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_all_routes():
    """獲取所有客運路線的 ID 與名稱"""
    base_url = "https://www.edabus.com.tw/route"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    response = requests.get(base_url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    routes = []
    menu = soup.select_one(".desktop-left-menu")
    if menu:
        for li in menu.select("li a"):
            href = li.get("href")
            name = li.get_text(strip=True)
            if href:
                route_id = href.split("/")[-1]
                routes.append({
                    "id": route_id,
                    "name": name,
                    "timetable_url": f"https://www.edabus.com.tw/route/page/{route_id}/timetable"
                })
    return routes

def get_isu_schedules(timetable_url, route_name):
    """取得單一路線中，有停靠義守大學的班次"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(timetable_url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    results = []
    timetables = soup.select(".timetables")
    type_map = {
        "1": "平日",
        "2": "假日",
        "3": "寒暑假平日",
        "4": "寒暑假假日",
        "7": "颱風(豪雨)"
    }
    
    for tt in timetables:
        tt_id = tt.get("data-timetable-type-id")
        tt_type = type_map.get(tt_id, f"類型-{tt_id}")
        
        directions = [
            ("outbound-journey-schedules", "去程"), 
            ("return-journey-schedules", "回程")
        ]
        
        for direction_class, direction_label in directions:
            schedules_div = tt.select_one(f".{direction_class}")
            if not schedules_div:
                continue
                
            direction_name_elem = schedules_div.select_one(".travel-direction-btn.active")
            direction_name = direction_name_elem.get_text(strip=True) if direction_name_elem else direction_label
            
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
                    stops_at_isu = False
                    isu_time = ""
                    all_stops = []
                    
                    if collapse_div:
                        arrival_times = collapse_div.select(".arrival-time")
                        for arrival in arrival_times:
                            station_span = arrival.select_one(".station")
                            time_span = arrival.select_one(".time")
                            if station_span and time_span:
                                station_name = html.unescape(station_span.get_text(strip=True))
                                stop_time = html.unescape(time_span.get_text(strip=True))
                                all_stops.append({"station": station_name, "time": stop_time})
                                if "義守大學" in station_name:
                                    stops_at_isu = True
                                    isu_time = stop_time
                                    
                    if stops_at_isu:
                        results.append({
                            "route_name": route_name,
                            "day_type": tt_type,
                            "direction": direction_name,
                            "start_time": start_time,
                            "isu_time": isu_time,
                            "end_time": end_time,
                            "stops": all_stops
                        })
    return results

def main():
    print("開始抓取義大客運所有路線...")
    routes = get_all_routes()
    print(f"共找到 {len(routes)} 條路線。")
    
    all_isu_buses = []
    
    for route in routes:
        print(f"正在分析路線: {route['name']} ...")
        try:
            isu_buses = get_isu_schedules(route["timetable_url"], route["name"])
            all_isu_buses.extend(isu_buses)
        except Exception as e:
            print(f"抓取 {route['name']} 時發生錯誤: {e}")
        time.sleep(1)
        
    with open("all_isu_buses.json", "w", encoding="utf-8") as f:
        json.dump(all_isu_buses, f, ensure_ascii=False, indent=2)
        
    with open("all_isu_buses.js", "w", encoding="utf-8") as f:
        f.write("const rawData = " + json.dumps(all_isu_buses, ensure_ascii=False, indent=2) + ";\n")
        
    print(f"\n抓取完成！共找到 {len(all_isu_buses)} 個會進入義守大學的班次。")
    print("結果已儲存至 all_isu_buses.json")

if __name__ == "__main__":
    main()
