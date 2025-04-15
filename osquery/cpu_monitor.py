#!/usr/bin/env python3
import osquery
import psutil
import time

@osquery.register_plugin
class CPUUsageTable(osquery.TablePlugin):
    def name(self):
        return "cpu_usage"
    
    def columns(self):
        return [
            osquery.TableColumn(name="timestamp", type=osquery.STRING),
            osquery.TableColumn(name="cpu_percent", type=osquery.STRING),
            osquery.TableColumn(name="user", type=osquery.STRING),
            osquery.TableColumn(name="system", type=osquery.STRING),
            osquery.TableColumn(name="idle", type=osquery.STRING)
        ]
    
    def generate(self, context):
        cpu_times = psutil.cpu_times_percent(interval=0)
        cpu_percent = psutil.cpu_percent(interval=0)
        
        row = {}
        row["timestamp"] = str(int(time.time()))
        row["cpu_percent"] = str(cpu_percent)
        row["user"] = str(cpu_times.user)
        row["system"] = str(cpu_times.system)
        row["idle"] = str(cpu_times.idle)
        
        return [row]

if __name__ == "__main__":
    osquery.start_extension(name="cpu_monitor", version="1.0.0")
